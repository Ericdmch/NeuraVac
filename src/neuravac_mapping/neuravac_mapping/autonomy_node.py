"""Experimental exploration coordinator; disabled unless explicitly enabled.

It delegates movement to Nav2 and the serial owner's watchdog. The operator
interface exchanges JSON over autonomy/request and autonomy/state. Do not use
on a physical robot until the driver patch, Nav2 configuration and acceptance
checks have been completed.
"""
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from std_msgs.msg import String
from std_srvs.srv import Trigger

from .exploration import ExplorationPlanner
from .grid_geometry import GridGeometry
from .mission_supervisor import MissionSupervisor


class AutonomyNode(Node):
    def __init__(self):
        super().__init__('autonomous_mapping')
        self.declare_parameter('enable_motion', False)
        self.declare_parameter('clearance_m', .10)
        self.declare_parameter('goal_timeout_s', 120.)
        self.declare_parameter('behavior_tree', '')
        self.declare_parameter('click_to_move_speed_multiplier', 1.0)
        self.declare_parameter('max_autonomous_linear_vel_m_s', .35)
        self.declare_parameter('max_autonomous_angular_vel_rad_s', 1.5)
        self.declare_parameter('max_goto_retries', 5)
        self.mission = MissionSupervisor()
        self.goto_only_active = False
        self.goto_retries = 0
        self.mapping = self.position = self.mapping_at = self.position_at = None
        self.nav_velocity = self.nav_velocity_at = None
        self.driver_status = self.driver_status_at = None
        self.generation = 0
        self.goal_handle = None
        self.goal_started = None
        self.rejected = set()
        self.current_goal = None
        self.failures = 0
        self.armed = False
        self.arm_started = None
        self.plan_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='frontier')
        self.plan_future = None
        self.plan_generation = None
        self.plan_started = None
        self.plan_kind = None
        durable = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(OccupancyGrid, 'slam/map', self.on_map, durable)
        self.create_subscription(PoseStamped, 'slam/pose', self.on_pose, 10)
        self.create_subscription(String, 'autonomy/driver_status', self.on_driver, 10)
        self.create_subscription(String, 'autonomy/request', self.on_request, 10)
        self.create_subscription(Twist, 'autonomy/nav_cmd_vel', self.on_velocity, 10)
        self.state_pub = self.create_publisher(String, 'autonomy/state', 10)
        self.drive_pub = self.create_publisher(Twist, 'autonomy/cmd_vel', 10)
        self.arm_client = self.create_client(Trigger, 'autonomy/arm')
        self.disarm_client = self.create_client(Trigger, 'autonomy/disarm')
        self.navigator = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.create_timer(.1, self.tick)

    def fresh_header(self, header, max_age):
        now = self.get_clock().now().nanoseconds * 1e-9
        stamp = header.stamp.sec + header.stamp.nanosec * 1e-9
        return 0 <= now - stamp <= max_age

    def on_map(self, msg):
        info = msg.info
        q = info.origin.orientation
        if (msg.header.frame_id != 'map' or not self.fresh_header(msg.header, 3.) or
                len(msg.data) != info.width * info.height or
                not all(math.isfinite(v) for v in (q.x, q.y, q.z, q.w)) or
                abs(sum(v*v for v in (q.x, q.y, q.z, q.w)) - 1.) > .05):
            return
        yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
        try:
            geometry = GridGeometry(info.width, info.height, info.resolution,
                                    info.origin.position.x, info.origin.position.y, yaw)
        except ValueError:
            return
        rows = [list(msg.data[y*info.width:(y+1)*info.width]) for y in range(info.height)]
        self.mapping, self.mapping_at = (geometry, rows), time.monotonic()

    def on_pose(self, msg):
        if (msg.header.frame_id == 'map' and self.fresh_header(msg.header, .5) and
                all(math.isfinite(v) for v in (msg.pose.position.x, msg.pose.position.y))):
            self.position = (msg.pose.position.x, msg.pose.position.y)
            self.position_at = time.monotonic()

    def on_driver(self, msg):
        self.driver_status, self.driver_status_at = msg.data, time.monotonic()

    def on_velocity(self, msg):
        self.nav_velocity, self.nav_velocity_at = msg, time.monotonic()

    def planner(self):
        now = time.monotonic()
        if (self.mapping is None or self.position is None or self.mapping_at is None or
                self.position_at is None or now - self.mapping_at > 3. or now - self.position_at > .5):
            raise ValueError('Map or robot pose unavailable or stale')
        geometry, rows = self.mapping
        clearance = float(self.get_parameter('clearance_m').value)
        if not math.isfinite(clearance) or clearance <= 0:
            raise ValueError('Invalid robot clearance')
        return ExplorationPlanner(geometry, rows, math.ceil(clearance / geometry.resolution), self.rejected)

    def on_request(self, message):
        try:
            request = json.loads(message.data)
            if not isinstance(request, dict):
                raise ValueError('Invalid request')
            command = request.get('command')
            if command == 'start':
                self.start(request.get('return_goal'))
            elif command == 'goto':
                self.start(request.get('return_goal'), goto_only=True)
            elif command == 'return':
                if self.mission.state == 'exploring':
                    if not self.armed:
                        self.halt('Mapping has not started; waiting for operator')
                    else:
                        self.cancel_goal()
                        self.mission.request_return()
                        self.send_return()
            elif command == 'stop':
                self.halt('operator stop')
            else:
                raise ValueError('Unknown command')
        except (ValueError, TypeError, OverflowError, json.JSONDecodeError) as error:
            self.mission.reason = str(error)
        self.publish_state()

    def _goto_reachable(self, planner, position, target):
        goal = planner.geometry.world_cell(*target)
        if goal is None:
            return False
        gx, gy = goal
        r = max(1, planner.clearance - 1)
        def cell_clear(cx, cy):
            if not (0 <= cx < planner.geometry.width and 0 <= cy < planner.geometry.height):
                return False
            if planner.rows[cy][cx] >= 75:
                return False
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy > r * r:
                        continue
                    xx, yy = cx + dx, cy + dy
                    if 0 <= xx < planner.geometry.width and 0 <= yy < planner.geometry.height:
                        if planner.rows[yy][xx] >= 75:
                            return False
            return True
        if cell_clear(gx, gy):
            return True
        # Snap clicked point to the nearest cell outside the wall buffer within 1.0 m (20 cells)
        best = None
        best_d2 = 1e9
        for rad in range(1, 21):
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    d2 = dx * dx + dy * dy
                    if d2 >= best_d2:
                        continue
                    if cell_clear(gx + dx, gy + dy):
                        best = (gx + dx, gy + dy)
                        best_d2 = d2
            if best is not None:
                break
        if best is not None:
            wx, wy = planner.geometry.cell_world(*best)
            self.mission.return_goal = (round(wx, 3), round(wy, 3))
            return True
        return False

    def _find_escape_point(self, planner, position, min_rad=2, max_rad=25):
        if not hasattr(planner, 'geometry') or not hasattr(planner, 'rows'):
            return None
        start = planner.geometry.world_cell(*position)
        if start is None:
            return None
        sx, sy = start
        r = max(1, planner.clearance)
        def is_safe_open(cx, cy, clearance_r):
            if not (0 <= cx < planner.geometry.width and 0 <= cy < planner.geometry.height):
                return False
            if not (0 <= planner.rows[cy][cx] <= 20):
                return False
            for dy in range(-clearance_r, clearance_r + 1):
                for dx in range(-clearance_r, clearance_r + 1):
                    if dx * dx + dy * dy > clearance_r * clearance_r:
                        continue
                    xx, yy = cx + dx, cy + dy
                    if not (0 <= xx < planner.geometry.width and 0 <= yy < planner.geometry.height):
                        return False
                    if planner.rows[yy][xx] < 0 or planner.rows[yy][xx] > 20:
                        return False
            return True
        for clearance_r in (r, 1, 0):
            best = None
            best_d2 = 1e9
            for rad in range(min_rad, max_rad + 1):
                for dy in range(-rad, rad + 1):
                    for dx in range(-rad, rad + 1):
                        d2 = dx * dx + dy * dy
                        if d2 >= best_d2:
                            continue
                        if is_safe_open(sx + dx, sy + dy, clearance_r):
                            best = (sx + dx, sy + dy)
                            best_d2 = d2
                if best is not None:
                    wx, wy = planner.geometry.cell_center(*best)
                    return (round(wx, 3), round(wy, 3))
        return None

    def _persistent_preflight(self, planner, position, target):
        try:
            if planner.return_reachable(position, target):
                return True
        except Exception:
            pass
        if hasattr(planner, 'geometry') and hasattr(planner, 'rows'):
            return self._goto_reachable(planner, position, target)
        return False

    def _explore_next_with_escape(self, planner, position):
        try:
            goal = planner.next_goal(position)
            if goal is not None or not hasattr(planner, 'geometry'):
                return goal
        except ValueError:
            if not hasattr(planner, 'geometry'):
                raise
        # Robot is inside the red buffer zone or tight space; find nearest clear cell outside buffer
        escape_pt = self._find_escape_point(planner, position, min_rad=1, max_rad=25)
        search_origins = [p for p in (escape_pt, position) if p is not None]
        for c_try in (planner.clearance, 1, 0):
            for origin in search_origins:
                try:
                    relaxed = ExplorationPlanner(planner.geometry, planner.rows, c_try, self.rejected)
                    goal = relaxed.next_goal(origin, min_distance_m=.15)
                    if goal is not None:
                        return goal
                except ValueError:
                    continue
        if escape_pt is not None and escape_pt not in self.rejected:
            dist = math.hypot(escape_pt[0] - position[0], escape_pt[1] - position[1])
            if dist >= 0.08:
                return escape_pt
        return None

    def start(self, target, goto_only=False):
        if not self.get_parameter('enable_motion').value:
            raise ValueError('Autonomous motion is disabled')
        if goto_only and (self.mission.state in ('exploring', 'returning') or self.armed):
            self.halt('redirecting to new point')
            self.mission = MissionSupervisor()
        if self.mission.state in ('exploring', 'returning') or self.armed:
            raise ValueError('Mission already active')
        if not self.arm_client.service_is_ready() or not self.disarm_client.service_is_ready():
            raise ValueError('Driver watchdog unavailable')
        if not self.navigator.server_is_ready():
            raise ValueError('Navigation server unavailable')
        if not self.get_parameter('behavior_tree').value:
            raise ValueError('Safe navigation behavior tree unavailable')
        if not isinstance(target, (list, tuple)) or len(target) != 2:
            raise ValueError('Select a return point')
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in target):
            raise ValueError('Invalid return point')
        planner = self.planner()
        self.mission.start(target, True)
        self.goto_only_active = bool(goto_only)
        self.goto_retries = 0
        if goto_only:
            self.mission.request_return()
        self.rejected.clear()
        self.failures = 0
        self.generation += 1
        check_fn = (
            (lambda: self._goto_reachable(planner, self.position, tuple(target)))
            if goto_only
            else (lambda: self._persistent_preflight(planner, self.position, tuple(target)))
        )
        self.plan_future = self.plan_executor.submit(check_fn)
        self.plan_generation = self.generation
        self.plan_started = time.monotonic()
        self.plan_kind = 'preflight'

    def on_arm(self, future, generation):
        try:
            result = future.result()
        except Exception:
            if generation == self.generation:
                self.halt('Driver watchdog did not respond')
            return
        if generation != self.generation:
            if result.success and self.disarm_client.service_is_ready():
                self.disarm_client.call_async(Trigger.Request())
            return
        self.arm_started = None
        if not result.success:
            self.halt('Driver watchdog refused: ' + result.message)
            return
        self.armed = True
        self.driver_status_at = time.monotonic()
        self.driver_status = 'ARMED'
        self.drive_pub.publish(Twist())
        if self.mission.state == 'returning':
            self.send_goal(self.mission.return_goal)
        else:
            self.plan_next()

    def plan_next(self):
        try:
            planner, position = self.planner(), self.position
            self.plan_future = self.plan_executor.submit(self._explore_next_with_escape, planner, position)
            self.plan_generation = self.generation
            self.plan_started = time.monotonic()
            self.plan_kind = 'explore'
        except ValueError as error:
            self.halt(str(error))

    def send_return(self):
        try:
            planner, position, target = self.planner(), self.position, self.mission.return_goal
            self.plan_future = self.plan_executor.submit(self._persistent_preflight, planner, position, target)
            self.plan_generation = self.generation
            self.plan_started = time.monotonic()
            self.plan_kind = 'return'
        except ValueError as error:
            self.halt(str(error))

    def poll_plan(self):
        if self.plan_future is None:
            return
        if time.monotonic() - self.plan_started > 10.:
            self.halt('Route planning timed out; waiting for operator')
            return
        if not self.plan_future.done():
            return
        future, kind, generation = self.plan_future, self.plan_kind, self.plan_generation
        self.plan_future = self.plan_started = self.plan_kind = self.plan_generation = None
        if generation != self.generation or (kind != 'preflight' and not self.armed):
            return
        try:
            result = future.result()
        except Exception:
            self.halt('Route planning failed; waiting for operator')
            return
        if kind == 'preflight':
            if not result:
                self.halt('Return point is not reachable in known free space')
                return
            try:
                self.arm_started = time.monotonic()
                future = self.arm_client.call_async(Trigger.Request())
                future.add_done_callback(lambda done: self.on_arm(done, generation))
            except Exception:
                self.halt('Driver watchdog unavailable')
        elif kind == 'return':
            if result:
                self.send_goal(self.mission.return_goal)
            else:
                self.halt('Return spot unreachable; waiting for operator')
        elif result is None:
            self.mission.exploration_finished()
            self.send_return()
        else:
            self.send_goal(result)

    def send_goal(self, target):
        if not self.armed or not self.navigator.server_is_ready():
            self.halt('Navigation server unavailable')
            return
        self.generation += 1
        generation = self.generation
        self.current_goal = tuple(target)
        self.goal_started = time.monotonic()
        self.nav_velocity = self.nav_velocity_at = None
        goal = NavigateToPose.Goal()
        goal.behavior_tree = str(self.get_parameter('behavior_tree').value)
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x, goal.pose.pose.position.y = target
        goal.pose.pose.orientation.w = 1.
        future = self.navigator.send_goal_async(goal)
        future.add_done_callback(lambda done: self.goal_response(done, generation))

    def goal_response(self, future, generation):
        try:
            handle = future.result()
        except Exception:
            if generation == self.generation:
                self.halt('Navigation goal request failed')
            return
        if generation != self.generation:
            if handle.accepted:
                handle.cancel_goal_async()
            return
        if not handle.accepted:
            self.navigation_result(False)
            return
        self.goal_handle = handle
        handle.get_result_async().add_done_callback(lambda done: self.goal_result(done, generation))

    def goal_result(self, future, generation):
        if generation != self.generation:
            return
        self.goal_handle = None
        try:
            succeeded = future.result().status == GoalStatus.STATUS_SUCCEEDED
        except Exception:
            succeeded = False
        self.navigation_result(succeeded)

    def navigation_result(self, succeeded):
        self.drive_pub.publish(Twist())
        self.nav_velocity = self.nav_velocity_at = None
        self.goal_started = None
        if self.mission.state == 'returning':
            max_retries = int(self.get_parameter('max_goto_retries').value)
            if not succeeded and self.goto_only_active and self.armed and self.goto_retries < max_retries:
                self.goto_retries += 1
                self.mission.reason = f'Retrying path to target ({self.goto_retries}/{max_retries})…'
                self.send_goal(self.mission.return_goal)
                return
            self.mission.return_finished(succeeded)
            self.halt(self.mission.reason, preserve_state=True)
        elif self.mission.state == 'exploring':
            if not succeeded:
                self.rejected.add(self.current_goal)
                self.failures += 1
                if self.failures >= 8:
                    self.halt('Navigation failed repeatedly; waiting for operator')
                    return
            else:
                self.failures = 0
            self.plan_next()

    def cancel_goal(self):
        self.generation += 1
        if self.plan_future is not None:
            self.plan_future.cancel()
            self.plan_future = self.plan_started = self.plan_kind = self.plan_generation = None
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
            self.goal_handle = None
        self.goal_started = None
        self.nav_velocity = self.nav_velocity_at = None
        if self.armed:
            self.drive_pub.publish(Twist())

    def halt(self, reason, preserve_state=False):
        self.cancel_goal()
        if self.disarm_client.service_is_ready():
            self.disarm_client.call_async(Trigger.Request())
        self.armed = False
        self.arm_started = None
        if not preserve_state:
            if self.mission.state in ('exploring', 'returning'):
                self.mission.hazard(reason)
            else:
                self.mission.reason = reason
        self.publish_state()

    def tick(self):
        now = time.monotonic()
        if self.arm_started is not None and now - self.arm_started > 2.:
            self.halt('Driver watchdog did not respond; waiting for operator')
        if not self.armed and self.plan_kind == 'preflight':
            self.poll_plan()
        if self.armed:
            if (self.driver_status != 'ARMED' or self.driver_status_at is None or
                    now - self.driver_status_at > .6):
                reason = self.driver_status if self.driver_status and self.driver_status != 'ARMED' else 'unavailable or stale'
                self.halt('Driver watchdog stopped: ' + reason + '; waiting for operator')
            elif self.goal_started is not None and now - self.goal_started > float(self.get_parameter('goal_timeout_s').value):
                self.halt('Navigation timed out; waiting for operator')
            else:
                if self.nav_velocity_at is not None and now - self.nav_velocity_at <= .25:
                    mult = float(self.get_parameter('click_to_move_speed_multiplier').value) if self.goto_only_active else 1.0
                    if not math.isfinite(mult) or mult <= 0:
                        mult = 1.0
                    max_lin = max(.05, float(self.get_parameter('max_autonomous_linear_vel_m_s').value))
                    max_ang = max(.1, float(self.get_parameter('max_autonomous_angular_vel_rad_s').value))
                    if mult == 1.0:
                        command = self.nav_velocity
                    else:
                        command = Twist()
                        command.linear.x = max(-max_lin, min(max_lin, self.nav_velocity.linear.x * mult))
                        command.angular.z = max(-max_ang, min(max_ang, self.nav_velocity.angular.z * mult))
                else:
                    command = Twist()
                self.drive_pub.publish(command)
                self.poll_plan()
        self.publish_state()

    def publish_state(self):
        self.state_pub.publish(String(data=json.dumps({'state': self.mission.state,
            'reason': self.mission.reason, 'return_goal': self.mission.return_goal,
            'current_goal': self.current_goal, 'armed': self.armed,
            'motion_enabled': bool(self.get_parameter('enable_motion').value)})))


def main():
    rclpy.init()
    node = AutonomyNode()
    try:
        rclpy.spin(node)
    finally:
        if rclpy.ok():
            node.halt('coordinator shutdown')
        node.plan_executor.shutdown(wait=False, cancel_futures=True)
        node.destroy_node()
        rclpy.try_shutdown()

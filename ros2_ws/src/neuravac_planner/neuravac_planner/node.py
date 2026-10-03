"""Explicit-start mission state machine; Nav2 owns all geometric routing."""

import math
import uuid

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from neuravac_base.contracts import decode, restore_world
from neuravac_base.util import ConfigNode, spin
from rclpy.action import ActionClient
from rclpy.time import Time
from std_msgs.msg import String
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformListener

from neuravac_core.models import Decision, Pose


class PlannerNode(ConfigNode):
    def __init__(self):
        super().__init__("mission_planner")
        self.state = "SELF_TEST"
        self.world = None
        self.world_stamp = 0.0
        self.observed_at = 0.0
        self.available = False
        self.safety = False
        self.safety_stamp = 0.0
        self.base = False
        self.battery = 100.0
        self.goal = None
        self.target = None
        self.goal_future = None
        self.result_future = None
        self.cloud_request = None
        self.clean_request = None
        self.pass_number = 1
        self.failed = set()
        self.reason = "Waiting for healthy sensors and Nav2"
        self.hazard_signature = None
        self.planned_hazards = None
        self.completed = set()
        self.home = None
        self.mission_id = str(uuid.uuid4())
        self.cloud_enabled = self.declare_parameter("cloud_enabled", False).value
        self.cloud_timeout = self.declare_parameter("cloud_timeout_s", 12.0).value
        self.nav = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self)
        self.state_pub = self.create_publisher(String, "/mission_state", 10)
        self.heartbeat = self.create_publisher(String, "/mission/heartbeat", 10)
        self.cloud_pub = self.create_publisher(String, "/cloud/request", 10)
        self.clean_pub = self.create_publisher(String, "/cleaning/request", 10)
        self.cancel_pub = self.create_publisher(String, "/cleaning/cancel", 10)
        self.create_subscription(String, "/world_model", self.observation, 10)
        self.create_subscription(String, "/safety/status", self.safety_cb, 10)
        self.create_subscription(String, "/cloud/result", self.cloud_result, 10)
        self.create_subscription(String, "/cleaning/result", self.clean_result, 10)
        self.create_service(Trigger, "/mission/start", self.start)
        self.create_service(Trigger, "/mission/pause", self.pause)
        self.create_service(Trigger, "/mission/resume", self.resume)
        self.create_service(Trigger, "/mission/return_home", self.home_service)
        self.create_timer(0.1, self.tick)

    def healthy(self):
        now = self.seconds()
        return bool(
            self.world
            and self.available
            and self.base
            and self.safety
            and 0 <= now - self.observed_at <= self.config.safety.camera_timeout_s
            and 0 <= now - self.world_stamp <= self.config.safety.watchdog_s
            and 0 <= now - self.safety_stamp <= self.config.safety.watchdog_s
            and self.nav.server_is_ready()
        )

    def observation(self, msg):
        try:
            data = decode(
                msg.data, "world_model", self.seconds(), self.config.safety.camera_timeout_s
            )
            p = data["payload"]
            self.world = restore_world(p["world"], self.config)
            self.world_stamp = data["stamp"]
            self.observed_at = p["observed_at"]
            self.available = p["available"] is True
            self.base = p["base"].get("connected") is True
            self.battery = p["base"].get("battery", {}).get("percent", 0)
            self.hazard_signature = tuple(
                sorted(
                    (h.id, tuple(h.position), tuple(map(tuple, h.polygon)))
                    for h in self.world.hazards
                )
            )
            for region in self.world.regions.values():
                if region.id in self.failed:
                    region.reachable = False
                if (
                    region.id in self.completed
                    and region.debris_score <= self.config.cleaning.success_threshold
                ):
                    region.cleaned = True
        except (ValueError, KeyError, TypeError):
            self.available = False

    def safety_cb(self, msg):
        try:
            data = decode(msg.data, "safety", self.seconds(), self.config.safety.watchdog_s)
            self.safety = data["payload"].get("safe") is True
            self.safety_stamp = data["stamp"]
        except ValueError:
            self.safety = False

    def stop_actions(self):
        if self.goal:
            self.goal.cancel_goal_async()
            self.goal = None
        if self.goal_future and not self.goal_future.done():
            # Accepted goals arriving after pause/replan are cancelled in goal_accepted.
            self.goal_future = None
        self.result_future = None
        self.cloud_request = None
        self.publish_json(self.cancel_pub, "cleaning_cancel", {"reason": "mission_interrupted"})
        self.clean_request = None

    def service(self, response, allowed, state, reason):
        response.success = allowed
        response.message = reason
        if allowed:
            self.state = state
            self.reason = reason
        return response

    def start(self, request, response):
        allowed = self.state in ("IDLE", "COMPLETE") and self.healthy()
        if allowed:
            self.mission_id = str(uuid.uuid4())
            self.failed.clear()
            self.completed.clear()
            self.target = None
        return self.service(
            response,
            allowed,
            "SCANNING",
            "Mission started" if allowed else "Start requires IDLE and healthy sensors/Nav2",
        )

    def pause(self, request, response):
        self.state = "PAUSED"
        self.stop_actions()
        return self.service(response, True, "PAUSED", "Mission paused")

    def resume(self, request, response):
        allowed = self.state == "PAUSED" and self.healthy()
        return self.service(
            response,
            allowed,
            "SCANNING",
            "Mission resumed" if allowed else "Resume requires healthy sensors/Nav2",
        )

    def robot_pose(self):
        tf = self.tf.lookup_transform("map", "base_link", Time())
        p = tf.transform.translation
        q = tf.transform.rotation
        return Pose(
            x=p.x,
            y=p.y,
            yaw=math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)),
        )

    def local_plan(self):
        try:
            pose = self.robot_pose()
            # Reachability failures remain excluded from deterministic selection.
            region = self.world.choose(
                pose,
                lambda p: all(
                    p != self.world.regions[r].position
                    for r in self.failed
                    if r in self.world.regions
                ),
            )
            if region:
                self.execute(
                    Decision(
                        action="clean_region",
                        target_id=region.id,
                        reason="Locally validated debris priority",
                    )
                )
            elif any(
                r.debris_score > self.config.cleaning.success_threshold and not r.cleaned
                for r in self.world.regions.values()
            ):
                self.state = "PAUSED"
                self.reason = "Unresolved or unreachable debris requires inspection"
            else:
                self.state = "COMPLETE"
                self.reason = "Fresh world observation contains no unresolved debris"
        except Exception:
            self.state = "PAUSED"
            self.reason = "Map transform or target unavailable"

    def execute(self, decision):
        decision = self.world.validate_decision(decision, self.seconds())
        if decision.action == "return_home":
            self.return_home()
            return
        if decision.action != "clean_region":
            self.state = "COMPLETE" if decision.action == "finish" else "PAUSED"
            self.reason = decision.reason
            return
        if decision.target_id in self.failed:
            raise ValueError("unreachable target")
        target = self.world.regions[decision.target_id]
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x, goal.pose.pose.position.y = target.position
        goal.pose.pose.orientation.w = 1.0
        self.target = target.id
        self.pass_number = 1
        self.planned_hazards = self.hazard_signature
        self.state = "NAVIGATING"
        self.reason = decision.reason
        self.goal_future = self.nav.send_goal_async(goal)
        self.goal_future.add_done_callback(self.goal_accepted)

    def home_service(self, request, response):
        response.success = self.healthy() and self.home is not None
        response.message = (
            "Returning to measured home"
            if response.success
            else "Healthy sensors and measured startup home required"
        )
        if response.success:
            self.return_home()
            response.success = self.state == "RETURNING_HOME"
            response.message = self.reason
        return response

    def return_home(self):
        self.stop_actions()
        if self.home is None or not self.world.safe_point((self.home.x, self.home.y)):
            self.state = "PAUSED"
            self.reason = "Measured home unavailable or unsafe; human charging assistance required"
            return
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x, goal.pose.pose.position.y = self.home.x, self.home.y
        goal.pose.pose.orientation.z = math.sin(self.home.yaw / 2)
        goal.pose.pose.orientation.w = math.cos(self.home.yaw / 2)
        self.target = None
        self.planned_hazards = self.hazard_signature
        self.state = "RETURNING_HOME"
        self.reason = "Navigating to measured startup home for charging assistance"
        self.goal_future = self.nav.send_goal_async(goal)
        self.goal_future.add_done_callback(self.goal_accepted)

    def goal_accepted(self, future):
        try:
            handle = future.result()
            if future is not self.goal_future or self.state not in ("NAVIGATING", "RETURNING_HOME"):
                if handle.accepted:
                    handle.cancel_goal_async()
                return
            self.goal_future = None
            if not handle.accepted and self.state == "RETURNING_HOME":
                self.state = "PAUSED"
                self.reason = "Home goal rejected; human charging assistance required"
                return
            if not handle.accepted:
                self.failed.add(self.target)
                self.state = "REPLANNING"
                return
            self.goal = handle
            self.result_future = handle.get_result_async()
        except Exception:
            self.state = "PAUSED"
            self.reason = "Nav2 goal failed"

    def begin_clean(self):
        self.clean_request = str(uuid.uuid4())
        self.state = "CLEANING"
        self.clean_deadline = (
            self.seconds()
            + self.config.cleaning.pass_duration_s
            + 2 * self.config.safety.camera_timeout_s
            + 5
        )
        self.publish_json(
            self.clean_pub,
            "cleaning_request",
            {
                "request_id": self.clean_request,
                "region_id": self.target,
                "pass_number": self.pass_number,
            },
        )

    def clean_result(self, msg):
        try:
            p = decode(
                msg.data, "cleaning_result", self.seconds(), self.config.safety.camera_timeout_s
            )["payload"]
            if p["request_id"] != self.clean_request or self.state not in ("CLEANING", "VERIFYING"):
                return
            self.clean_request = None
            if p["success"] is True:
                self.completed.add(self.target)
                self.state = "SCANNING"
                self.reason = "Fresh AFTER observation verified cleaning"
            elif p.get("retry") is True and self.pass_number <= self.config.cleaning.max_retries:
                self.pass_number += 1
                self.state = "RETRYING"
                self.reason = "Fresh AFTER observation requires another pass"
            else:
                self.failed.add(self.target)
                self.state = "REPLANNING"
                self.reason = p.get("reason", "verification_failed")
        except (ValueError, KeyError):
            pass

    def cloud_result(self, msg):
        try:
            p = decode(
                msg.data, "cloud_result", self.seconds(), self.config.safety.camera_timeout_s
            )["payload"]
            if (
                not self.cloud_request
                or p["request_id"] != self.cloud_request[0]
                or self.state != "PLANNING"
            ):
                return
            self.cloud_request = None
            if p["decision"]:
                self.execute(Decision.model_validate(p["decision"]))
            else:
                self.local_plan()
        except (ValueError, KeyError):
            self.cloud_request = None
            if self.state == "PLANNING":
                self.local_plan()

    def tick(self):
        self.publish_json(self.heartbeat, "heartbeat", {"state": self.state})
        if self.state == "SELF_TEST":
            if self.healthy():
                try:
                    self.home = self.robot_pose()
                    self.state = "IDLE"
                    self.reason = "Self-test passed; explicit start required"
                except Exception:
                    self.reason = "Waiting for measured map localization"

        elif self.state not in ("IDLE", "COMPLETE", "PAUSED"):
            if not self.healthy():
                self.state = "PAUSED"
                self.reason = "Sensor, world, safety or Nav2 unavailable"
                self.stop_actions()
            elif (
                self.battery <= self.config.safety.return_battery_percent
                and self.state != "RETURNING_HOME"
            ):
                self.return_home()
            elif (
                self.state in ("NAVIGATING", "CLEANING", "VERIFYING", "RETURNING_HOME")
                and self.hazard_signature != self.planned_hazards
            ):
                returning = self.state == "RETURNING_HOME"
                self.state = "REPLANNING"
                self.reason = "Hazard changed; navigation cancelled"
                self.stop_actions()
                if returning:
                    self.return_home()
            elif self.state in ("SCANNING", "REPLANNING"):
                self.state = "PLANNING"
                if self.cloud_enabled:
                    request = str(uuid.uuid4())
                    self.cloud_request = (request, self.seconds())
                    self.publish_json(
                        self.cloud_pub,
                        "cloud_request",
                        {"request_id": request, "world": self.world.reasoning_state(self.battery)},
                    )
                else:
                    self.local_plan()
            elif (
                self.state == "PLANNING"
                and self.cloud_request
                and self.seconds() - self.cloud_request[1] >= self.cloud_timeout
            ):
                self.cloud_request = None
                self.local_plan()
            elif (
                self.state in ("NAVIGATING", "RETURNING_HOME")
                and self.result_future
                and self.result_future.done()
            ):
                result = self.result_future.result()
                self.goal = None
                self.result_future = None
                if self.state == "RETURNING_HOME":
                    self.state = "PAUSED"
                    self.reason = (
                        "Home reached; human charging assistance required"
                        if result.status == GoalStatus.STATUS_SUCCEEDED
                        else "Home unreachable; human charging assistance required"
                    )
                elif result.status == GoalStatus.STATUS_SUCCEEDED:
                    self.begin_clean()
                else:
                    self.failed.add(self.target)
                    self.state = "REPLANNING"
                    self.reason = "Nav2 target unreachable"
            elif self.state == "RETRYING":
                self.begin_clean()
            elif self.state == "CLEANING" and self.seconds() > self.clean_deadline:
                self.state = "PAUSED"
                self.reason = "Cleaning verification timed out"
                self.stop_actions()
        self.publish_json(
            self.state_pub,
            "mission_state",
            {
                "state": self.state,
                "mission_id": self.mission_id,
                "reason": self.reason,
                "target_id": self.target,
                "pass_number": self.pass_number,
                "failed_regions": sorted(self.failed),
            },
        )

    def destroy_node(self):
        self.stop_actions()
        return super().destroy_node()


def main():
    spin(PlannerNode)

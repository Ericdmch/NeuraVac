"""ROS-only navigation acceptance harness. Uses no robot hardware or serial port."""
import json
import math
import os
import threading
import sys
import time
from array import array
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, qos_profile_sensor_data
from geometry_msgs.msg import PoseStamped, TransformStamped, Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from std_srvs.srv import Trigger
from tf2_ros import TransformBroadcaster
from neuravac_mapping.driver_watchdog import DriverWatchdog


class SimulatedSerial:
    is_open = True
    def __init__(self, world):
        self.world = world
    def write(self, data):
        if data == bytes([131]):
            return
        if len(data) != 5 or data[0] != 145:
            raise ValueError('Unexpected serial command')
        right = int.from_bytes(data[1:3], 'big', signed=True) / 1000.
        left = int.from_bytes(data[3:5], 'big', signed=True) / 1000.
        self.world.v = (left + right) / 2
        self.world.w = (right - left) / .235


class World(Node):
    def __init__(self):
        super().__init__('autonomy_fake_world')
        self.x = self.y = self.yaw = 0.
        self.v = self.w = 0.
        self.last_cmd = 0.
        self._sensor_condition = threading.Condition()
        self._serial_lock = threading.RLock()
        self._latest_group_zero = bytes(26)
        self._latest_group_zero_at = time.monotonic()
        self.serial = SimulatedSerial(self)
        self.fault_test = os.environ.get('FAKE_BUMPER') == '1'
        self.last_update = time.monotonic()
        self.last_received_command = None
        self.started = self.returned = False
        self.start_time = time.monotonic()
        self.result = None
        durable = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.map = self.create_publisher(OccupancyGrid, 'map', durable)
        self.slam_map = self.create_publisher(OccupancyGrid, 'slam/map', durable)
        self.pose = self.create_publisher(PoseStamped, 'slam/pose', 10)
        self.odom = self.create_publisher(Odometry, 'odom', 10)
        self.scan = self.create_publisher(LaserScan, 'scan', qos_profile_sensor_data)
        self.slam_status = self.create_publisher(String, 'slam/status', 10)
        self.request = self.create_publisher(String, 'autonomy/request', 10)
        self.create_subscription(String, 'autonomy/state', self.state, 10)
        self.watchdog = DriverWatchdog(self)
        self.create_subscription(Twist, 'autonomy/cmd_vel', self.monitor_command, 10)
        self.tf = TransformBroadcaster(self)
        self.create_timer(.05, self.update)
        self.create_timer(1., self.publish_map)
        self.create_timer(1., self.control)
        self.publish_map()

    def monitor_command(self, _msg):
        now = time.monotonic()
        if self.last_received_command is not None and now - self.last_received_command > .2:
            print(f'HEARTBEAT_GAP {now - self.last_received_command:.3f}s', flush=True)
        self.last_received_command = now

    def state(self, msg):
        data = json.loads(msg.data)
        if self.started and data['state'] == 'stopped':
            self.result = ('PASSED: bumper stopped simulated robot' if self.fault_test and
                           self.watchdog.guard.reason == 'bumper' and self.v == 0. and self.w == 0.
                           else 'FAILED: ' + str(data['reason']))
        if not self.fault_test and self.returned and data['state'] == 'complete':
            self.result = 'PASSED: simulated exploration moved and returned'

    def control(self):
        elapsed = time.monotonic() - self.start_time
        if not self.started and elapsed > 12.:
            self.request.publish(String(data=json.dumps({'command': 'start', 'return_goal': [0., 0.]})))
            self.started = True
        if not self.fault_test and self.started and not self.returned and math.hypot(self.x, self.y) > .18:
            self.request.publish(String(data=json.dumps({'command': 'return'})))
            self.returned = True
        if elapsed > 50 and self.result is None:
            self.result = f'FAILED: timeout at x={self.x:.2f}, y={self.y:.2f}, armed={self.watchdog.guard.armed}'
        if self.result:
            print(self.result, flush=True)
            rclpy.shutdown()

    def publish_map(self):
        m = OccupancyGrid()
        m.header.frame_id = 'map'
        m.header.stamp = self.get_clock().now().to_msg()
        m.info.resolution = .05
        m.info.width = m.info.height = 80
        m.info.origin.position.x = m.info.origin.position.y = -2.
        m.info.origin.orientation.w = 1.
        m.data = array('b', [0 if 5 <= x < 60 and 5 <= y < 60 else -1
                             for y in range(80) for x in range(80)])
        self.map.publish(m)
        self.slam_map.publish(m)

    def update(self):
        now = time.monotonic()
        if now - self.last_update > .2:
            print(f'WORLD_TIMER_GAP {now - self.last_update:.3f}s', flush=True)
        self.last_update = now
        self._latest_group_zero_at = now
        if self.fault_test and math.hypot(self.x, self.y) > .12:
            self._latest_group_zero = bytes([1] + [0]*25)
        self.x += self.v * math.cos(self.yaw) * .05
        self.y += self.v * math.sin(self.yaw) * .05
        self.yaw += self.w * .05
        stamp = self.get_clock().now().to_msg()
        qz, qw = math.sin(self.yaw/2), math.cos(self.yaw/2)
        transforms = []
        for parent, child, x, y, z, w in [('map','odom',0.,0.,0.,1.),
                                         ('odom','base_link',self.x,self.y,qz,qw),
                                         ('base_link','lidar_link',0.,0.,0.,1.)]:
            tf = TransformStamped()
            tf.header.stamp, tf.header.frame_id, tf.child_frame_id = stamp, parent, child
            tf.transform.translation.x, tf.transform.translation.y = x, y
            tf.transform.rotation.z, tf.transform.rotation.w = z, w
            transforms.append(tf)
        self.tf.sendTransform(transforms)
        pose = PoseStamped()
        pose.header.stamp, pose.header.frame_id = stamp, 'map'
        pose.pose.position.x, pose.pose.position.y = self.x, self.y
        pose.pose.orientation.z, pose.pose.orientation.w = qz, qw
        self.pose.publish(pose)
        odom = Odometry()
        odom.header.stamp, odom.header.frame_id, odom.child_frame_id = stamp, 'odom', 'base_link'
        odom.pose.pose = pose.pose
        odom.twist.twist.linear.x, odom.twist.twist.angular.z = self.v, self.w
        self.odom.publish(odom)
        scan = LaserScan()
        scan.header.stamp, scan.header.frame_id = stamp, 'lidar_link'
        scan.angle_min, scan.angle_max = -math.pi, math.pi
        scan.angle_increment = math.tau/360
        scan.range_min, scan.range_max = .05, 5.
        scan.ranges = [3.] * 360
        self.scan.publish(scan)
        self.slam_status.publish(String(data='TRACKING'))


if __name__ == '__main__':
    rclpy.init()
    node = World()
    try:
        rclpy.spin(node)
    except Exception as error:
        if rclpy.ok():
            raise error
    finally:
        result = node.result
        node.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if result and result.startswith('PASSED') else 1)

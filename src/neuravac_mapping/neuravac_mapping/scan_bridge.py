"""Deskew native D6 scans with measured odometry and publish the TF chain."""
from collections import deque
import json
import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from roomba_interfaces.msg import SerialData
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster
from .scan_math import PoseHistory, deskew_ranges
from .scan_stability import ScanStability


def seconds(stamp):
    return stamp.sec + stamp.nanosec * 1e-9


class ScanBridge(Node):
    def __init__(self):
        super().__init__('neuravac_scan_bridge')
        for key, value in [('lidar_x_m', 0.), ('lidar_y_m', 0.), ('lidar_yaw_rad', 0.)]:
            self.declare_parameter(key, value)
        self.mount = tuple(self.get_parameter(k).value for k in
                           ('lidar_x_m', 'lidar_y_m', 'lidar_yaw_rad'))
        self.history = PoseHistory()
        self.stability = ScanStability()
        self.pending = deque(maxlen=3)
        self.contact_windows = deque(maxlen=40)
        self.published = self.rejected = 0
        self.last_odom = self.last_scan = None
        self.tf = TransformBroadcaster(self)
        self.static_tf = StaticTransformBroadcaster(self)
        mount = TransformStamped()
        mount.header.stamp = self.get_clock().now().to_msg()
        mount.header.frame_id, mount.child_frame_id = 'base_link', 'lidar_link'
        mount.transform.translation.x, mount.transform.translation.y = self.mount[:2]
        mount.transform.rotation.z = math.sin(self.mount[2] / 2)
        mount.transform.rotation.w = math.cos(self.mount[2] / 2)
        self.static_tf.sendTransform(mount)
        self.scan_pub = self.create_publisher(LaserScan, 'scan', qos_profile_sensor_data)
        self.diagnostics = self.create_publisher(String, 'mapping/scan_diagnostics', 10)
        self.create_subscription(Odometry, 'odom', self.on_odom, 50)
        self.create_subscription(SerialData, 'roomba/sensors', self.on_sensors, 10)
        self.create_subscription(LaserScan, 'scan_raw', self.on_scan, qos_profile_sensor_data)
        self.create_timer(.02, self.process)
        self.create_timer(1., self.report)

    def on_odom(self, msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y*q.y + q.z*q.z))
        self.history.add(seconds(msg.header.stamp), (p.x, p.y, yaw))
        self.last_odom = self.get_clock().now().nanoseconds * 1e-9
        transform = TransformStamped()
        transform.header = msg.header
        transform.child_frame_id = msg.child_frame_id
        transform.transform.translation.x = p.x
        transform.transform.translation.y = p.y
        transform.transform.rotation = q
        self.tf.sendTransform(transform)

    def on_sensors(self, msg):
        if len(msg.data) == 26 and msg.data[0] & 31:
            now = self.get_clock().now().nanoseconds * 1e-9
            # Include the sensor polling interval before reported contact.
            self.contact_windows.append((now - .1, now + .35))

    def on_scan(self, msg):
        self.pending.append(msg)

    def process(self):
        if not self.pending:
            return
        msg = self.pending[0]
        start = seconds(msg.header.stamp)
        end = start + msg.scan_time
        now = self.get_clock().now().nanoseconds * 1e-9
        if any(start <= finish and end >= begin for begin, finish in self.contact_windows):
            self.pending.popleft()
            self.rejected += 1
            return
        if not self.history.samples or self.history.samples[-1][0] < end:
            if now - end > .5:
                self.pending.popleft()
                self.rejected += 1
            return
        self.pending.popleft()
        ranges = deskew_ranges(msg.ranges, msg.angle_min, msg.angle_increment,
                               start, msg.time_increment, end, self.history,
                               mount=self.mount)
        if ranges is None or sum(math.isfinite(v) for v in ranges) < 30:
            self.rejected += 1
            return
        pose = self.history.at(end)
        if pose is None or not self.stability.accept(ranges, pose, end):
            self.rejected += 1
            return
        scan = LaserScan()
        scan.header.stamp = Time(seconds=end).to_msg()
        scan.header.frame_id = 'lidar_link'
        scan.angle_min = -math.pi
        scan.angle_increment = 2 * math.pi / len(ranges)
        scan.angle_max = scan.angle_min + (len(ranges) - 1) * scan.angle_increment
        # Already transformed to a single acquisition reference time.
        scan.time_increment = 0.
        scan.scan_time = msg.scan_time
        scan.range_min, scan.range_max = .12, 8.
        scan.ranges = ranges
        self.scan_pub.publish(scan)
        self.published += 1
        self.last_scan = now

    def report(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        self.diagnostics.publish(String(data=json.dumps(dict(
            published_scans=self.published, rejected_scans=self.rejected,
            pending_scans=len(self.pending), unstable_scans_held=self.stability.held,
            odom_age_s=None if self.last_odom is None else now-self.last_odom,
            scan_age_s=None if self.last_scan is None else now-self.last_scan,
            timing='reconstructed from serial receipt seams; no hardware clock'))))


def main():
    rclpy.init()
    node = ScanBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

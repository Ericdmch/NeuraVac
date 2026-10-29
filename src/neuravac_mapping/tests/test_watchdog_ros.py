"""Exercise the watchdog against a ROS node and a fake serial port only."""
import threading
import time
import unittest
from types import SimpleNamespace
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from neuravac_mapping.driver_watchdog import DriverWatchdog


class FakeSerial:
    is_open = True
    def __init__(self):
        self.writes = []
    def write(self, command):
        self.writes.append(bytes(command))


class FakeDriver(Node):
    def __init__(self):
        super().__init__('fake_roomba_watchdog_test')
        self.serial = FakeSerial()
        self._serial_lock = threading.RLock()
        self._sensor_condition = threading.Condition()
        self._latest_group_zero = bytes(26)
        self._latest_group_zero_at = time.monotonic()


class WatchdogRosTests(unittest.TestCase):
    def setUp(self):
        rclpy.init()
        self.node = FakeDriver()
        self.watchdog = DriverWatchdog(self.node)
        stamp = self.node.get_clock().now().to_msg()
        scan = LaserScan()
        scan.header.stamp = stamp
        scan.angle_increment = 6.2831853 / 360
        scan.range_min, scan.range_max = .05, 10.
        scan.ranges = [1.] * 360
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = stamp
        pose.pose.orientation.w = 1.
        odom = Odometry()
        odom.header.frame_id, odom.child_frame_id = 'odom', 'base_link'
        odom.header.stamp = stamp
        odom.pose.pose.orientation.w = 1.
        self.watchdog.on_scan(scan)
        self.watchdog.on_pose(pose)
        self.watchdog.on_odom(odom)
        self.watchdog.on_status(String(data='TRACKING'))

    def tearDown(self):
        self.node.destroy_node()
        rclpy.try_shutdown()

    def test_contact_stops_active_drive(self):
        response = self.watchdog.arm(None, SimpleNamespace())
        self.assertTrue(response.success, response.message)
        twist = Twist()
        twist.linear.x = .05
        self.watchdog.on_velocity(twist)
        self.assertEqual(self.node.serial.writes[-1], bytes([145, 0, 50, 0, 50]))
        self.node._latest_group_zero = bytes([1] + [0]*25)
        self.watchdog.tick()
        self.assertEqual(self.node.serial.writes[-1], bytes([145, 0, 0, 0, 0]))
        self.assertFalse(self.watchdog.guard.armed)

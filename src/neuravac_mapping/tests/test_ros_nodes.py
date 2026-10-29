"""ROS constructor contracts; run in an isolated ROS_DOMAIN_ID on the Pi."""
import time
import unittest
from unittest.mock import patch
import rclpy
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import LaserScan
from roomba_interfaces.msg import SerialData
from rclpy.time import Time
from neuravac_mapping.scan_bridge import ScanBridge
from neuravac_mapping.dashboard_bridge import DashboardBridge

class NodeTests(unittest.TestCase):
    def setUp(self):
        rclpy.init()

    def tearDown(self):
        rclpy.try_shutdown()

    def test_scan_bridge_constructs_tf_and_scan_publishers(self):
        node = ScanBridge()
        try:
            self.assertEqual(node.scan_pub.topic_name, '/scan')
            self.assertEqual(node.mount, (0., 0., 0.))
        finally:
            node.destroy_node()

    def test_fresh_tf_without_scans_is_not_tracking(self):
        node = DashboardBridge()
        try:
            tf = TransformStamped()
            tf.header.stamp = node.get_clock().now().to_msg()
            tf.header.frame_id = 'map'
            tf.child_frame_id = 'base_link'
            tf.transform.rotation.w = 1.
            with patch.object(node.buffer, 'lookup_transform', return_value=tf), \
                 patch.object(node.status_pub, 'publish') as publish:
                node.publish_pose()
                self.assertEqual(publish.call_args.args[0].data, 'WAITING FOR SCANS')
                node.last_scan_received = time.monotonic()
                node.publish_pose()
                self.assertEqual(publish.call_args.args[0].data, 'TRACKING')
        finally:
            node.destroy_node()

    def test_contact_scan_is_rejected_before_map_insertion(self):
        node = ScanBridge()
        try:
            now = node.get_clock().now().nanoseconds * 1e-9
            scan = LaserScan()
            scan.header.stamp = Time(seconds=now-.05).to_msg()
            scan.scan_time = .1
            node.on_sensors(SerialData(data=[1] + [0]*25))
            node.on_scan(scan)
            node.process()
            self.assertEqual(node.rejected, 1)
            self.assertFalse(node.pending)
        finally:
            node.destroy_node()

"""Pose must keep measured body orientation and all motion after rejected scans."""
import math
import threading
import unittest
import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from web.web_node import LidarBridge
from web.travel_heading import TravelHeading
from neuravac_slam.slam_node import LidarMapper

class PoseFrameTests(unittest.TestCase):
    def test_map_arrow_is_body_heading_even_after_reverse(self):
        bridge = LidarBridge.__new__(LidarBridge)
        bridge._pose_lock = threading.Lock()
        bridge._map_condition = threading.Condition()
        bridge._map = None
        bridge._travel_heading = TravelHeading()
        bridge._travel_heading.offset = 0.7
        bridge._travel_heading.command([137, 255, 56, 128, 0])
        message = PoseStamped()
        message.pose.position.x = 1.2
        message.pose.position.y = -0.3
        message.pose.orientation.z = math.sin(0.4 / 2)
        message.pose.orientation.w = math.cos(0.4 / 2)
        bridge.pose_callback(message)
        self.assertAlmostEqual(bridge._slam_pose['yaw'], .4)
        self.assertAlmostEqual(bridge._slam_pose['x'], 1.2)
        self.assertAlmostEqual(bridge._slam_pose['y'], -.3)

    def test_failed_match_does_not_lose_previous_wheel_motion(self):
        rclpy.init()
        node = LidarMapper()
        try:
            node._pose = np.array((2., 3., math.pi / 2))
            node._display_anchor = (node._pose.copy(), np.zeros(3))
            node._odom_at_last_scan = np.zeros(3)
            node._predict_from_odometry(np.array((.1, 0., 0.)))
            # Failed scan restores trusted pose, but odometry baseline advanced.
            node._pose = node._display_anchor[0].copy()
            node._predict_from_odometry(np.array((.2, 0., 0.)))
            np.testing.assert_allclose(node._pose, (2., 3.2, math.pi / 2), atol=1e-12)
        finally:
            node.destroy_node()
            rclpy.try_shutdown()

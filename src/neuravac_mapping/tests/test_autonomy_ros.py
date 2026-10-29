"""Coordinator tests in isolated ROS; no driver or motor topics are connected."""
import json
import unittest
import time
from unittest.mock import patch, PropertyMock
from rclpy.parameter import Parameter
from array import array
import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import String
from neuravac_mapping.autonomy_node import AutonomyNode


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        rclpy.init()
        self.node = AutonomyNode()

    def tearDown(self):
        self.node.destroy_node()
        rclpy.try_shutdown()

    def test_motion_is_disabled_by_default(self):
        self.node.on_request(String(data=json.dumps({'command': 'start', 'return_goal': [0, 0]})))
        self.assertEqual(self.node.mission.state, 'idle')
        self.assertIn('disabled', self.node.mission.reason)
        self.assertFalse(self.node.armed)

    def test_grid_and_pose_produce_local_planner(self):
        msg = OccupancyGrid()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.info.width, msg.info.height, msg.info.resolution = 8, 8, 1.
        msg.info.origin.orientation.w = 1.
        msg.data = array('b', [0]*64)
        self.node.on_map(msg)
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.node.get_clock().now().to_msg()
        pose.pose.position.x = pose.pose.position.y = 4.5
        self.node.on_pose(pose)
        self.assertTrue(self.node.planner().return_reachable((4.5, 4.5), (5.5, 5.5)))

    def test_route_search_does_not_block_ros_callback(self):
        class SlowPlanner:
            def next_goal(self, position):
                time.sleep(.4)
                return (1., 2.)
        self.node.mission.start((0., 0.), True)
        self.node.armed = True
        self.node.position = (0., 0.)
        with patch.object(self.node, 'planner', return_value=SlowPlanner()):
            started = time.monotonic()
            self.node.plan_next()
            self.assertLess(time.monotonic() - started, .2)
            self.assertIsNotNone(self.node.plan_future)

    def test_return_preflight_does_not_block_ros_callback(self):
        class SlowPlanner:
            def return_reachable(self, position, goal):
                time.sleep(.4)
                return True
        self.node.set_parameters([Parameter('enable_motion', value=True),
                                  Parameter('behavior_tree', value='/test/tree.xml')])
        self.node.position = (0., 0.)
        with patch.object(self.node, 'planner', return_value=SlowPlanner()), \
             patch.object(self.node.arm_client, 'service_is_ready', return_value=True), \
             patch.object(self.node.disarm_client, 'service_is_ready', return_value=True), \
             patch.object(self.node.navigator, 'server_is_ready', return_value=True):
            started = time.monotonic()
            self.node.start([1., 2.])
            self.assertLess(time.monotonic() - started, .2)
            self.assertEqual(self.node.plan_kind, 'preflight')

    def test_missing_arm_response_stops_mission(self):
        self.node.mission.start((0., 0.), True)
        self.node.arm_started = time.monotonic() - 3.
        self.node.tick()
        self.assertEqual(self.node.mission.state, 'stopped')
        self.assertIn('watchdog', self.node.mission.reason)

    def test_old_pose_is_not_treated_as_fresh(self):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.pose.position.x = 1.
        self.node.on_pose(pose)
        self.assertIsNone(self.node.position)

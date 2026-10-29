"""Verify scan-matched pose reaches the occupancy-map dashboard stream."""
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import String
from web.web_node import LidarBridge


class SlamPoseTests(unittest.TestCase):
    def test_live_pose_streams_without_a_new_grid(self):
        bridge = object.__new__(LidarBridge)
        bridge._pose_lock = threading.Lock()
        bridge._map_condition = threading.Condition()
        bridge._map_sequence = 7
        bridge._map = {'data': 'unchanged'}
        pose = PoseStamped()
        pose.pose.position.x = 0.2
        pose.pose.orientation.w = 1.0
        bridge.pose_callback(pose)
        sequence, snapshot = bridge.wait_for_map(7, timeout=0)
        self.assertEqual(sequence, 8)
        self.assertEqual(snapshot['robot_x'], 0.2)
        self.assertEqual(snapshot['data'], 'unchanged')

    def test_recovery_status_streams_even_when_grid_is_unchanged(self):
        bridge = object.__new__(LidarBridge)
        bridge._map_condition = threading.Condition()
        bridge._map_sequence = 7
        bridge._map = {'data': 'unchanged', 'robot_x': 1.0}
        bridge.status_callback(String(data='RECOVERING'))
        sequence, snapshot = bridge.wait_for_map(7, timeout=0)
        self.assertEqual(sequence, 8)
        self.assertEqual(snapshot['tracking_status'], 'RECOVERING')
        self.assertEqual(snapshot['data'], 'unchanged')
        self.assertEqual(snapshot['robot_x'], 1.0)

    def test_pose_is_attached_to_map_snapshot(self):
        bridge = object.__new__(LidarBridge)
        bridge._pose_lock = threading.Lock()
        bridge._slam_pose = None
        bridge._map_condition = threading.Condition()
        bridge._map_sequence = 0
        bridge._map = None

        pose = PoseStamped()
        pose.pose.position.x = 1.25
        pose.pose.position.y = -0.5
        pose.pose.orientation.w = 1.0
        bridge.pose_callback(pose)

        grid = OccupancyGrid()
        grid.info.width = 2
        grid.info.height = 2
        grid.info.resolution = 0.05
        grid.info.origin.position.x = -10.0
        grid.info.origin.position.y = -10.0
        bridge.map_callback(grid)

        sequence, snapshot = bridge.wait_for_map(-1, timeout=0)
        self.assertEqual(sequence, 1)
        self.assertEqual(snapshot['robot_x'], 1.25)
        self.assertEqual(snapshot['robot_y'], -0.5)
        self.assertAlmostEqual(snapshot['robot_yaw'], 0.0)


if __name__ == '__main__':
    unittest.main()

"""Verify the COIN-D6 clockwise angle convention maps into ROS coordinates."""
import unittest
import tempfile
import time
from pathlib import Path

import numpy as np
import rclpy
from std_srvs.srv import Trigger

from neuravac_slam.slam_node import LidarMapper, rotation_search_angles, scan_to_cartesian


class ScanCoordinateTests(unittest.TestCase):
    def test_clockwise_lidar_angle_becomes_clockwise_local_y(self):
        scan = np.array(((0.0, 1.0), (np.pi / 2, 1.0), (np.pi, 1.0)))
        points = scan_to_cartesian(scan)
        np.testing.assert_allclose(
            points,
            ((1.0, 0.0), (0.0, -1.0), (-1.0, 0.0)),
            atol=1e-12,
        )

    def test_fixed_wall_aligns_after_counter_clockwise_robot_turn(self):
        # A wall point at world (2, 0) appears at local (0, -2) after a
        # 90-degree counter-clockwise turn, which the D6 reports as +90 deg.
        local = scan_to_cartesian(np.array(((np.pi / 2, 2.0),)))[0]
        yaw = np.pi / 2
        rotation = np.array(((np.cos(yaw), -np.sin(yaw)),
                             (np.sin(yaw), np.cos(yaw))))
        world = rotation @ local
        np.testing.assert_allclose(world, (2.0, 0.0), atol=1e-12)

    def test_scan_matching_search_widens_when_odometry_is_stale(self):
        fallback = rotation_search_angles(False, 0.2, 0.8, 19)
        self.assertEqual(len(fallback), 19)
        self.assertAlmostEqual(fallback[0], -0.8)
        self.assertAlmostEqual(fallback[-1], 0.8)

        odom_guided = rotation_search_angles(True, 0.2, 0.8, 19)
        self.assertEqual(len(odom_guided), 9)
        self.assertAlmostEqual(odom_guided[0], -0.2)
        self.assertAlmostEqual(odom_guided[-1], 0.2)


class MapProtectionTests(unittest.TestCase):
    def setUp(self):
        rclpy.init()
        self.mapper = LidarMapper()

    def tearDown(self):
        self.mapper.destroy_node()
        rclpy.shutdown()

    def test_rejected_alignment_cannot_modify_map(self):
        mapper = self.mapper
        mapper.grid[10, 10] = 12
        mapper._last_scan = np.zeros((40, 2))
        original = mapper.grid.copy()

        def poor_match(points):
            mapper._match_score = 0.01
            return np.array((1.0, 1.0, 1.0))

        mapper._match_scan = poor_match
        scan = np.column_stack((np.linspace(0, 6.2, 40), np.ones(40)))
        mapper._process_scan(scan)
        np.testing.assert_array_equal(mapper.grid, original)
        np.testing.assert_array_equal(mapper._pose, np.zeros(3))

    def test_collision_pause_cannot_modify_map(self):
        mapper = self.mapper
        mapper._collision_until = time.monotonic() + 10
        scan = np.column_stack((np.linspace(0, 6.2, 40), np.ones(40)))
        mapper._process_scan(scan)
        self.assertFalse(mapper.grid.any())

    def test_saved_checkpoint_restores_grid_and_pose(self):
        mapper = self.mapper
        with tempfile.TemporaryDirectory() as directory:
            mapper.map_file = Path(directory) / 'room.npz'
            mapper.grid[10, 10] = 12
            mapper._pose[:] = (1.0, 2.0, 0.3)
            self.assertTrue(mapper.save_map(None, Trigger.Response()).success)
            mapper.grid.fill(0)
            mapper._pose.fill(0)
            self.assertTrue(mapper.load_map(None, Trigger.Response()).success)
            self.assertEqual(mapper.grid[10, 10], 12)
            np.testing.assert_allclose(mapper._pose, (1.0, 2.0, 0.3))


if __name__ == '__main__':
    unittest.main()

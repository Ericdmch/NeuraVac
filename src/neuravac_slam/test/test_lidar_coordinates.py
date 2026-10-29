"""Verify the COIN-D6 clockwise angle convention maps into ROS coordinates."""
import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
import rclpy
from std_srvs.srv import Trigger

from neuravac_slam.slam_node import LidarMapper, refine_icp, rotation_search_angles, scan_to_cartesian


class ScanCoordinateTests(unittest.TestCase):
    def test_icp_recovers_rigid_motion_with_distant_outliers(self):
        rng = np.random.default_rng(4)
        points = rng.uniform(-2, 2, (100, 2))
        yaw = 0.03
        rotation = np.array(((np.cos(yaw), -np.sin(yaw)),
                             (np.sin(yaw), np.cos(yaw))))
        target = points @ rotation.T + (0.03, -0.02)
        noisy = np.vstack((points, rng.uniform(8, 9, (10, 2))))
        pose, ratio, error = refine_icp(noisy, target, np.zeros(3))
        np.testing.assert_allclose(pose, (0.03, -0.02, yaw), atol=0.01)
        self.assertGreater(ratio, 0.85)
        self.assertLess(error, 0.01)

    def test_icp_rejects_clouds_without_correspondences(self):
        points = np.column_stack((np.arange(40), np.zeros(40)))
        _, ratio, error = refine_icp(points, points + (0, 10), np.zeros(3))
        self.assertEqual(ratio, 0)
        self.assertTrue(np.isinf(error))

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

    def test_recovery_requires_three_consistent_scans(self):
        mapper = self.mapper
        mapper.grid[10, :40] = 12
        mapper._last_scan = np.zeros((40, 2))
        mapper._recovering = True
        original = mapper.grid.copy()

        def good_match(points):
            mapper._match_score = 1.0
            return np.array((0.01, 0.0, 0.01))

        mapper._match_scan = good_match
        scan = np.column_stack((np.linspace(0, 6.2, 40), np.ones(40)))
        with patch('neuravac_slam.slam_node.refine_icp',
                   return_value=(np.array((0.01, 0.0, 0.01)), 1.0, 0.01)):
            for _ in range(2):
                mapper._process_scan(scan)
                np.testing.assert_array_equal(mapper.grid, original)
                np.testing.assert_array_equal(mapper._pose, np.zeros(3))
            mapper._process_scan(scan)
        self.assertFalse(mapper._recovering)
        np.testing.assert_allclose(mapper._pose, (0.01, 0.0, 0.01))

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

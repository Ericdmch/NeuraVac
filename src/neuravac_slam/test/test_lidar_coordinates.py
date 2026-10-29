"""Verify the COIN-D6 clockwise angle convention maps into ROS coordinates."""
import unittest

import numpy as np

from neuravac_slam.slam_node import rotation_search_angles, scan_to_cartesian


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


if __name__ == '__main__':
    unittest.main()

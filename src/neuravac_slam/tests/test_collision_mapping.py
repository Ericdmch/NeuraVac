"""Collision scans must never add evidence to the room map."""
import unittest
from unittest.mock import patch

import numpy as np
import rclpy
from roomba_interfaces.msg import SerialData, LidarPoint
from neuravac_slam.slam_node import LidarMapper


class CollisionMappingTests(unittest.TestCase):
    def setUp(self):
        rclpy.init()
        self.node = LidarMapper()
        self.scan = np.column_stack((np.linspace(0, 2 * np.pi, 180), np.full(180, 2.0)))

    def tearDown(self):
        self.node.destroy_node()
        rclpy.try_shutdown()

    def bump(self):
        self.node.on_serial(SerialData(data=[1] + [0] * 25))

    def test_contact_invalidates_queued_scan_even_after_pause_expires(self):
        generation = self.node._generation
        self.bump()
        self.node._collision_until = 0
        self.node._process_scan(self.scan, generation)
        self.assertEqual(self.node._map_version, 0)
        self.assertFalse(self.node.grid.any())

    def test_contact_during_ray_insertion_rolls_back_entire_scan(self):
        original = self.node._trace_ray
        def trace(start, end):
            original(start, end)
            self.bump()
        with patch.object(self.node, '_trace_ray', side_effect=trace):
            self.node._process_scan(self.scan, self.node._generation)
        self.assertFalse(self.node.grid.any())
        self.assertEqual(self.node._map_version, 0)

    def test_points_during_contact_cannot_form_next_scan(self):
        self.node._scan = [(0, 1)] * 50
        self.node._have_scan_seam = True
        self.bump()
        self.node.on_point(LidarPoint(angle_deg=20.0, distance_mm=1000.0))
        self.assertFalse(self.node._scan)
        self.assertFalse(self.node._have_scan_seam)

    def test_recovery_requires_two_consistent_scans(self):
        self.node._process_scan(self.scan, self.node._generation)
        version = self.node._map_version
        self.bump()
        self.node._collision_until = 0
        # A deterministic good fit isolates recovery confirmation from ICP.
        with patch('neuravac_slam.slam_node.refine_icp',
                   return_value=(np.zeros(3), 1.0, 0.0)):
            self.node._process_scan(self.scan, self.node._generation)
            self.assertEqual(self.node._map_version, version)
            self.assertTrue(self.node._recovering)
            self.node._process_scan(self.scan, self.node._generation)
        self.assertEqual(self.node._map_version, version + 1)
        self.assertFalse(self.node._recovering)

    def test_bad_alignment_keeps_map_unchanged(self):
        self.node._process_scan(self.scan, self.node._generation)
        before = self.node.grid.copy()
        self.bump()
        self.node._collision_until = 0
        with patch('neuravac_slam.slam_node.refine_icp',
                   return_value=(np.zeros(3), 0.1, 0.5)):
            self.node._process_scan(self.scan, self.node._generation)
        np.testing.assert_array_equal(self.node.grid, before)
        self.assertTrue(self.node._recovering)

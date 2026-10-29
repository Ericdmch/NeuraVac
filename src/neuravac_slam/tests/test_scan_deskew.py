"""Synthetic fixed-room targets observed while robot rotates and translates."""
import unittest
import math
import numpy as np
from neuravac_slam.slam_node import deskew_scan

class DeskewTests(unittest.TestCase):
    def test_fixed_wall_during_rotation_and_translation(self):
        poses = np.column_stack((np.linspace(0, .2, 80), np.zeros(80), np.linspace(0, .6, 80)))
        world = np.column_stack((np.full(80, 3.), np.linspace(-1, 1, 80)))
        delta = world - poses[:, :2]
        angles = np.arctan2(delta[:, 1], delta[:, 0]) - poses[:, 2]
        scan = np.column_stack((-angles, np.linalg.norm(delta, axis=1), poses))
        result = deskew_scan(scan)
        c, s = math.cos(poses[-1, 2]), math.sin(poses[-1, 2])
        expected = (world - poses[-1, :2]) @ np.array(((c, -s), (s, c)))
        np.testing.assert_allclose(result, expected, atol=1e-12)

    def test_stationary_and_legacy_scan(self):
        raw = np.array(((0., 2.), (math.pi / 2, 1.)))
        expected = np.array(((2., 0.), (0., -1.)))
        np.testing.assert_allclose(deskew_scan(raw), expected, atol=1e-12)
        full = np.column_stack((raw, np.tile((1., 2., .3), (2, 1))))
        np.testing.assert_allclose(deskew_scan(full), expected, atol=1e-12)

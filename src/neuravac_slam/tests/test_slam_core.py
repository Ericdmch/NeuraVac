import math

import numpy as np

from neuravac_slam.slam_core import RecoveryGate, polar_to_points, transform_points, wrap_angle


def test_wrap_angle_crosses_pi_seam():
    assert math.isclose(wrap_angle(-math.pi - 0.1), math.pi - 0.1)
    assert math.isclose(wrap_angle(math.pi + 0.1), -math.pi + 0.1)


def test_transform_applies_rotation_then_translation():
    points = np.array(((1.0, 0.0), (0.0, 1.0)))
    actual = transform_points(points, (2.0, 3.0, math.pi / 2))
    np.testing.assert_allclose(actual, ((2.0, 4.0), (1.0, 3.0)), atol=1e-12)


def test_polar_conversion_and_invalid_input_filtering():
    scan = np.array(((0.0, 2.0), (math.pi / 2, 1.0), (math.nan, 3.0)))
    actual = polar_to_points(scan)
    np.testing.assert_allclose(actual, ((2.0, 0.0), (0.0, 1.0)), atol=1e-12)


def test_recovery_requires_multiple_overlapping_observations():
    angles = np.linspace(0.0, 2.0 * math.pi, 80, endpoint=False)
    cloud = np.column_stack((np.cos(angles), np.sin(angles)))
    gate = RecoveryGate(required=3)
    pose = np.zeros(3)
    assert not gate.observe(pose, cloud)
    assert not gate.observe(pose, cloud + 0.01)
    assert gate.observe(pose, cloud - 0.01)


def test_recovery_restarts_when_pose_or_scan_geometry_disagrees():
    angles = np.linspace(0.0, 2.0 * math.pi, 80, endpoint=False)
    cloud = np.column_stack((np.cos(angles), np.sin(angles)))
    gate = RecoveryGate(required=3)
    assert not gate.observe(np.zeros(3), cloud)
    displaced = np.array((0.5, 0.0, 0.0))
    assert not gate.observe(displaced, cloud)
    assert gate.count == 1
    assert not gate.observe(displaced, cloud)
    assert gate.observe(displaced, cloud)

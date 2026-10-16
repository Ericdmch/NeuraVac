import math

import pytest

from neuravac_robot.odometry import Odometry, wrap_angle, yaw_to_quaternion


def test_straight_line():
    odom = Odometry()
    for _ in range(10):
        pose = odom.update(distance_mm=100, angle_deg=0)
    assert pose.x == pytest.approx(1.0)
    assert pose.y == pytest.approx(0.0, abs=1e-9)
    assert pose.yaw == pytest.approx(0.0)


def test_reverse_goes_backwards():
    pose = Odometry().update(distance_mm=-500, angle_deg=0)
    assert pose.x == pytest.approx(-0.5)


def test_counter_clockwise_spin_in_place():
    odom = Odometry()
    for _ in range(9):
        pose = odom.update(distance_mm=0, angle_deg=10)
    assert pose.x == pytest.approx(0.0, abs=1e-9)
    assert pose.yaw == pytest.approx(math.pi / 2)


def test_driving_after_a_left_turn_goes_along_y():
    odom = Odometry()
    odom.update(0, 90)
    pose = odom.update(1000, 0)
    assert pose.x == pytest.approx(0.0, abs=1e-9)
    assert pose.y == pytest.approx(1.0)


def test_quarter_circle_arc():
    # Radius 1 m: each 1 degree step travels 1 m * (pi/180).
    odom = Odometry()
    step_mm = 1000 * math.pi / 180
    for _ in range(90):
        pose = odom.update(step_mm, 1)
    assert pose.x == pytest.approx(1.0, abs=0.005)
    assert pose.y == pytest.approx(1.0, abs=0.005)
    assert pose.yaw == pytest.approx(math.pi / 2)


def test_yaw_wraps_and_reset():
    odom = Odometry()
    for _ in range(3):
        pose = odom.update(0, 90)
    assert -math.pi <= pose.yaw < math.pi
    assert pose.yaw == pytest.approx(-math.pi / 2)    # 270 degrees wraps to -90
    odom.reset()
    assert odom.pose.x == odom.pose.y == odom.pose.yaw == 0.0
    assert wrap_angle(3 * math.pi / 2) == pytest.approx(-math.pi / 2)


def test_quaternion_is_unit_length():
    for yaw in (0.0, 1.0, -2.5, math.pi):
        x, y, z, w = yaw_to_quaternion(yaw)
        assert math.sqrt(x * x + y * y + z * z + w * w) == pytest.approx(1.0)

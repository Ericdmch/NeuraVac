"""Verify travel-derived front heading for forward, reverse, and noisy poses."""
import math
import unittest

from web.travel_heading import TravelHeading


class TravelHeadingTests(unittest.TestCase):
    def test_first_moving_update_can_calibrate_after_short_key_press(self):
        heading = TravelHeading()
        heading.update(0, 0, math.pi / 2, 0)
        heading.command([137, 0, 200, 128, 0])
        self.assertAlmostEqual(heading.update(0.025, 0, math.pi / 2, 0.1), 0)

    def test_first_reverse_update_can_calibrate_after_short_key_press(self):
        heading = TravelHeading()
        heading.update(0, 0, math.pi / 2, 0)
        heading.command([137, 255, 56, 128, 0])
        self.assertAlmostEqual(heading.update(-0.025, 0, math.pi / 2, 0.1), 0)

    def test_forward_calibrates_from_displacement(self):
        heading = TravelHeading()
        heading.command([137, 0, 200, 128, 0])
        heading.update(0, 0, math.pi / 2, 0)
        self.assertAlmostEqual(heading.update(0.1, 0, math.pi / 2, 0.5), 0)

    def test_reverse_preserves_front_direction(self):
        heading = TravelHeading()
        heading.command([137, 255, 56, 128, 0])
        heading.update(0, 0, math.pi / 2, 0)
        self.assertAlmostEqual(heading.update(-0.1, 0, math.pi / 2, 0.5), 0)

    def test_stationary_noise_does_not_calibrate(self):
        heading = TravelHeading()
        heading.command([137, 0, 200, 128, 0])
        heading.update(0, 0, 1.0, 0)
        self.assertAlmostEqual(heading.update(0.005, 0, 1.0, 0.5), 1.0)

    def test_turn_uses_heading_change_after_calibration(self):
        heading = TravelHeading()
        heading.command([137, 0, 200, 128, 0])
        heading.update(0, 0, 1.0, 0)
        heading.update(0.1, 0, 1.0, 0.5)
        heading.command([137, 0, 200, 0, 1])
        self.assertAlmostEqual(heading.update(0.1, 0, 1.5, 1.0), 0.5)

    def test_pose_jump_is_not_travel_calibration(self):
        heading = TravelHeading()
        heading.command([137, 0, 200, 128, 0])
        heading.update(0, 0, 1.0, 0)
        self.assertAlmostEqual(heading.update(2, 0, 1.0, 0.5), 1.0)

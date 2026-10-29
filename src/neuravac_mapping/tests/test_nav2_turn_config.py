"""Navigation's first turn command must exceed the Roomba wheel speed step."""
from pathlib import Path
import re
import unittest


class TurnConfigTests(unittest.TestCase):
    def test_first_turn_exceeds_roomba_speed_step_and_stays_bounded(self):
        text = (Path(__file__).resolve().parents[1] / 'config/autonomy_nav2.yaml').read_text()
        def value(key):
            match = re.search(r'^\s*' + re.escape(key) + r':\s*([0-9.]+)', text, re.M)
            self.assertIsNotNone(match, key)
            return float(match.group(1))
        acceleration = value('max_angular_accel')
        frequency = value('controller_frequency')
        turn_speed = value('rotate_to_heading_angular_vel')
        wheel_mps = min(acceleration / frequency, turn_speed) * .235 / 2
        self.assertGreater(wheel_mps, .0285)
        self.assertLessEqual(wheel_mps, .15)
        self.assertGreaterEqual(value('yaw_goal_tolerance'), 3.14159)
        self.assertGreater(value('min_approach_linear_velocity'), .0285)
        self.assertGreater(value('regulated_linear_scaling_min_speed'), .0285)
        self.assertGreater(value('robot_radius'), .25)

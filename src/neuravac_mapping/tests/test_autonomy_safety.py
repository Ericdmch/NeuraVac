import unittest
from neuravac_mapping.autonomy_safety import safety_fault


def safe_robot():
    return {'online': True, 'bridge_connected': True, 'age_seconds': 0.1,
            'values': {name: False for name in ('bump_left', 'bump_right',
                'wheel_drop_left', 'wheel_drop_right', 'cliff_left', 'cliff_right',
                'cliff_front_left', 'cliff_front_right', 'overcurrent', 'virtual_wall')}}


class SafetyTests(unittest.TestCase):
    def test_all_hazard_flags_stop(self):
        for flag in safe_robot()['values']:
            with self.subTest(flag=flag):
                robot = safe_robot()
                robot['values'][flag] = True
                self.assertEqual(safety_fault(robot, True), flag)

    def test_missing_or_stale_data_fails_closed(self):
        for change in ({'online': False}, {'bridge_connected': False},
                       {'age_seconds': 2.0}, {'values': None}, {'values': {}}):
            robot = safe_robot()
            robot.update(change)
            self.assertIsNotNone(safety_fault(robot, True))
        self.assertIsNotNone(safety_fault(safe_robot(), False))

    def test_fresh_safe_data_passes(self):
        self.assertIsNone(safety_fault(safe_robot(), True))

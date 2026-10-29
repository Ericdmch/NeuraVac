import unittest

from neuravac_mapping.mission_supervisor import MissionSupervisor


class MissionSupervisorTests(unittest.TestCase):
    def test_mapping_finishes_and_returns_then_stops(self):
        mission = MissionSupervisor()
        mission.start((2.0, 3.0), True)
        self.assertEqual(mission.state, 'exploring')
        mission.exploration_finished()
        self.assertEqual(mission.state, 'returning')
        self.assertEqual(mission.return_goal, (2.0, 3.0))
        mission.return_finished(True)
        self.assertEqual(mission.state, 'complete')

    def test_unreachable_return_stops_and_waits(self):
        mission = MissionSupervisor()
        mission.start((1.0, 2.0), True)
        mission.exploration_finished()
        mission.return_finished(False)
        self.assertEqual(mission.state, 'stopped')
        self.assertIn('unreachable', mission.reason)

    def test_contact_or_stale_input_latches_stop(self):
        for reason in ('bumper', 'cliff', 'wheel drop', 'stale telemetry', 'stale scan', 'lost localization'):
            with self.subTest(reason=reason):
                mission = MissionSupervisor()
                mission.start((1.0, 2.0), True)
                mission.hazard(reason)
                self.assertEqual(mission.state, 'stopped')
                self.assertEqual(mission.reason, reason)
                mission.exploration_finished()
                self.assertEqual(mission.state, 'stopped')

    def test_start_requires_readiness_and_valid_return(self):
        mission = MissionSupervisor()
        with self.assertRaises(ValueError):
            mission.start((1, 2), False)
        with self.assertRaises(ValueError):
            mission.start((float('nan'), 2), True)
        self.assertEqual(mission.state, 'idle')

    def test_operator_can_end_exploration_and_return(self):
        mission = MissionSupervisor()
        mission.start((1, 2), True)
        mission.request_return()
        self.assertEqual(mission.state, 'returning')


if __name__ == '__main__':
    unittest.main()

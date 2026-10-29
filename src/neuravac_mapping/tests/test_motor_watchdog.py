import unittest
from neuravac_mapping.motor_watchdog import MotorWatchdog


class WatchdogTests(unittest.TestCase):
    def test_missing_heartbeat_stops_and_latches(self):
        guard = MotorWatchdog(timeout=.3)
        guard.arm(10.)
        self.assertTrue(guard.heartbeat(10.1, True))
        self.assertFalse(guard.check(10.41, True))
        self.assertFalse(guard.heartbeat(10.42, True))
        self.assertEqual(guard.reason, 'autonomous command timeout')

    def test_contact_stops_immediately_even_with_fresh_heartbeat(self):
        guard = MotorWatchdog(timeout=.3)
        guard.arm(2.)
        self.assertTrue(guard.heartbeat(2.1, True))
        self.assertFalse(guard.check(2.11, False, 'bumper'))
        self.assertEqual(guard.reason, 'bumper')
        self.assertFalse(guard.heartbeat(2.12, True))

    def test_manual_control_preempts_and_requires_explicit_rearm(self):
        guard = MotorWatchdog()
        guard.arm(0.)
        guard.preempt('manual control')
        self.assertFalse(guard.heartbeat(.1, True))
        guard.arm(.2)
        self.assertTrue(guard.heartbeat(.21, True))

    def test_clock_regression_latches_stop(self):
        guard = MotorWatchdog()
        guard.arm(5.)
        self.assertFalse(guard.heartbeat(4., True))

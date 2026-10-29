import math
import unittest
from neuravac_mapping.scan_stability import ScanStability

class StabilityTests(unittest.TestCase):
    def test_transient_distortion_is_held_then_normal_resumes(self):
        g = ScanStability()
        good = [2.0] * 180
        bad = [1.1] * 180
        self.assertTrue(g.accept(good, (0, 0, 0), 0))
        self.assertFalse(g.accept(bad, (0, 0, 0), .1))
        self.assertTrue(g.accept(good, (0, 0, 0), .2))

    def test_real_persistent_change_recovers_without_stalling(self):
        g = ScanStability()
        self.assertTrue(g.accept([2.] * 180, (0,0,0), 0))
        self.assertFalse(g.accept([1.] * 180, (0,0,0), .1))
        self.assertTrue(g.accept([1.] * 180, (0,0,0), .2))

    def test_large_robot_motion_does_not_trigger_naive_comparison(self):
        g = ScanStability()
        self.assertTrue(g.accept([2.] * 180, (0,0,0), 0))
        self.assertTrue(g.accept([1.] * 180, (.2,0,0), .1))

    def test_large_loss_of_returns_is_held(self):
        g = ScanStability()
        self.assertTrue(g.accept([2.] * 180, (0,0,0), 0))
        self.assertFalse(g.accept([2.] * 30 + [math.inf] * 150, (0,0,0), .1))

import math
import unittest
from neuravac_mapping.scan_math import PoseHistory, ScanAssembler, deskew_ranges

class ScanMathTests(unittest.TestCase):
    def test_pose_interpolates_across_yaw_wrap_without_extrapolation(self):
        h = PoseHistory()
        h.add(0, (0, 0, math.radians(179)))
        h.add(.1, (.1, 0, math.radians(-179)))
        self.assertAlmostEqual(abs(h.at(.05)[2]), math.pi)
        self.assertIsNone(h.at(.2))
        self.assertAlmostEqual(h.at(.05)[0], .05)

    def test_scan_seam_preserves_clockwise_acquisition_order(self):
        a = ScanAssembler(bins=360)
        result = None
        for i in range(721):
            completed = a.add(i % 360, 1000, i / 1800)
            if completed:
                result = completed
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['duration'], .2)
        self.assertLess(result['angle_increment'], 0)
        self.assertAlmostEqual(result['stamp'], .2)
        self.assertEqual(result['ranges'][90], 1)

    def test_incomplete_or_delayed_revolution_is_not_published(self):
        a = ScanAssembler()
        for angle in range(0, 360, 10):
            self.assertIsNone(a.add(angle, 1000, angle / 1800))
        self.assertIsNone(a.add(0, 1000, 2))

    def test_deskew_fixed_wall_while_turning_and_translating(self):
        h = PoseHistory()
        # A single ray acquired facing east, then robot moves 0.1m forward
        # and turns left 90deg. Endpoint is east in world, now to the right.
        h.add(0, (0, 0, 0))
        h.add(.1, (.1, 0, math.pi / 2))
        out = deskew_ranges([2.], 0., 0., 0., 0., .1, h, bins=360)
        self.assertAlmostEqual(out[90], 1.9)
        self.assertEqual(sum(math.isfinite(v) for v in out), 1)

    def test_scan_without_complete_odometry_is_rejected(self):
        h = PoseHistory()
        h.add(0, (0, 0, 0))
        self.assertIsNone(deskew_ranges([1.], 0, 0, 0, 0, .1, h))

    def test_mount_offset_and_invalid_ranges(self):
        h = PoseHistory()
        h.add(0, (0, 0, 0))
        h.add(.1, (0, 0, 0))
        out = deskew_ranges([1, 0, float('nan'), float('inf')], 0, 0, 0, 0, .1, h,
                            bins=360, mount=(.2, .1, .3))
        self.assertAlmostEqual(out[180], 1.)
        self.assertEqual(sum(math.isfinite(v) for v in out), 1)

    def test_nonzero_seam_angle_does_not_shift_ray_times(self):
        a = ScanAssembler(bins=360)
        a.add(350, 1000, -.02)
        a.add(30, 1000, 0.)
        for angle in range(31, 360):
            a.add(angle, 1000, (angle-30)/1800)
        result = a.add(30, 1000, .2)
        self.assertAlmostEqual(result['duration'], .2)
        self.assertAlmostEqual(result['stamp'], -.2 * 30 / 360)

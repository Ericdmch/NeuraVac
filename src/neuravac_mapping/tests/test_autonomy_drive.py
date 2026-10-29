import unittest
from neuravac_mapping.autonomy_drive import drive_command, safety_from_group_zero


class DriveTests(unittest.TestCase):
    def test_unsafe_or_missing_group_zero_rejected(self):
        good = bytearray(26)
        self.assertIsNone(safety_from_group_zero(good))
        for index, bit in [(0, 1), (0, 2), (0, 4), (2, 1), (5, 1), (6, 1), (7, 1), (16, 2)]:
            sensor = bytearray(good)
            sensor[index] = bit
            self.assertIsNotNone(safety_from_group_zero(sensor))
        self.assertIsNotNone(safety_from_group_zero(None))
        self.assertIsNotNone(safety_from_group_zero(bytes(25)))

    def test_drive_conversion_is_bounded_and_stops(self):
        self.assertEqual(drive_command(0., 0.), bytes([145, 0, 0, 0, 0]))
        self.assertEqual(drive_command(.1, 0.), bytes([145, 0, 100, 0, 100]))
        self.assertEqual(drive_command(0., 1.), bytes([145, 0, 117, 255, 139]))
        with self.assertRaises(ValueError):
            drive_command(float('nan'), 0.)
        with self.assertRaises(ValueError):
            drive_command(1., 0.)

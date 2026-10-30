"""Sensor protocol and freshness checks against hand-checked OI packet fixtures."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.telemetry import SensorState, decode_group_zero

# Real 26-byte group 0 response: -1796 mm, -365 degrees, 14750 mV,
# -258 mA, 32 C, 1970 / 2696 mAh. Values are big-endian and signed as specified.
PACKET = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                248, 252, 254, 147, 4, 57, 158, 254, 254, 32, 7, 178, 10, 136])


class SensorTests(unittest.TestCase):
    def test_decodes_signed_motion_and_battery_fields(self):
        values = decode_group_zero(PACKET)
        self.assertEqual(values['voltage_v'], 14.75)
        self.assertEqual(values['current_ma'], -258)
        self.assertEqual(values['temperature_c'], 32)
        self.assertEqual(values['charge_mah'], 1970)
        self.assertEqual(values['capacity_mah'], 2696)
        self.assertEqual(values['battery_percent'], 73.1)
        self.assertEqual(values['distance_mm'], -1796)
        self.assertEqual(values['angle_deg'], -365)
        self.assertEqual(values['charging_state'], 'Waiting')

    def test_preserves_bumper_wheeldrop_and_cliff_bits(self):
        packet = bytearray(PACKET)
        packet[0] = 0b1001  # left wheel drop, right bumper
        packet[3] = 1  # cliff front left
        values = decode_group_zero(packet)
        self.assertTrue(values['bump_right'])
        self.assertFalse(values['bump_left'])
        self.assertTrue(values['wheel_drop_left'])
        self.assertFalse(values['wheel_drop_right'])
        self.assertTrue(values['cliff_front_left'])
        self.assertFalse(values['cliff_right'])

    def test_zero_capacity_is_unknown_not_zero_percent(self):
        packet = bytearray(PACKET)
        packet[24:26] = b'\x00\x00'
        self.assertIsNone(decode_group_zero(packet)['battery_percent'])

    def test_rejects_wrong_length_and_invalid_boolean(self):
        with self.assertRaises(ValueError):
            decode_group_zero(PACKET[:-1])
        packet = bytearray(PACKET)
        packet[2] = 255
        with self.assertRaises(ValueError):
            decode_group_zero(packet)

    def test_fragmented_reply_is_published_only_when_complete(self):
        state = SensorState()
        self.assertTrue(state.request(10))
        state.receive(PACKET[:9], 10.1)
        self.assertFalse(state.snapshot(10.1)['online'])
        state.receive(PACKET[9:], 10.2)
        self.assertTrue(state.snapshot(10.2)['online'])
        self.assertEqual(state.snapshot(10.2)['values']['current_ma'], -258)

    def test_unsolicited_and_late_replies_do_not_become_fresh_readings(self):
        state = SensorState()
        state.receive(PACKET, 10)
        self.assertFalse(state.snapshot(10)['online'])
        state.request(11)
        state.receive(PACKET, 12)
        self.assertFalse(state.snapshot(12)['online'])

    def test_stale_readings_are_not_shown_as_current(self):
        state = SensorState()
        state.request(10)
        state.receive(PACKET, 10.1)
        self.assertTrue(state.snapshot(11)['online'])
        stale = state.snapshot(10.1 + state.MAX_AGE + 1.0)
        self.assertFalse(stale['online'])
        self.assertIsNone(stale['values'])


if __name__ == '__main__':
    unittest.main()

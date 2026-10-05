"""Protocol checks using synthetic responses; no robot or pyserial required."""

import contextlib
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sensors


def sci_packet():
    # 10 environment bytes, remote/buttons, distance/angle, battery bytes.
    return bytes.fromhex(
        "15 01 00 01 00 01 01 1b 2a 33 ff 09 "
        "ff 9c 00 81 02 38 40 fe 0c fb 03 e8 07 d0"
    )


class FakeSerial:
    def __init__(self, data, chunks=3):
        self.data = bytearray(data)
        self.chunks = chunks
        self.timeout = 2
        self.commands = []
        self.closed = False

    def read(self, size):
        size = min(size, self.chunks)
        chunk = bytes(self.data[:size])
        del self.data[:size]
        return chunk

    def write(self, data):
        self.commands.append(data)
        return len(data)

    def flush(self):
        pass

    def reset_input_buffer(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


class SensorTests(unittest.TestCase):
    def test_sci_signed_values_bit_masks_and_angle(self):
        result = sensors.decode_sensors(sci_packet(), "sci")
        self.assertEqual(result["distance_mm"], -100)
        self.assertAlmostEqual(result["angle_degrees"], 180 / sensors.math.pi)
        self.assertEqual(result["battery_voltage_mv"], 14400)
        self.assertEqual(result["battery_current_ma"], -500)
        self.assertEqual(result["battery_temperature_c"], -5)
        self.assertEqual(result["battery_percent"], 50)
        self.assertTrue(result["bumps_wheeldrops"]["wheeldrop_caster"])
        self.assertTrue(result["motor_overcurrents"]["vacuum"])
        self.assertEqual(result["buttons"],
                         {"max": True, "clean": False, "spot": False, "power": True})
        self.assertEqual(result["dirt_detector_right"], 51)

    def test_oi_full_packet_offsets_and_different_meanings(self):
        packet = bytearray(sci_packet() + bytes(54))
        packet[39] = 3  # packet 34: both charging sources
        packet[40] = 1  # packet 35: passive mode
        packet[52:54] = b"\xff\xff"  # packet 43: left encoder
        packet[56] = 0x21  # packet 45: left and right light bumper
        packet[71:73] = b"\xff\x9c"  # packet 54: left motor current
        packet[79] = 3  # last byte, stasis
        result = sensors.decode_sensors(packet, "oi")
        self.assertEqual(result["angle_degrees"], 129)
        self.assertEqual(result["encoder_counts_left"], 65535)
        self.assertEqual(result["left_motor_current_ma"], -100)
        self.assertEqual(result["stasis_raw"], 3)
        self.assertTrue(result["buttons"]["clean"])
        self.assertTrue(result["buttons"]["minute"])
        self.assertNotIn("vacuum", result["motor_overcurrents"])
        self.assertNotIn("wheeldrop_caster", result["bumps_wheeldrops"])
        self.assertEqual(result["oi_mode_name"], "passive")
        self.assertTrue(all(result["charging_sources"].values()))
        self.assertTrue(result["light_bumper"]["left"])
        self.assertTrue(result["light_bumper"]["right"])

    def test_zero_capacity_unknown_state_and_bad_size(self):
        packet = bytearray(26)
        packet[16] = 255
        result = sensors.decode_sensors(packet, "sci")
        self.assertIsNone(result["battery_percent"])
        self.assertEqual(result["charging_state_name"], "unknown")
        for size in (0, 25, 27):
            with self.assertRaises(ValueError):
                sensors.decode_sensors(bytes(size), "sci")

    def test_partial_reads_and_timeout_restore(self):
        connection = FakeSerial(sci_packet())
        self.assertEqual(sensors.read_exact(connection, 26, 2), sci_packet())
        self.assertEqual(connection.timeout, 2)
        connection = FakeSerial(b"\x01\x02")
        with self.assertRaisesRegex(TimeoutError, "2/26 bytes"):
            sensors.read_exact(connection, 26, 2)
        self.assertEqual(connection.timeout, 2)

    def test_cli_oi_commands_json_and_closes_port(self):
        connection = FakeSerial(bytes(80))
        module = types.SimpleNamespace(Serial=lambda *a, **k: connection)
        output = io.StringIO()
        with patch.dict(sys.modules, {"serial": module}), \
                patch("sensors.time.sleep"), contextlib.redirect_stdout(output):
            status = sensors.main(["--port", "fake", "--once"])
        self.assertEqual(status, 0)
        self.assertEqual(connection.commands, [b"\x80", b"\x96\x00", b"\x8e\x64"])
        self.assertEqual(json.loads(output.getvalue())["packet_group"], 100)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()

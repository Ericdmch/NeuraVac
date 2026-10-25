"""Verify restored speed controls and release commands without robot hardware."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.web_node import create_app


class SerialSink:
    def __init__(self):
        self.commands = []

    def send_message(self, message):
        self.commands.append(list(message.data))


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.serial = SerialSink()
        self.client = create_app(self.serial, None, '/tmp').test_client()

    def key(self, key, pressed=True):
        return self.client.post('/override', json={'key': key, 'pressed': pressed})

    def test_speed_adjustment_changes_drive_bytes_without_moving_on_its_own(self):
        self.assertEqual(self.key('E').json['speed'], 250)
        self.assertEqual(self.serial.commands, [])
        self.key('W')
        self.assertEqual(self.serial.commands, [[137, 0, 250, 128, 0]])
        self.key('W', False)
        self.assertEqual(self.serial.commands[-1], [137, 0, 0, 128, 0])

    def test_speed_limits_are_bounded(self):
        for _ in range(20):
            self.key('Q')
        self.assertEqual(self.key('Q').json['speed'], 50)
        for _ in range(20):
            self.key('E')
        self.assertEqual(self.key('E').json['speed'], 500)
        self.assertEqual(self.serial.commands, [])

    def test_releasing_an_inactive_key_does_not_cancel_the_active_key(self):
        self.key('A')
        self.key('W', False)
        self.assertEqual(self.serial.commands, [[137, 0, 200, 0, 1]])
        self.key('A', False)
        self.assertEqual(self.serial.commands[-1], [137, 0, 0, 128, 0])


if __name__ == '__main__':
    unittest.main()

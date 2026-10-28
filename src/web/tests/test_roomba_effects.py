"""Verify Roomba LED and song web controls without robot hardware."""
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


class RoombaEffectTests(unittest.TestCase):
    def setUp(self):
        self.serial = SerialSink()
        self.client = create_app(self.serial, None, '/tmp').test_client()

    def test_led_sends_expected_oi_command(self):
        response = self.client.post(
            '/roomba/led', json={'color': 128, 'intensity': 200}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.serial.commands, [[139, 0, 128, 200]])

    def test_led_rejects_invalid_values_without_sending(self):
        for payload in (
            {'color': -1, 'intensity': 0},
            {'color': 1, 'intensity': 256},
            {'color': True, 'intensity': 0},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(
                    self.client.post('/roomba/led', json=payload).status_code, 400
                )
        self.assertEqual(self.serial.commands, [])

    def test_song_definition_and_play_are_one_ordered_write(self):
        response = self.client.post('/roomba/song', json={
            'song_number': 3,
            'notes': [{'note': 60, 'duration': 8}, {'note': 64, 'duration': 12}],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.serial.commands, [[140, 3, 2, 60, 8, 64, 12, 141, 3]])

    def test_song_rejects_invalid_notes_without_sending(self):
        for payload in (
            {'song_number': 16, 'notes': [{'note': 60, 'duration': 8}]},
            {'song_number': 0, 'notes': [{'note': 30, 'duration': 8}]},
            {'song_number': 0, 'notes': [{'note': 60, 'duration': 256}]},
            {'song_number': 0, 'notes': []},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(
                    self.client.post('/roomba/song', json=payload).status_code, 400
                )
        self.assertEqual(self.serial.commands, [])


if __name__ == '__main__':
    unittest.main()

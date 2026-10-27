"""LatestJpeg: the camera feed used when vision owns the webcam."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.camera import LatestJpeg


class LatestJpegTests(unittest.TestCase):
    def test_no_frame_yet_is_offline(self):
        self.assertIsNone(LatestJpeg().snapshot())

    def test_returns_newest_frame(self):
        feed = LatestJpeg()
        feed.update(b'\xff\xd8one\xff\xd9')
        feed.update(bytearray(b'\xff\xd8two\xff\xd9'))
        self.assertEqual(feed.snapshot(), b'\xff\xd8two\xff\xd9')

    def test_stale_frame_is_not_served(self):
        feed = LatestJpeg()
        with mock.patch('web.camera.time.monotonic', return_value=100.0):
            feed.update(b'frame')
        with mock.patch('web.camera.time.monotonic', return_value=101.0):
            self.assertEqual(feed.snapshot(), b'frame')
        with mock.patch('web.camera.time.monotonic', return_value=103.0):
            self.assertIsNone(feed.snapshot())

    def test_start_and_close_are_safe(self):
        feed = LatestJpeg()
        feed.start()
        feed.close()


if __name__ == '__main__':
    unittest.main()

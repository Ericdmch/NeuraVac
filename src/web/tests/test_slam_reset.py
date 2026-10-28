"""Verify the dashboard forwards map reset requests without robot hardware."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.web_node import create_app


class ResetSink:
    def __init__(self, result=(True, 'SLAM map and pose reset.')):
        self.result = result
        self.calls = 0

    def reset_slam(self):
        self.calls += 1
        return self.result


class SlamResetTests(unittest.TestCase):
    def setUp(self):
        self.reset = ResetSink()
        self.client = create_app(None, self.reset, '/tmp').test_client()

    def test_reset_endpoint_invokes_slam_service_bridge(self):
        response = self.client.post('/slam/reset')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['reset'])
        self.assertEqual(self.reset.calls, 1)

    def test_unavailable_slam_service_returns_error(self):
        self.reset.result = (False, 'SLAM reset service is unavailable.')
        response = self.client.post('/slam/reset')
        self.assertEqual(response.status_code, 503)
        self.assertIn('unavailable', response.json['error'])
        self.assertEqual(self.reset.calls, 1)


if __name__ == '__main__':
    unittest.main()

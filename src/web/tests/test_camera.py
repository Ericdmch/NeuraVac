"""Camera HTTP contract: valid JPEG, stale feed, and no configured camera."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.web_node import create_app


class Camera:
    def __init__(self, jpeg=None):
        self.jpeg = jpeg

    def snapshot(self):
        return self.jpeg


class CameraEndpointTests(unittest.TestCase):
    def client(self, camera=None):
        return create_app(None, None, '/tmp', camera=camera).test_client()

    def test_returns_latest_jpeg_without_caching(self):
        camera = Camera(b'\xff\xd8first\xff\xd9')
        client = self.client(camera)
        response = client.get('/camera/frame')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/jpeg')
        self.assertEqual(response.data, b'\xff\xd8first\xff\xd9')
        self.assertIn('no-store', response.headers['Cache-Control'])
        camera.jpeg = b'\xff\xd8second\xff\xd9'
        self.assertEqual(client.get('/camera/frame').data, b'\xff\xd8second\xff\xd9')

    def test_camera_disconnect_does_not_serve_previous_frame(self):
        camera = Camera(b'frame')
        client = self.client(camera)
        self.assertEqual(client.get('/camera/frame').status_code, 200)
        camera.jpeg = None
        response = client.get('/camera/frame')
        self.assertEqual(response.status_code, 503)
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_missing_camera_does_not_break_dashboard(self):
        self.assertEqual(self.client().get('/camera/frame').status_code, 503)


if __name__ == '__main__':
    unittest.main()

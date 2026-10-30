import unittest
from neuravac_mapping.autonomy_http import create_app


class Bridge:
    def __init__(self):
        self.requests = []
    def snapshot(self):
        return {'state': {'state': 'idle'}, 'map': None, 'pose': None}
    def send(self, request):
        self.requests.append(request)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.bridge = Bridge()
        self.client = create_app(self.bridge).test_client()

    def test_snapshot_and_map_screen(self):
        self.assertEqual(self.client.get('/api/state').json['state']['state'], 'idle')
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_start_requires_finite_return_goal(self):
        self.assertEqual(self.client.post('/api/mission', json={'command': 'start'}).status_code, 400)
        self.assertEqual(self.client.post('/api/mission', json={'command': 'start', 'return_goal': [float('nan'), 0]}).status_code, 400)
        self.assertEqual(self.client.post('/api/mission', json={'command': 'start', 'return_goal': [1, 2]}).status_code, 202)
        self.assertEqual(self.bridge.requests[-1]['return_goal'], [1, 2])
        self.assertEqual(self.client.post('/api/mission', json={'command': 'goto', 'return_goal': [3, 4]}).status_code, 202)
        self.assertEqual(self.bridge.requests[-1], {'command': 'goto', 'return_goal': [3, 4]})

    def test_stop_and_return_are_accepted(self):
        for command in ('stop', 'return'):
            self.assertEqual(self.client.post('/api/mission', json={'command': command}).status_code, 202)
        self.assertEqual(self.client.post('/api/mission', json={'command': 'drive'}).status_code, 400)

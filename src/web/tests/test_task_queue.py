"""Unit tests for the draggable Roomba task queue, polygon cleaning, dock seeking (143), and override preemption."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.task_queue import TaskQueueManager, generate_polygon_waypoints, generate_polygon_tiles
from web.web_node import create_app, VisionMarkerStore


class SerialSink:
    def __init__(self):
        self.commands = []

    def send_message(self, message):
        self.commands.append(list(message.data))


class FakeAutonomyBridge:
    def __init__(self):
        self.requests = []
        self.motion_enabled = False
        self.state = {'state': 'idle', 'armed': False, 'reason': ''}
        self.vision_store = VisionMarkerStore()
        self.pose = [0.0, 0.0]

    def set_motion_enabled(self, enabled):
        self.motion_enabled = bool(enabled)
        return True, 'ok'

    def send_autonomy_request(self, body):
        self.requests.append(dict(body))
        if body.get('command') in ('goto', 'start'):
            self.state = {'state': 'returning', 'armed': True, 'reason': 'Navigating'}
        elif body.get('command') == 'stop':
            self.state = {'state': 'stopped', 'armed': False, 'reason': 'operator stop'}

    def autonomy_snapshot(self):
        return {
            'state': dict(self.state),
            'costmap': None,
            'path': None,
            'pose': list(self.pose),
            'motion_enabled': self.motion_enabled,
            'vision': self.vision_store.snapshot(),
        }


class TaskQueueTests(unittest.TestCase):
    def test_queue_auto_starts_reorders_and_advances_on_completion(self):
        dispatched = []
        stopped = []
        cleaning = []
        docked = []
        mgr = TaskQueueManager(
            dispatch_fn=lambda t: dispatched.append(t['title']),
            stop_fn=lambda: stopped.append(True),
            cleaning_fn=lambda flag: cleaning.append(flag),
            seek_dock_fn=lambda: docked.append(True),
        )

        t1 = mgr.add_task('goto', params={'target': [1.0, 2.0]})
        t2 = mgr.add_task('scan_area', title='Scan Area', params={'target': [0.5, 0.5]})
        t3 = mgr.add_task('return_home', title='Return to Dock', params={'target': [0.0, 0.0]})

        snap = mgr.snapshot()
        self.assertEqual([t['id'] for t in snap['queue']], [t1['id'], t2['id'], t3['id']])
        self.assertEqual(snap['queue'][0]['status'], 'active')
        self.assertEqual(dispatched, ['Go to (1.00, 2.00) m'])

        # Dragging t2 to the top demotes t1 back to queued and immediately starts t2
        reordered = mgr.reorder([t2['id'], t1['id'], t3['id']])
        self.assertEqual([t['id'] for t in reordered], [t2['id'], t1['id'], t3['id']])
        self.assertEqual(reordered[0]['status'], 'active')
        self.assertEqual(reordered[1]['status'], 'queued')
        self.assertEqual(dispatched[-1], 'Scan Area')

        # Simulate robot arming and completing t2
        mgr.snapshot({'state': 'exploring', 'armed': True, 'reason': 'Exploring'})
        after = mgr.snapshot({'state': 'complete', 'armed': False, 'reason': 'Done'})
        self.assertEqual([t['id'] for t in after['queue']], [t1['id'], t3['id']])
        self.assertEqual(after['queue'][0]['status'], 'active')
        self.assertEqual(after['history'][0]['id'], t2['id'])

    def test_polygon_region_generation_and_multi_waypoint_cleaning(self):
        square = [[0.0, 0.0], [0.6, 0.0], [0.6, 0.6], [0.0, 0.6]]
        wps = generate_polygon_waypoints(square, spacing_m=0.25)
        self.assertGreaterEqual(len(wps), 4)

        serial = SerialSink()
        bridge = FakeAutonomyBridge()
        client = create_app(serial, bridge, '/tmp').test_client()

        reg_res = client.post('/regions', json={
            'name': 'Rug Zone',
            'vertices': square,
            'queue_clean': True,
        })
        self.assertEqual(reg_res.status_code, 201)
        data = reg_res.json
        self.assertEqual(len(data['regions']), 1)
        self.assertEqual(data['regions'][0]['name'], 'Rug Zone')
        self.assertEqual(data['queue'][0]['type'], 'clean_polygon')
        self.assertEqual(data['queue'][0]['status'], 'active')
        self.assertIn([138, 7], serial.commands)
        self.assertEqual(bridge.requests[-1]['command'], 'goto')

    def test_return_home_and_dock_endpoint_send_seek_dock_opcode_143(self):
        serial = SerialSink()
        bridge = FakeAutonomyBridge()
        client = create_app(serial, bridge, '/tmp').test_client()

        # Direct dock endpoint sends opcode 143
        r_dock = client.post('/roomba/dock')
        self.assertEqual(r_dock.status_code, 200)
        self.assertIn([143], serial.commands)

        # Queued return_home navigates to (0, 0) then triggers opcode 143 on completion
        serial.commands.clear()
        r_task = client.post('/tasks', json={'type': 'return_home', 'title': 'Return to Dock'})
        self.assertEqual(r_task.status_code, 201)
        self.assertEqual(bridge.requests[-1], {'command': 'goto', 'return_goal': [0.0, 0.0]})

        # Snapshot while armed so _busy_seen is recorded, then complete Nav2 leg -> triggers Opcode 143
        client.get('/tasks')
        bridge.state = {'state': 'complete', 'armed': False, 'reason': 'Arrived at (0.00, 0.00) m'}
        snap = client.get('/tasks').json
        self.assertIn([143], serial.commands)
        self.assertIn('Opcode 143', snap['queue'][0]['note'])

    def test_manual_override_inserts_at_top_and_resumes_queue(self):
        serial = SerialSink()
        bridge = FakeAutonomyBridge()
        client = create_app(serial, bridge, '/tmp').test_client()

        r1 = client.post('/tasks', json={'type': 'scan_area', 'title': 'Scan Area', 'params': {'target': [0.5, 0.5]}})
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r1.json['queue'][0]['title'], 'Scan Area')
        self.assertEqual(r1.json['queue'][0]['status'], 'active')

        # Pressing W inserts Manual Override at index 0 and demotes Scan Area to queued
        client.post('/override', json={'key': 'W', 'pressed': True})
        q_override = client.get('/tasks').json['queue']
        self.assertEqual(q_override[0]['type'], 'override')
        self.assertEqual(q_override[0]['status'], 'active')
        self.assertEqual(q_override[1]['title'], 'Scan Area')
        self.assertEqual(q_override[1]['status'], 'queued')

        # Deleting/clearing the override task resumes Scan Area at index 0
        client.delete('/tasks/override-active')
        q_resumed = client.get('/tasks').json['queue']
        self.assertEqual(len(q_resumed), 1)
        self.assertEqual(q_resumed[0]['title'], 'Scan Area')
        self.assertEqual(q_resumed[0]['status'], 'active')

    def test_polygon_tiles_and_sweep_clearing(self):
        square = [[0.0, 0.0], [0.5, 0.0], [0.5, 0.5], [0.0, 0.5]]
        tiles = generate_polygon_tiles(square, tile_size_m=0.10)
        self.assertGreater(len(tiles), 5)

        serial = SerialSink()
        bridge = FakeAutonomyBridge()
        bridge.pose = [10.0, 10.0]  # Start robot far away from the region
        client = create_app(serial, bridge, '/tmp').test_client()

        # Create region with queue_clean = True
        res = client.post('/regions', json={'name': 'Kitchen', 'vertices': square, 'queue_clean': True})
        self.assertEqual(res.status_code, 201)
        reg = res.json['regions'][0]
        self.assertTrue(reg['cleaning_active'])
        self.assertEqual(len(reg['uncleaned_tiles']), reg['total_tiles'])
        self.assertEqual(reg['progress_pct'], 0)

        # Robot sweeps through corner (0.05, 0.05)
        bridge.pose = [0.05, 0.05]
        snap = client.get('/autonomy/state').json
        after_reg = snap['task_queue']['regions'][0]
        self.assertLess(len(after_reg['uncleaned_tiles']), after_reg['total_tiles'])
        self.assertGreater(after_reg['progress_pct'], 0)
        self.assertGreater(len(after_reg['swept_points']), 0)

    def test_vision_markers_clean_and_avoid(self):
        serial = SerialSink()
        bridge = FakeAutonomyBridge()
        client = create_app(serial, bridge, '/tmp').test_client()

        # Add a debris marker (should have identifier CLEAN)
        r_debris = client.post('/vision/markers', json={
            'label': 'solid_debris', 'action': 'clean', 'x': 1.2, 'y': 0.8, 'confidence': 0.92
        })
        self.assertEqual(r_debris.status_code, 201)
        self.assertEqual(r_debris.json['created']['identifier'], 'CLEAN')
        self.assertEqual(r_debris.json['created']['action'], 'clean')

        # Add an obstacle marker (should have identifier AVOID)
        r_obstacle = client.post('/vision/markers', json={
            'label': 'cable', 'action': 'avoid', 'x': 2.0, 'y': 1.5, 'confidence': 0.88
        })
        self.assertEqual(r_obstacle.status_code, 201)
        self.assertEqual(r_obstacle.json['created']['identifier'], 'AVOID')
        self.assertEqual(r_obstacle.json['created']['action'], 'avoid')

        # GET /vision/markers returns both markers
        snap = client.get('/vision/markers').json
        self.assertEqual(len(snap['markers']), 2)

        # DELETE one marker
        mid = r_debris.json['created']['id']
        del_res = client.delete(f'/vision/markers/{mid}')
        self.assertEqual(del_res.status_code, 200)
        snap2 = client.get('/vision/markers').json
        self.assertEqual(len(snap2['markers']), 1)
        self.assertEqual(snap2['markers'][0]['action'], 'avoid')

        # DELETE all markers
        client.delete('/vision/markers')
        snap3 = client.get('/vision/markers').json
        self.assertEqual(len(snap3['markers']), 0)

    def test_vision_marker_dismiss_as_false_positive(self):
        serial = SerialSink()
        bridge = FakeAutonomyBridge()
        client = create_app(serial, bridge, '/tmp').test_client()

        # Add a cable marker
        res = client.post('/vision/markers', json={
            'label': 'cable', 'action': 'avoid', 'x': 1.0, 'y': 2.0, 'confidence': 0.95
        })
        mid = res.json['created']['id']

        # Dismiss marker as false positive
        dismiss_res = client.post(f'/vision/markers/{mid}/dismiss')
        self.assertEqual(dismiss_res.status_code, 200)
        self.assertTrue(dismiss_res.json['dismissed'])
        self.assertEqual(dismiss_res.json['dismissed_count'], 1)

        # Check marker is gone
        snap = client.get('/vision/markers').json
        self.assertEqual(len(snap['markers']), 0)

        # Subsequent camera detection at same location is suppressed as false positive
        readd_res = client.post('/vision/markers', json={
            'label': 'cable', 'action': 'avoid', 'x': 1.05, 'y': 2.02, 'confidence': 0.90
        })
        self.assertIsNone(readd_res.json['created'])
        snap2 = client.get('/vision/markers').json
        self.assertEqual(len(snap2['markers']), 0)

        # Clear dismissed list
        clear_res = client.delete('/vision/markers/dismissed')
        self.assertEqual(clear_res.status_code, 200)
        self.assertEqual(clear_res.json['cleared_count'], 1)

        # Now re-adding succeeds
        readd_res2 = client.post('/vision/markers', json={
            'label': 'cable', 'action': 'avoid', 'x': 1.0, 'y': 2.0, 'confidence': 0.90
        })
        self.assertIsNotNone(readd_res2.json['created'])
        self.assertEqual(len(client.get('/vision/markers').json['markers']), 1)

    def test_vision_avoid_identifiers_toggle(self):
        serial = SerialSink()
        bridge = FakeAutonomyBridge()
        client = create_app(serial, bridge, '/tmp').test_client()

        # GET avoid identifiers
        cfg_res = client.get('/vision/avoid-identifiers')
        self.assertEqual(cfg_res.status_code, 200)
        identifiers = cfg_res.json['identifiers']
        self.assertIn('cable', identifiers)
        self.assertIn('shoe', identifiers)
        self.assertTrue(identifiers['cable']['enabled'])

        # Add cable and shoe markers
        client.post('/vision/markers', json={'label': 'cable', 'action': 'avoid', 'x': 1.0, 'y': 1.0})
        client.post('/vision/markers', json={'label': 'shoe', 'action': 'avoid', 'x': 2.0, 'y': 2.0})
        self.assertEqual(len(client.get('/vision/markers').json['markers']), 2)

        # Toggle cable avoidance OFF
        update_res = client.post('/vision/avoid-identifiers', json={'key': 'cable', 'enabled': False})
        self.assertEqual(update_res.status_code, 200)
        self.assertFalse(update_res.json['identifiers']['cable']['enabled'])

        # Existing cable marker was pruned, shoe remains
        markers = client.get('/vision/markers').json['markers']
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]['label'], 'shoe')

        # New cable detection is ignored
        add_cable = client.post('/vision/markers', json={'label': 'cable', 'action': 'avoid', 'x': 3.0, 'y': 3.0})
        self.assertIsNone(add_cable.json['created'])
        self.assertEqual(len(client.get('/vision/markers').json['markers']), 1)

        # Re-enable cable avoidance
        client.post('/vision/avoid-identifiers', json={'key': 'cable', 'enabled': True})
        add_cable2 = client.post('/vision/markers', json={'label': 'cable', 'action': 'avoid', 'x': 3.0, 'y': 3.0})
        self.assertIsNotNone(add_cable2.json['created'])
        self.assertEqual(len(client.get('/vision/markers').json['markers']), 2)


if __name__ == '__main__':
    unittest.main()

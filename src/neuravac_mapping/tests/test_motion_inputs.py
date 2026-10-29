import unittest
from neuravac_mapping.motion_inputs import motion_fault


def readings():
    return {'sensors': (10., bytes(26)), 'scan': (10., True), 'pose': (10., True),
            'odom': (10., True), 'status': (10., 'TRACKING')}


class InputTests(unittest.TestCase):
    def test_ready_only_with_all_fresh_inputs(self):
        self.assertIsNone(motion_fault(readings(), 10.1))
        for name in readings():
            data = readings()
            data.pop(name)
            self.assertIsNotNone(motion_fault(data, 10.1), name)
            data = readings()
            data[name] = (8., data[name][1])
            self.assertIsNotNone(motion_fault(data, 10.1), name)

    def test_bad_scan_tracking_or_contact_stop(self):
        for key, value in [('scan', False), ('pose', False), ('odom', False), ('status', 'LOST')]:
            data = readings()
            data[key] = (10., value)
            self.assertIsNotNone(motion_fault(data, 10.1))
        data = readings()
        data['sensors'] = (10., bytes([1] + [0]*25))
        self.assertEqual(motion_fault(data, 10.1), 'bumper')

class ScanTests(unittest.TestCase):
    def test_rejects_obstacle_and_sparse_or_invalid_scans(self):
        from neuravac_mapping.motion_inputs import scan_clear
        self.assertTrue(scan_clear([1.] * 360, .05, 10., .25))
        self.assertFalse(scan_clear([.24] + [1.]*359, .05, 10., .25))
        self.assertFalse(scan_clear([float('inf')]*360, .05, 10., .25))
        self.assertFalse(scan_clear([], .05, 10., .25))
        self.assertFalse(scan_clear([float('inf')]*90 + [1.]*270, .05, 10., .25))

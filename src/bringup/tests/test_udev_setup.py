"""Rule generation and device detection, with udev and /dev mocked out."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bringup import udev_setup as u

CH340_LIDAR = {
    'ID_VENDOR_ID': '1a86', 'ID_MODEL_ID': '7523', 'ID_SERIAL_SHORT': '',
    'ID_PATH': 'platform-xhci-hcd.1-usb-0:1.2:1.0',
}
CH340_ROOMBA = dict(CH340_LIDAR, ID_PATH='platform-xhci-hcd.1-usb-0:1.3:1.0')
FTDI_ROOMBA = {
    'ID_VENDOR_ID': '0403', 'ID_MODEL_ID': '6001', 'ID_SERIAL_SHORT': 'A50285BI',
    'ID_PATH': 'platform-xhci-hcd.1-usb-0:1.3:1.0',
}
WEBCAM = {
    'ID_VENDOR_ID': '046d', 'ID_MODEL_ID': '085c', 'ID_SERIAL_SHORT': '',
    'ID_PATH': 'platform-xhci-hcd.0-usb-0:2:1.0',
    'ID_V4L_CAPABILITIES': ':capture:',
}


class ChooseMethodTests(unittest.TestCase):
    def test_identical_adapters_without_serial_use_port(self):
        methods = u.choose_methods({'lidar': CH340_LIDAR, 'roomba': CH340_ROOMBA})
        self.assertEqual(methods, {'lidar': 'path', 'roomba': 'path'})

    def test_unique_serial_is_used(self):
        methods = u.choose_methods({'lidar': CH340_LIDAR, 'roomba': FTDI_ROOMBA})
        self.assertEqual(methods, {'lidar': 'path', 'roomba': 'serial'})

    def test_shared_generic_serial_falls_back_to_port(self):
        a = dict(FTDI_ROOMBA, ID_SERIAL_SHORT='0001')
        b = dict(FTDI_ROOMBA, ID_SERIAL_SHORT='0001',
                 ID_PATH='platform-xhci-hcd.1-usb-0:1.2:1.0')
        methods = u.choose_methods({'roomba': a, 'lidar': b})
        self.assertEqual(methods, {'roomba': 'path', 'lidar': 'path'})


class BuildRuleTests(unittest.TestCase):
    def test_serial_rule_by_port(self):
        rule = u.build_rule('lidar', 'serial', CH340_LIDAR, 'path')
        self.assertIn('SUBSYSTEM=="tty"', rule)
        self.assertIn('ENV{ID_PATH}=="platform-xhci-hcd.1-usb-0:1.2:1.0"', rule)
        self.assertIn('SYMLINK+="neuravac_lidar"', rule)
        self.assertIn('GROUP="dialout"', rule)
        self.assertNotIn('ID_SERIAL_SHORT', rule)

    def test_serial_rule_by_serial_number(self):
        rule = u.build_rule('roomba', 'serial', FTDI_ROOMBA, 'serial')
        self.assertIn('ENV{ID_VENDOR_ID}=="0403"', rule)
        self.assertIn('ENV{ID_SERIAL_SHORT}=="A50285BI"', rule)
        self.assertNotIn('ID_PATH', rule)

    def test_camera_rule_selects_capture_node_only(self):
        rule = u.build_rule('camera', 'video', WEBCAM, 'path')
        self.assertIn('SUBSYSTEM=="video4linux"', rule)
        self.assertIn('ATTR{index}=="0"', rule)
        self.assertIn('SYMLINK+="neuravac_camera"', rule)
        self.assertIn('GROUP="video"', rule)

    def test_missing_path_is_an_error(self):
        with self.assertRaises(ValueError):
            u.build_rule('lidar', 'serial', {'ID_VENDOR_ID': '1a86'}, 'path')

    def test_rules_file_has_one_rule_per_device(self):
        selected = {'lidar': CH340_LIDAR, 'roomba': FTDI_ROOMBA, 'camera': WEBCAM}
        text = u.build_rules(selected, u.choose_methods(selected))
        rules = [l for l in text.splitlines() if l and not l.startswith('#')]
        self.assertEqual(len(rules), 3)
        for name in selected:
            self.assertEqual(text.count(f'SYMLINK+="neuravac_{name}"'), 1)


class DetectTests(unittest.TestCase):
    def run_detect(self, name, kind, before, after, props):
        listings = iter([before, after])
        with mock.patch.object(u, 'list_nodes', side_effect=lambda k: next(listings)), \
                mock.patch.object(u, 'udev_properties', side_effect=lambda n: props[n]):
            return u.detect(name, kind, prompt=lambda _: '', sleep=lambda _: None)

    def test_finds_the_new_serial_node(self):
        props = {'/dev/ttyUSB1': CH340_LIDAR}
        found = self.run_detect('lidar', 'serial', {'/dev/ttyUSB0'},
                                {'/dev/ttyUSB0', '/dev/ttyUSB1'}, props)
        self.assertEqual(found, CH340_LIDAR)

    def test_no_new_device_is_reported(self):
        with self.assertRaises(RuntimeError):
            self.run_detect('lidar', 'serial', {'/dev/ttyUSB0'}, {'/dev/ttyUSB0'}, {})

    def test_two_new_serial_devices_are_ambiguous(self):
        props = {'/dev/ttyUSB0': CH340_LIDAR, '/dev/ttyUSB1': CH340_ROOMBA}
        with self.assertRaises(RuntimeError):
            self.run_detect('lidar', 'serial', set(), set(props), props)

    def test_webcam_picks_capture_node(self):
        meta = dict(WEBCAM, ID_V4L_CAPABILITIES=':')
        props = {'/dev/video0': WEBCAM, '/dev/video1': meta}
        found = self.run_detect('camera', 'video', set(), set(props), props)
        self.assertEqual(found, WEBCAM)


if __name__ == '__main__':
    unittest.main()

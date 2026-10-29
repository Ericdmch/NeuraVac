"""Exercise serial stop behavior using a fake driver and ROS message shims."""
import importlib
import sys
import threading
import types
import unittest
from unittest.mock import patch


def module(name, **members):
    obj = types.ModuleType(name)
    for key, value in members.items():
        setattr(obj, key, value)
    return obj


class String:
    def __init__(self, data=''):
        self.data = data


class FakeSerial:
    is_open = True
    def __init__(self):
        self.writes = []
    def write(self, data):
        self.writes.append(bytes(data))


class Driver:
    def __init__(self):
        self.serial = FakeSerial()
        self._serial_lock = threading.RLock()
        self._sensor_condition = threading.Condition()
        self._latest_group_zero_at = 10.
        self._latest_group_zero = bytes(26)
    def create_publisher(self, *args):
        return types.SimpleNamespace(publish=lambda msg: None)
    def create_subscription(self, *args):
        return object()
    def create_service(self, *args):
        return object()
    def create_timer(self, *args):
        return object()


class DriverWatchdogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        msg_types = {'PoseStamped': object, 'Twist': object, 'Odometry': object,
                     'LaserScan': object, 'String': String}
        modules = {}
        for package in ('geometry_msgs', 'nav_msgs', 'sensor_msgs', 'std_msgs'):
            modules[package] = module(package)
            modules[package + '.msg'] = module(package + '.msg', **msg_types)
        modules['std_srvs'] = module('std_srvs')
        modules['std_srvs.srv'] = module('std_srvs.srv', Trigger=object)
        modules['rclpy'] = module('rclpy')
        modules['rclpy.qos'] = module('rclpy.qos', qos_profile_sensor_data=object())
        cls.module_patch = patch.dict(sys.modules, modules)
        cls.module_patch.start()
        cls.lib = importlib.import_module('neuravac_mapping.driver_watchdog')

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop('neuravac_mapping.driver_watchdog', None)
        cls.module_patch.stop()

    def setUp(self):
        self.driver = Driver()
        self.guard = self.lib.DriverWatchdog(self.driver)
        self.guard.inputs = {'scan': (10., True), 'pose': (10., True),
                             'odom': (10., True), 'status': (10., 'TRACKING')}
        self.guard.guard.arm(10.)

    def test_arm_reenters_safe_mode_and_stops_before_accepting_motion(self):
        self.guard.guard.preempt('not armed')
        with patch.object(self.lib.time, 'monotonic', return_value=10.1):
            response = self.guard.arm(None, types.SimpleNamespace())
        self.assertTrue(response.success)
        self.assertEqual(self.driver.serial.writes[-2:], [bytes([131]), bytes([145, 0, 0, 0, 0])])

    def test_timeout_sends_zero_and_latches(self):
        with patch.object(self.lib.time, 'monotonic', return_value=10.31):
            self.guard.tick()
        self.assertEqual(self.driver.serial.writes[-1], bytes([145, 0, 0, 0, 0]))
        self.assertFalse(self.guard.guard.armed)

    def test_bumper_sends_zero_without_waiting_for_next_command(self):
        self.driver._latest_group_zero = bytes([1] + [0] * 25)
        with patch.object(self.lib.time, 'monotonic', return_value=10.1):
            self.guard.tick()
        self.assertEqual(self.driver.serial.writes[-1], bytes([145, 0, 0, 0, 0]))
        self.assertEqual(self.guard.guard.reason, 'bumper')

    def test_timed_out_command_still_sends_zero(self):
        msg = types.SimpleNamespace(linear=types.SimpleNamespace(x=.05, y=0., z=0.),
                                    angular=types.SimpleNamespace(x=0., y=0., z=0.))
        with patch.object(self.lib.time, 'monotonic', return_value=10.31):
            self.guard.on_velocity(msg)
        self.assertEqual(self.driver.serial.writes[-1], bytes([145, 0, 0, 0, 0]))
        self.assertFalse(self.guard.guard.armed)

    def test_serial_failure_is_reported_and_remains_latched(self):
        with patch.object(self.driver.serial, 'write', side_effect=OSError('disconnected')):
            response = self.guard.disarm(None, types.SimpleNamespace())
        self.assertFalse(response.success)
        self.assertFalse(self.guard.guard.armed)
        self.assertIn('serial', self.guard.guard.reason)

    def test_disarm_does_not_erase_latched_fault(self):
        self.guard.stop('bumper')
        self.guard.disarm(None, types.SimpleNamespace())
        self.assertEqual(self.guard.guard.reason, 'bumper')

    def test_manual_command_preempts_and_stops(self):
        self.guard.manual_preempt()
        self.assertEqual(self.driver.serial.writes[-1], bytes([145, 0, 0, 0, 0]))
        self.assertFalse(self.guard.guard.armed)

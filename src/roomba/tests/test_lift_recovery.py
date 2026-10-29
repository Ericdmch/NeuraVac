import time
import unittest
from unittest.mock import patch
import rclpy
from roomba.roomba_node import Roomba
from roomba_interfaces.msg import SerialData
from test_encoder_odometry import FakeSerial

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        rclpy.init()
        self.port = FakeSerial()
        with patch('roomba.roomba_node.serial.Serial', return_value=self.port), patch('roomba.roomba_node.time.sleep'):
            self.node = Roomba()
        self.port.writes.clear()
        self.drive = SerialData(data=[137,0,100,128,0])
    def tearDown(self):
        self.node.destroy_node()
        rclpy.try_shutdown()
    def test_drive_rearms_safe_only_after_clear_fresh_feedback(self):
        self.node._latest_group_zero = bytes(26)
        self.node._latest_group_zero_at = time.monotonic()
        self.node.write_serial(self.drive)
        self.assertEqual(self.port.writes, [bytes([131]),bytes(self.drive.data)])
    def test_lift_cliff_and_stale_block_nonzero_drive(self):
        for index, flag in [(0,4),(2,1)]:
            sensor = bytearray(26); sensor[index] = flag
            self.node._latest_group_zero = sensor
            self.node._latest_group_zero_at = time.monotonic()
            self.node.write_serial(self.drive)
        self.node._latest_group_zero = bytes(26)
        self.node._latest_group_zero_at = time.monotonic()-5
        self.node.write_serial(self.drive)
        self.assertEqual(self.port.writes, [])
    def test_stop_passes_even_with_no_sensor_feedback(self):
        self.node.write_serial(SerialData(data=[137,0,0,128,0]))
        self.assertEqual(self.port.writes, [bytes([137,0,0,128,0])])

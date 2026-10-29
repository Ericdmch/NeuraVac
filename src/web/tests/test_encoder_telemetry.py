"""Keep encoder response bytes out of the dashboard group-zero decoder."""
from collections import deque
import threading
import time
import unittest

from roomba_interfaces.msg import SerialData
from web.telemetry import SensorState
from web.web_node import SerialBridge


class EncoderTelemetryTests(unittest.TestCase):
    def test_raw_query_reply_is_logged_but_only_extracted_telemetry_is_decoded(self):
        bridge = object.__new__(SerialBridge)
        bridge.sensors = SensorState()
        bridge._rx_lock = threading.Lock()
        bridge._rx_sequence = 0
        bridge._rx_log = deque()
        observed = bytes.fromhex('000000000000000000000000000000000439d6ff8b2205a90a889bf8b45b')
        bridge.receive_serial(SerialData(data=list(observed)))
        self.assertFalse(bridge.sensors.snapshot(time.monotonic())['online'])
        self.assertEqual(len(bytes.fromhex(bridge._rx_log[0]['text'])), 30)
        bridge.receive_telemetry(SerialData(data=list(observed[:26])))
        snapshot = bridge.sensors.snapshot(time.monotonic())
        self.assertTrue(snapshot['online'])
        self.assertEqual(snapshot['values']['capacity_mah'], 2696)

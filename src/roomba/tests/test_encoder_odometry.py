"""Exercise encoder arithmetic and complete, serialized Query List exchanges."""
import math
import threading
import unittest
from unittest.mock import Mock, patch

import rclpy
from roomba_interfaces.srv import RequestTelemetry
from roomba.encoder_odometry import EncoderOdometry, QUERY, counter_delta, decode_reply
from roomba.roomba_node import Roomba


def reply(left=100, right=100):
    return bytes(26) + left.to_bytes(2, 'big') + right.to_bytes(2, 'big')


class EncoderTests(unittest.TestCase):
    def test_signed_and_unsigned_wrap_in_both_directions(self):
        self.assertEqual(counter_delta(5, 65530), 11)
        self.assertEqual(counter_delta(65530, 5), -11)
        self.assertEqual(counter_delta(32768, 32767), 1)
        self.assertEqual(counter_delta(32767, 32768), -1)

    def test_first_sample_is_only_a_baseline(self):
        odom = EncoderOdometry()
        self.assertIsNone(odom.update(39928, 46171, 1))
        self.assertEqual((odom.x, odom.y, odom.yaw), (0, 0, 0))

    def test_forward_and_reverse_are_signed(self):
        for sign in (1, -1):
            odom = EncoderOdometry()
            odom.update(1000, 1000, 0)
            x, y, yaw, velocity, angular = odom.update(1000 + sign * 100, 1000 + sign * 100, 1)
            self.assertAlmostEqual(x, sign * 100 * math.pi * .072 / 508.8)
            self.assertAlmostEqual(y, 0)
            self.assertAlmostEqual(yaw, 0)
            self.assertEqual(math.copysign(1, velocity), sign)

    def test_in_place_turn_uses_wheel_track(self):
        odom = EncoderOdometry()
        odom.update(1000, 1000, 0)
        x, y, yaw, _, _ = odom.update(900, 1100, 1)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 0)
        self.assertAlmostEqual(yaw, 200 * odom.meters_per_count / .235)

    def test_implausible_jump_does_not_move_pose_and_rebaselines(self):
        odom = EncoderOdometry()
        odom.update(100, 100, 0)
        self.assertIsNone(odom.update(20000, 20000, .1))
        self.assertTrue(odom.rejected)
        self.assertEqual(odom.x, 0)
        self.assertIsNotNone(odom.update(20002, 20002, .2))
        self.assertAlmostEqual(odom.x, 2 * odom.meters_per_count)

    def test_reply_contract_preserves_telemetry_and_encoder_order(self):
        telemetry, left, right = decode_reply(reply(39928, 46171))
        self.assertEqual(len(telemetry), 26)
        self.assertEqual((left, right), (39928, 46171))
        for length in (4, 26, 29, 31):
            with self.assertRaises(ValueError):
                decode_reply(bytes(length))

    def test_actual_stationary_roomba_650_reply(self):
        observed = bytes.fromhex('000000000000000000000000000000000439d6ff8b2205a90a889bf8b45b')
        telemetry, left, right = decode_reply(observed)
        self.assertEqual((left, right), (39928, 46171))
        self.assertEqual(int.from_bytes(telemetry[24:26], 'big'), 2696)


class FakeSerial:
    def __init__(self):
        self.buffer = bytearray()
        self.writes = []
        self.is_open = True

    @property
    def in_waiting(self):
        return len(self.buffer)

    def write(self, data):
        self.writes.append(bytes(data))

    def read(self, size):
        data = bytes(self.buffer[:size])
        del self.buffer[:size]
        return data

    def reset_input_buffer(self):
        self.buffer.clear()

    def close(self):
        self.is_open = False


class QueryTransactionTests(unittest.TestCase):
    def setUp(self):
        rclpy.init()
        self.port = FakeSerial()
        with patch('roomba.roomba_node.serial.Serial', return_value=self.port):
            with patch('roomba.roomba_node.time.sleep'):
                self.node = Roomba()
        self.node.sensors_pub = Mock()
        self.node.encoder_pub = Mock()
        self.node.odom_pub = Mock()

    def tearDown(self):
        self.node.destroy_node()
        rclpy.try_shutdown()

    def test_fragmented_reply_is_published_only_after_all_30_bytes(self):
        self.node.request_group_zero()
        self.node.request_group_zero()
        self.assertEqual(self.port.writes.count(QUERY), 1)
        self.port.buffer.extend(reply()[:13])
        self.node.read_serial()
        self.node.sensors_pub.publish.assert_not_called()
        self.port.buffer.extend(reply()[13:])
        self.node.read_serial()
        self.assertEqual(self.node._sensor_sequence, 1)
        self.assertEqual(len(self.node.sensors_pub.publish.call_args.args[0].data), 26)
        self.assertEqual(list(self.node.encoder_pub.publish.call_args.args[0].data), [100, 100])

    def test_service_joins_existing_transaction(self):
        self.node.request_group_zero()
        entered = threading.Event()
        request = self.node.request_group_zero

        def joined():
            result = request()
            entered.set()
            return result

        self.node.request_group_zero = joined
        responses = []
        thread = threading.Thread(target=lambda: responses.append(
            self.node.request_telemetry(None, RequestTelemetry.Response())))
        thread.start()
        self.assertTrue(entered.wait(1))
        self.port.buffer.extend(reply())
        self.node.read_serial()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(self.port.writes.count(QUERY), 1)
        self.assertTrue(responses[0].accepted)
        self.assertEqual(len(responses[0].data), 26)

    def test_timeout_drains_late_bytes_before_retry(self):
        with patch('roomba.roomba_node.time.monotonic', return_value=10):
            self.node.request_group_zero()
        with patch('roomba.roomba_node.time.monotonic', return_value=11):
            self.node.request_group_zero()
        self.assertFalse(self.node._query_pending)
        self.port.buffer.extend(reply())
        self.node.read_serial()
        self.node.sensors_pub.publish.assert_not_called()
        with patch('roomba.roomba_node.time.monotonic', return_value=11.3):
            self.node.request_group_zero()
        self.assertEqual(self.port.writes.count(QUERY), 2)


if __name__ == '__main__':
    unittest.main()

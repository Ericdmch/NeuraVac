"""Roomba serial class against a fake port. No robot, no ROS."""
import os
import threading
import time
import types
from unittest import mock

import pytest
import serial

from neuravac_robot import roomba as roomba_module
from neuravac_robot.roomba import Roomba, split16, twist_to_wheels

OI_REPLY = bytes(80)    # an all-zero group-100 packet


class FakeSerial:
    """Stands in for pyserial. Answers the sensor request with an 80-byte reply."""

    def __init__(self, port, baud, **kwargs):
        self.kwargs = kwargs
        self.timeout = kwargs.get('timeout')
        self.is_open = True
        self.writes = []
        self.flushes = 0
        self.rx = bytearray()
        self.silent = False
        self.dead = False

    def write(self, data):
        if self.dead:
            raise serial.SerialException('device disconnected')
        self.writes.append(bytes(data))
        if bytes(data) == bytes([142, 100]) and not self.silent:
            self.rx.extend(OI_REPLY)
        return len(data)

    def flush(self):
        self.flushes += 1

    def reset_input_buffer(self):
        self.rx.clear()

    def read(self, size):
        if not self.rx:
            time.sleep(self.timeout or 0)    # like pyserial: wait, then return nothing
            return b''
        chunk = bytes(self.rx[:size])
        del self.rx[:size]
        return chunk

    def close(self):
        self.is_open = False


@pytest.fixture
def robot():
    with mock.patch.object(roomba_module.serial, 'Serial', FakeSerial), \
            mock.patch.object(roomba_module, 'time', types.SimpleNamespace(sleep=lambda s: None)):
        r = Roomba('FAKE', 115200)
        r.connect()
        yield r


def test_split16_handles_negative_and_sentinel_values():
    assert split16(300) == [1, 44]
    assert split16(-100) == [0xFF, 0x9C]
    assert split16(0x8000) == [0x80, 0x00]


@pytest.mark.skipif(os.name != 'posix', reason='exclusive locking is POSIX-only')
def test_port_opens_exclusive_with_timeouts(robot):
    assert robot.ser.kwargs['exclusive'] is True
    assert robot.ser.kwargs['write_timeout'] == 1.0


def test_writes_are_flushed(robot):
    robot._write([128])
    assert robot.ser.writes[-1] == bytes([128])
    assert robot.ser.flushes == 1


def test_start_sequence_safe_and_full(robot):
    robot.start(safe_mode=True)
    assert robot.ser.writes == [bytes([128]), bytes([150, 0]), bytes([131])]
    robot.ser.writes.clear()
    robot.start(safe_mode=False)
    assert robot.ser.writes[-1] == bytes([132])


def test_drive_direct_packet_and_clamping(robot):
    robot.drive_direct(100, -100)
    assert robot.ser.writes[-1] == bytes([145, 0x00, 0x64, 0xFF, 0x9C])
    robot.drive_direct(900, -900)    # clamped to the +/-500 mm/s limit
    assert robot.ser.writes[-1] == bytes([145, 0x01, 0xF4, 0xFE, 0x0C])


def test_read_sensors_requests_group_100_and_decodes(robot):
    result = robot.read_sensors()
    assert robot.ser.writes[-1] == bytes([142, 100])
    assert result['distance_mm'] == 0
    assert result['oi_mode_name'] == 'off'


def test_read_sensors_ignores_stale_bytes(robot):
    robot.ser.rx.extend(b'\xaa' * 7)    # leftover bytes from an old reply
    result = robot.read_sensors()
    # Stale bytes would be decoded as the first fields of the packet.
    assert result['bumps_wheeldrops_raw'] == 0
    assert result['cliff_left'] == 0
    assert not robot.ser.rx


def test_missing_reply_raises_timeout_and_port_stays_open(robot):
    robot.ser.silent = True
    with pytest.raises(TimeoutError):
        robot.read_sensors(timeout=0.05)
    assert robot.is_open


def test_stop_command_is_not_blocked_by_a_stalled_read(robot):
    robot.ser.silent = True    # the robot never answers, so the reader keeps waiting
    reader = threading.Thread(
        target=lambda: pytest.raises(TimeoutError, robot.read_sensors, timeout=0.5))
    reader.start()
    time.sleep(0.1)            # the reader is now waiting inside read_exact
    assert reader.is_alive()   # proof it really is stalled, not finished
    started = time.monotonic()
    robot.drive_direct(0, 0)
    assert time.monotonic() - started < 0.2
    assert robot.ser.writes[-1] == bytes([145, 0, 0, 0, 0])
    reader.join()


def test_unplugged_device_raises_oserror(robot):
    robot.ser.dead = True
    with pytest.raises(OSError):
        robot.drive_direct(0, 0)


def test_not_open_raises_connection_error():
    r = Roomba('FAKE')
    assert not r.is_open
    with pytest.raises(ConnectionError):
        r.drive_direct(0, 0)
    with pytest.raises(ConnectionError):
        r.read_sensors()


def test_stop_halts_wheels_then_closes(robot):
    port = robot.ser
    robot.stop()
    assert port.writes[-2:] == [bytes([145, 0, 0, 0, 0]), bytes([128])]
    assert not port.is_open
    assert not robot.is_open
    robot.stop()    # a second stop on a closed port must not raise


def test_stop_survives_a_dead_port(robot):
    robot.ser.dead = True
    robot.stop()
    assert not robot.is_open


def test_twist_straight_and_reverse():
    assert twist_to_wheels(0.2, 0.0, 0.235) == (200, 200)
    assert twist_to_wheels(-0.1, 0.0, 0.235) == (-100, -100)


def test_twist_counter_clockwise_spin_speeds_up_the_right_wheel():
    right, left = twist_to_wheels(0.0, 2.0, 0.235)
    assert (right, left) == (235, -235)


def test_twist_arc_left_has_faster_right_wheel():
    right, left = twist_to_wheels(0.2, 1.0, 0.235)
    assert right > left
    assert (right + left) / 2 == pytest.approx(200, abs=1)


def test_twist_over_limit_scales_both_wheels_together():
    right, left = twist_to_wheels(0.5, 2.0, 0.235, max_speed=0.5)
    assert right == 500
    assert left == pytest.approx(180, abs=1)    # 0.265 * (0.5 / 0.735) m/s

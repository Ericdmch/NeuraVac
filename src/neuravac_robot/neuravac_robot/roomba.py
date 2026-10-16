"""The Roomba's serial port: opcodes in, sensor packets out. Plain Python, no ROS.

This object is the single owner of the serial port. Two threads may use it at
once (one reads sensors, one sends drive commands), so every write is guarded
by a lock. Reads are only ever done by one caller at a time.
"""
import os
import struct
import threading
import time

import serial

from neuravac_robot import sensors

OP_START = 128         # open the interface, robot enters passive mode
OP_SAFE = 131          # safe mode: cliff and wheel-drop sensors stop the wheels
OP_FULL = 132          # full mode: NO cliff or wheel-drop protection
OP_SENSORS = 142       # request one sensor packet (or packet group)
OP_STREAM_PAUSE = 150  # pause/resume a sensor stream left over from before
OP_DRIVE_DIRECT = 145  # set the right and left wheel speeds in mm/s

MAX_WHEEL_MM_S = 500   # the Open Interface limit


def split16(value):
    """Return [high_byte, low_byte] of a signed 16-bit value."""
    return [(value >> 8) & 0xFF, value & 0xFF]


def twist_to_wheels(linear, angular, wheel_base, max_speed=0.5):
    """Convert a velocity command to (right, left) wheel speeds in mm/s.

    linear is m/s forward, angular is rad/s counter-clockwise, wheel_base is the
    distance between the wheels in metres. If either wheel would exceed
    max_speed (m/s), both are scaled down together so the turn radius is kept.
    """
    right = linear + angular * wheel_base / 2.0
    left = linear - angular * wheel_base / 2.0
    fastest = max(abs(right), abs(left))
    if fastest > max_speed:
        scale = max_speed / fastest
        right *= scale
        left *= scale
    return round(right * 1000), round(left * 1000)


class Roomba:
    """Owns the serial connection to one Roomba (Open Interface, 600 series)."""

    def __init__(self, port, baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self._write_lock = threading.Lock()
        group, fields = sensors.packet_layout('oi')
        self._request = bytes([OP_SENSORS, group])
        self._reply_size = struct.calcsize('>' + ''.join(kind for _, kind in fields))

    @property
    def is_open(self):
        return bool(self.ser and self.ser.is_open)

    def connect(self):
        """Open the port. Raises OSError (SerialException) if that fails."""
        # exclusive=True makes a second program fail instead of silently sharing
        # the port. It only exists on Linux/macOS; Windows already refuses.
        extra = {'exclusive': True} if os.name == 'posix' else {}
        self.ser = serial.Serial(
            self.port, self.baud, timeout=0.2, write_timeout=1.0, **extra)

    def start(self, safe_mode=True):
        """Wake the interface and choose safe or full mode."""
        self._write([OP_START])
        time.sleep(0.2)
        self._write([OP_STREAM_PAUSE, 0])   # stop any stream left from a past run
        time.sleep(0.05)
        self.ser.reset_input_buffer()        # drop stale bytes before the first read
        self._write([OP_SAFE if safe_mode else OP_FULL])
        time.sleep(0.2)

    def drive_direct(self, right_mm_s, left_mm_s):
        """Set both wheel speeds in mm/s (positive is forward)."""
        right = max(-MAX_WHEEL_MM_S, min(MAX_WHEEL_MM_S, int(right_mm_s)))
        left = max(-MAX_WHEEL_MM_S, min(MAX_WHEEL_MM_S, int(left_mm_s)))
        self._write([OP_DRIVE_DIRECT] + split16(right) + split16(left))

    def read_sensors(self, timeout=0.1):
        """Request one packet and return it decoded. Raises TimeoutError if no reply."""
        ser = self._require_open()
        ser.reset_input_buffer()    # never decode leftover bytes as this reply
        self._write(self._request)
        payload = sensors.read_exact(ser, self._reply_size, timeout)
        return sensors.decode_sensors(payload, 'oi')

    def stop(self):
        """Stop the wheels, return to passive mode, and close the port."""
        if self.is_open:
            try:
                self.drive_direct(0, 0)
                self._write([OP_START])
            except OSError:
                pass    # the port is going away anyway
        self.close()

    def close(self):
        try:
            if self.ser:
                self.ser.close()
        except OSError:
            pass
        self.ser = None

    def _require_open(self):
        ser = self.ser
        if not (ser and ser.is_open):
            raise ConnectionError('serial port is not open')
        return ser

    def _write(self, data):
        ser = self._require_open()
        with self._write_lock:
            ser.write(bytes(data))
            ser.flush()

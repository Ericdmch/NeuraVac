"""Decode standard Roomba OI group 0 replies, retaining receipt freshness."""

import threading


CHARGING_STATES = (
    'Not charging', 'Reconditioning', 'Charging', 'Trickle charging',
    'Waiting', 'Charging fault',
)


def decode_group_zero(packet):
    if len(packet) != 26:
        raise ValueError('Group 0 must contain exactly 26 bytes')
    if any(value not in (0, 1) for value in packet[1:7]) or packet[16] > 5:
        raise ValueError('Invalid sensor flags or charging state')

    def word(offset, signed=False):
        return int.from_bytes(packet[offset:offset + 2], 'big', signed=signed)

    charge, capacity = word(22), word(24)
    flags = packet[0]
    return {
        'bump_right': bool(flags & 1),
        'bump_left': bool(flags & 2),
        'wheel_drop_right': bool(flags & 4),
        'wheel_drop_left': bool(flags & 8),
        'wall': bool(packet[1]),
        'cliff_left': bool(packet[2]),
        'cliff_front_left': bool(packet[3]),
        'cliff_front_right': bool(packet[4]),
        'cliff_right': bool(packet[5]),
        'virtual_wall': bool(packet[6]),
        'overcurrent': bool(packet[7]),
        'distance_mm': word(12, signed=True),
        'angle_deg': word(14, signed=True),
        'charging_state': CHARGING_STATES[packet[16]],
        'voltage_v': word(17) / 1000,
        'current_ma': word(19, signed=True),
        'temperature_c': int.from_bytes(packet[21:22], 'big', signed=True),
        'charge_mah': charge,
        'capacity_mah': capacity,
        'battery_percent': round(min(100, 100 * charge / capacity), 1) if capacity else None,
    }


class SensorState:
    RESPONSE_TIMEOUT = 0.4
    MAX_AGE = 15.0

    def __init__(self):
        self._lock = threading.Lock()
        self._pending = None
        self._buffer = bytearray()
        self._values = None
        self._updated = None
        self._version = 0
        self._condition = threading.Condition(self._lock)

    def request(self, now):
        with self._lock:
            if self._pending is not None and now - self._pending < self.RESPONSE_TIMEOUT:
                return False
            self._buffer.clear()
            self._pending = now
            return True

    def receive(self, data, now):
        with self._lock:
            if self._pending is None:
                return
            if now - self._pending > self.RESPONSE_TIMEOUT:
                self._pending = None
                self._buffer.clear()
                return
            self._buffer.extend(data)
            while len(self._buffer) >= 26:
                packet = bytes(self._buffer[:26])
                try:
                    values = decode_group_zero(packet)
                except ValueError:
                    del self._buffer[0]
                    continue
                del self._buffer[:26]
                self._pending = None
                self._values = values
                self._updated = now
                self._version += 1
                self._condition.notify_all()

    def version(self):
        with self._lock:
            return self._version

    def wait_for_update(self, after_version, timeout):
        with self._condition:
            return self._condition.wait_for(
                lambda: self._version > after_version,
                timeout=timeout,
            )

    def cancel_request(self):
        with self._lock:
            self._pending = None
            self._buffer.clear()

    def snapshot(self, now):
        with self._lock:
            age = None if self._updated is None else max(0, now - self._updated)
            online = age is not None and age <= self.MAX_AGE
            return {
                'online': online,
                'age_seconds': round(age, 2) if age is not None else None,
                'values': dict(self._values) if online else None,
            }

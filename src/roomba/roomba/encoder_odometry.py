"""Differential-drive odometry from Roomba OI encoder packets 43 and 44."""
import math

QUERY = bytes((149, 3, 0, 43, 44))
REPLY_BYTES = 30


def decode_reply(reply):
    """Return group-zero telemetry and unsigned encoder bit patterns."""
    if len(reply) != REPLY_BYTES:
        raise ValueError('Query List response must contain exactly 30 bytes')
    telemetry = bytes(reply[:26])
    if any(v not in (0, 1) for v in telemetry[1:7]) or telemetry[16] > 5:
        raise ValueError('Invalid group-zero fields in Query List response')
    return telemetry, int.from_bytes(reply[26:28], 'big'), int.from_bytes(reply[28:30], 'big')


def counter_delta(current, previous):
    """Signed modular difference, including both signed/unsigned rollovers."""
    return ((current - previous + 32768) % 65536) - 32768


class EncoderOdometry:
    def __init__(self, diameter=0.072, counts_per_rev=508.8, track=0.235,
                 left_scale=1.0, right_scale=1.0, max_speed=0.6):
        if min(diameter, counts_per_rev, track, left_scale, right_scale, max_speed) <= 0:
            raise ValueError('Encoder geometry and calibration values must be positive')
        self.meters_per_count = math.pi * diameter / counts_per_rev
        self.track = track
        self.left_scale = left_scale
        self.right_scale = right_scale
        self.max_speed = max_speed
        self.previous = None
        self.stamp = None
        self.x = self.y = self.yaw = 0.0
        self.rejected = False

    def update(self, left, right, stamp):
        self.rejected = False
        previous, previous_stamp = self.previous, self.stamp
        self.previous, self.stamp = (left, right), stamp
        if previous is None:
            return None
        dt = stamp - previous_stamp
        dl = counter_delta(left, previous[0]) * self.meters_per_count * self.left_scale
        dr = counter_delta(right, previous[1]) * self.meters_per_count * self.right_scale
        if dt <= 0 or dt > 2.0 or max(abs(dl), abs(dr)) > self.max_speed * dt + 0.01:
            # Rebaseline a reset/corrupt counter instead of jumping the map.
            self.rejected = True
            return None
        distance = (dl + dr) / 2.0
        turn = (dr - dl) / self.track
        if abs(turn) < 1e-9:
            local_x, local_y = distance, 0.0
        else:
            local_x = distance * math.sin(turn) / turn
            local_y = distance * (1.0 - math.cos(turn)) / turn
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        self.x += c * local_x - s * local_y
        self.y += s * local_x + c * local_y
        self.yaw = math.atan2(math.sin(self.yaw + turn), math.cos(self.yaw + turn))
        return self.x, self.y, self.yaw, distance / dt, turn / dt

"""Measurement-order scan reconstruction and SE(2) wheel-pose interpolation."""
from collections import deque
import bisect
import math


class PoseHistory:
    def __init__(self, max_gap=.25):
        self.samples = deque(maxlen=400)
        self.max_gap = max_gap

    def add(self, stamp, pose):
        if self.samples and stamp <= self.samples[-1][0]:
            self.samples.clear()
        self.samples.append((stamp, tuple(pose)))

    def at(self, stamp):
        if not self.samples or stamp < self.samples[0][0] or stamp > self.samples[-1][0]:
            return None
        times = [s[0] for s in self.samples]
        i = bisect.bisect_left(times, stamp)
        if times[i] == stamp:
            return self.samples[i][1]
        start, end = self.samples[i - 1], self.samples[i]
        if end[0] - start[0] > self.max_gap:
            return None
        f = (stamp - start[0]) / (end[0] - start[0])
        a, b = start[1], end[1]
        turn = math.atan2(math.sin(b[2] - a[2]), math.cos(b[2] - a[2]))
        return (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]), a[2] + f * turn)


class ScanAssembler:
    """Clockwise revolution bins; timing estimated from consecutive seams.

    D6 protocol has no hardware timestamp. Receipt seam times approximate
    acquisition times; serial latency remains an uncertainty to calibrate.
    """
    def __init__(self, bins=720):
        self.bins = bins
        self.last_angle = None
        self.start = None
        self.start_angle = 0.
        self.ranges = [float('inf')] * bins
        self.count = 0

    def add(self, angle_deg, distance_mm, stamp):
        angle = angle_deg % 360
        result = None
        seam = self.last_angle is not None and self.last_angle > 300 and angle < 60
        if seam:
            if self.start is not None:
                phase = 1. + (angle - self.start_angle) / 360.
                duration = (stamp - self.start) / phase
                if .04 <= duration <= .5 and self.count >= 30:
                    result = dict(stamp=self.start - self.start_angle / 360. * duration, duration=duration,
                                  angle_increment=-2 * math.pi / self.bins,
                                  ranges=self.ranges)
            self.start = stamp
            self.start_angle = angle
            self.ranges = [float('inf')] * self.bins
            self.count = 0
        elif self.last_angle is not None and angle < self.last_angle - 2:
            self.start = None
            self.count = 0
        self.last_angle = angle
        if self.start is not None:
            index = min(self.bins - 1, int(angle * self.bins / 360))
            value = distance_mm / 1000
            if value > 0 and math.isfinite(value):
                self.ranges[index] = min(self.ranges[index], value)
            self.count += 1
        return result


def sensor_pose(base, mount):
    c, s = math.cos(base[2]), math.sin(base[2])
    return (base[0] + c * mount[0] - s * mount[1],
            base[1] + s * mount[0] + c * mount[1], base[2] + mount[2])


def deskew_ranges(ranges, angle_min, angle_increment, stamp, time_increment,
                  reference_stamp, history, bins=720, mount=(0, 0, 0),
                  min_range=.12, max_range=8.):
    reference = history.at(reference_stamp)
    if reference is None:
        return None
    reference = sensor_pose(reference, mount)
    c, s = math.cos(reference[2]), math.sin(reference[2])
    output = [float('inf')] * bins
    for i, distance in enumerate(ranges):
        if not math.isfinite(distance) or not min_range <= distance <= max_range:
            continue
        pose = history.at(stamp + i * time_increment)
        if pose is None:
            return None
        pose = sensor_pose(pose, mount)
        angle = pose[2] + angle_min + i * angle_increment
        wx = pose[0] + distance * math.cos(angle) - reference[0]
        wy = pose[1] + distance * math.sin(angle) - reference[1]
        x, y = c * wx + s * wy, -s * wx + c * wy
        index = round((math.atan2(y, x) + math.pi) * bins / (2 * math.pi)) % bins
        corrected = math.hypot(x, y)
        if min_range <= corrected <= max_range:
            output[index] = min(output[index], corrected)
    return output

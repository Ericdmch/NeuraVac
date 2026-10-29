"""Reject brief, large scan changes while successive wheel poses are similar."""
import math
import statistics


class ScanStability:
    def __init__(self):
        self.reference = None
        self.candidate = None
        self.held = 0

    @staticmethod
    def compare(a, b):
        ranges_a, pose_a, stamp_a = a
        ranges_b, pose_b, stamp_b = b
        turn = abs(math.atan2(math.sin(pose_b[2] - pose_a[2]),
                              math.cos(pose_b[2] - pose_a[2])))
        if (stamp_b - stamp_a > .6 or stamp_b < stamp_a or
                math.hypot(pose_b[0] - pose_a[0], pose_b[1] - pose_a[1]) > .05 or
                turn > math.radians(3)):
            return None
        count_a = sum(math.isfinite(x) for x in ranges_a)
        count_b = sum(math.isfinite(x) for x in ranges_b)
        if count_a >= 60 and count_b < count_a * .4:
            return False
        pairs = [(x, y) for x, y in zip(ranges_a, ranges_b)
                 if math.isfinite(x) and math.isfinite(y)]
        if len(pairs) < 30:
            return None
        # Both absolute and relative disagreement are needed to ignore noise
        # on nearby surfaces and normal range noise on far ones.
        errors = [abs(x-y) / max(.3, min(x,y)) for x,y in pairs if abs(x-y) > .20]
        return len(errors) <= len(pairs) * .5 or statistics.median(errors) <= .15

    def accept(self, ranges, pose, stamp):
        current = (tuple(ranges), tuple(pose), stamp)
        if self.reference is None:
            self.reference = current
            return True
        match = self.compare(self.reference, current)
        if match is not False:
            self.reference, self.candidate = current, None
            return True
        if self.candidate is not None and self.compare(self.candidate, current) is True:
            self.reference, self.candidate = current, None
            return True
        self.candidate = current
        self.held += 1
        return False

"""Calibrate a display arrow from commanded straight travel in map coordinates."""
import math


class TravelHeading:
    def __init__(self):
        self.direction = 0
        self.anchor = None
        self.offset = 0.0
        self.latest_pose = None

    def command(self, data):
        if len(data) != 5 or data[0] != 137:
            return
        velocity = int.from_bytes(bytes(data[1:3]), 'big', signed=True)
        radius = int.from_bytes(bytes(data[3:5]), 'big')
        direction = (1 if velocity > 0 else -1) if velocity and radius in (32768, 32767) else 0
        if direction != self.direction:
            self.anchor = self.latest_pose if direction else None
        self.direction = direction

    def update(self, x, y, yaw, now):
        self.latest_pose = (x, y, yaw, now)
        if self.direction:
            if self.anchor is not None:
                ax, ay, ayaw, stamp = self.anchor
                distance = math.hypot(x - ax, y - ay)
                turn = abs(math.atan2(math.sin(yaw - ayaw), math.cos(yaw - ayaw)))
                elapsed = now - stamp
                if distance > 0.5 or turn > math.radians(5) or elapsed > 2:
                    self.anchor = None
                elif distance >= 0.02 and elapsed > 0:
                    forward = math.atan2(y - ay, x - ax)
                    if self.direction < 0:
                        forward += math.pi
                    self.offset = math.atan2(math.sin(forward - yaw), math.cos(forward - yaw))
                    self.anchor = None
            if self.anchor is None:
                self.anchor = (x, y, yaw, now)
        result = yaw + self.offset
        return math.atan2(math.sin(result), math.cos(result))

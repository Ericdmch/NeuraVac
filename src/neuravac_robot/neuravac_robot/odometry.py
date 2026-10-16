"""Dead-reckoning odometry for the Roomba. Plain Python, no ROS.

The Roomba reports how far it moved (mm) and how much it turned (degrees)
*since the previous sensor request*. Adding those small steps up gives a pose.
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Pose:
    """Where the robot is, relative to where it started."""

    x: float = 0.0    # metres, forward from the start
    y: float = 0.0    # metres, left of the start
    yaw: float = 0.0  # radians, counter-clockwise is positive (ROS convention)


def wrap_angle(angle):
    """Wrap an angle in radians to the range [-pi, pi)."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def yaw_to_quaternion(yaw):
    """Return (x, y, z, w) for a rotation of `yaw` radians about the Z axis."""
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


class Odometry:
    """Accumulates the Roomba's distance/angle deltas into a pose."""

    def __init__(self):
        self.pose = Pose()

    def reset(self):
        self.pose = Pose()

    def update(self, distance_mm, angle_deg):
        """Add one step: `distance_mm` forward and `angle_deg` turned (CCW positive).

        The step is taken along the heading halfway through the turn, which is
        more accurate than the heading at the start of the step.
        """
        distance = distance_mm / 1000.0
        dyaw = math.radians(angle_deg)
        mid_yaw = self.pose.yaw + 0.5 * dyaw
        self.pose = Pose(
            x=self.pose.x + distance * math.cos(mid_yaw),
            y=self.pose.y + distance * math.sin(mid_yaw),
            yaw=wrap_angle(self.pose.yaw + dyaw),
        )
        return self.pose

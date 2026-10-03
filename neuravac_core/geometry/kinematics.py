import math

from neuravac_core.models import Pose


def wrap_angle(angle: float) -> float:
    return (angle + math.pi) % (2 * math.pi) - math.pi


def integrate(pose: Pose, linear: float, angular: float, dt: float) -> Pose:
    if not all(math.isfinite(v) for v in (linear, angular, dt)) or dt < 0:
        raise ValueError("finite velocity and nonnegative timestep required")
    turn = angular * dt
    if abs(angular) < 1e-9:
        dx, dy = linear * dt * math.cos(pose.yaw), linear * dt * math.sin(pose.yaw)
    else:
        dx = linear / angular * (math.sin(pose.yaw + turn) - math.sin(pose.yaw))
        dy = linear / angular * (math.cos(pose.yaw) - math.cos(pose.yaw + turn))
    return Pose(x=pose.x + dx, y=pose.y + dy, yaw=wrap_angle(pose.yaw + turn))


def encoder_delta(current: int, previous: int) -> int:
    return (current - previous + 32768) % 65536 - 32768


def encoder_odometry(pose: Pose, left_m: float, right_m: float, wheel_base: float) -> Pose:
    return integrate(pose, (left_m + right_m) / 2, (right_m - left_m) / wheel_base, 1)

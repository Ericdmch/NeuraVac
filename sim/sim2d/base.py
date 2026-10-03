import math

from neuravac_core.base.mock import MockRobotBase
from neuravac_core.config import RobotConfig
from neuravac_core.geometry.kinematics import integrate
from neuravac_core.models import BumperState
from sim.sim2d.environment import Environment


class SimRobotBase(MockRobotBase):
    def __init__(self, environment: Environment, config: RobotConfig) -> None:
        super().__init__()
        self.environment = environment
        self.config = config
        self.pose = environment.start.model_copy()
        self.time = 0.0
        self.trajectory = [(self.pose.x, self.pose.y)]
        self._ticks = [0.0, 0.0]

    def step(self, dt: float) -> None:
        if not self.connected:
            return
        linear, angular = self.velocity
        # Substeps prevent tunnelling through thin obstacles.
        count = max(1, math.ceil(abs(linear) * dt / 0.02))
        for _ in range(count):
            next_pose = integrate(self.pose, linear, angular, dt / count)
            if not self.environment.free(next_pose.x, next_pose.y, self.config.robot_radius_m):
                self.bumper = BumperState(left=True, right=True)
                self.velocity = (0, 0)
                self.vacuum = self.main_brush = self.side_brush = False
                break
            self.pose = next_pose
            for index, sign in enumerate((-1, 1)):
                distance = (linear + sign * angular * self.config.wheel_base_m / 2) * dt / count
                self._ticks[index] += (
                    distance
                    / (2 * math.pi * self.config.wheel_radius_m)
                    * self.config.encoder_ticks_per_rev
                )
            if self.vacuum:
                self.environment.clean(self.pose, self.config.cleaning.vacuum_radius_m, dt / count)
        self.time += dt
        self.encoders.left, self.encoders.right = (int(x) % 65536 for x in self._ticks)
        self.battery.percent = max(0, self.battery.percent - dt * 0.001)
        if (
            math.hypot(self.pose.x - self.trajectory[-1][0], self.pose.y - self.trajectory[-1][1])
            > 0.02
        ):
            self.trajectory.append((self.pose.x, self.pose.y))

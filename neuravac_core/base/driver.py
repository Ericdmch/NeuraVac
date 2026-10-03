"""Backend-independent actuator boundary and encoder odometry."""

import math

from neuravac_core.base.interface import RobotBase
from neuravac_core.config import RobotConfig
from neuravac_core.geometry.kinematics import encoder_delta, encoder_odometry
from neuravac_core.models import EncoderState, Pose
from neuravac_core.safety import SensorSnapshot, VelocityCommand


class BaseDriver:
    def __init__(self, base: RobotBase, config: RobotConfig) -> None:
        self.base = base
        self.config = config
        self.pose = Pose()
        self.last_command: float | None = None
        self.previous_encoders: EncoderState | None = None
        self.connected = False
        self.diagnostics = {
            "connected": False,
            "odometry_supported": False,
            "watchdog_expired": True,
        }

    async def connect(self) -> None:
        await self.base.connect()
        await self.base.stop()
        self.connected = True
        self.diagnostics["connected"] = True

    async def apply(self, command: VelocityCommand, now: float) -> None:
        if not 0 <= now - command.timestamp <= self.config.safety.watchdog_s:
            await self.base.stop()
            return
        if (
            abs(command.linear_mps) > self.config.safety.max_linear_mps
            or abs(command.angular_rps) > self.config.safety.max_angular_rps
        ):
            await self.base.stop()
            raise ValueError("arbiter command exceeds driver limits")
        try:
            await self.base.set_velocity(command.linear_mps, command.angular_rps)
            await self.base.set_vacuum(command.vacuum)
            await self.base.set_main_brush(command.main_brush)
            await self.base.set_side_brush(command.side_brush)
        except Exception:
            self.connected = False
            self.diagnostics["connected"] = False
            await self.base.stop()
            raise
        self.last_command = now
        self.diagnostics["watchdog_expired"] = False

    async def watchdog(self, now: float) -> None:
        if (
            self.last_command is None
            or not 0 <= now - self.last_command <= self.config.safety.watchdog_s
        ):
            await self.base.stop()
            self.diagnostics["watchdog_expired"] = True

    async def poll(self, now: float) -> SensorSnapshot:
        try:
            battery = await self.base.get_battery_state()
            bumper = await self.base.get_bumper_state()
            cliff = await self.base.get_cliff_state()
            encoders = await self.base.get_encoder_state()
        except Exception:
            self.connected = False
            self.diagnostics["connected"] = False
            await self.base.stop()
            raise
        self.diagnostics["odometry_supported"] = encoders.supported
        if encoders.supported and self.previous_encoders:
            metres_per_tick = (
                2 * math.pi * self.config.wheel_radius_m / self.config.encoder_ticks_per_rev
            )
            left = encoder_delta(encoders.left, self.previous_encoders.left) * metres_per_tick
            right = encoder_delta(encoders.right, self.previous_encoders.right) * metres_per_tick
            self.pose = encoder_odometry(self.pose, left, right, self.config.wheel_base_m)
        self.previous_encoders = encoders
        return SensorSnapshot(
            base_timestamp=now,
            connected=self.connected,
            battery=battery,
            bumper=bumper,
            cliff=cliff,
        )

    async def stop(self) -> None:
        self.last_command = None
        await self.base.stop()

    async def close(self) -> None:
        try:
            await self.stop()
        finally:
            await self.base.disconnect()
            self.connected = False

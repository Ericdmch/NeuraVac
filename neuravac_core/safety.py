"""Local fail-closed safety. Only the arbiter produces actuator commands."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import Field

from neuravac_core.config import SafetyConfig
from neuravac_core.models import BatteryState, BumperState, CliffState, StrictModel


@dataclass
class SensorSnapshot:
    base_timestamp: float | None = None
    scan_timestamp: float | None = None
    camera_timestamp: float | None = None
    heartbeat_timestamp: float | None = None
    connected: bool = True
    battery: BatteryState = field(default_factory=BatteryState)
    bumper: BumperState = field(default_factory=BumperState)
    cliff: CliffState = field(default_factory=CliffState)


class SafetyStatus(StrictModel):
    safe: bool = False
    reasons: list[str] = Field(default_factory=list)
    latched: bool = False


class SafetyMonitor:
    def __init__(self, config: SafetyConfig) -> None:
        self.config = config
        self.latched = False

    def emergency_stop(self) -> None:
        self.latched = True

    def evaluate(self, sensors: SensorSnapshot, now: float) -> SafetyStatus:
        reasons = []
        if self.latched:
            reasons.append("emergency_stop")
        if not sensors.connected:
            reasons.append("base_disconnected")
        for name, stamp, limit in (
            ("base", sensors.base_timestamp, self.config.sensor_timeout_s),
            ("lidar", sensors.scan_timestamp, self.config.sensor_timeout_s),
            ("heartbeat", sensors.heartbeat_timestamp, self.config.watchdog_s),
            ("camera", sensors.camera_timestamp, self.config.camera_timeout_s),
        ):
            if name == "camera" and not self.config.require_camera:
                continue
            if stamp is None or not 0 <= now - stamp <= limit:
                reasons.append(f"{name}_stale")
        if sensors.bumper.left or sensors.bumper.right:
            reasons.append("bumper")
        if sensors.bumper.wheel_drop:
            reasons.append("wheel_drop")
        if sensors.cliff.detected:
            reasons.append("cliff")
        if sensors.battery.percent <= self.config.critical_battery_percent:
            reasons.append("critical_battery")
        if abs(sensors.battery.current) >= self.config.max_current_a:
            reasons.append("motor_current")
        return SafetyStatus(safe=not reasons, reasons=reasons, latched=self.latched)

    def reset(self, sensors: SensorSnapshot, now: float) -> bool:
        was_latched = self.latched
        self.latched = False
        if not self.evaluate(sensors, now).safe:
            self.latched = was_latched
            return False
        return True


class VelocityCommand(StrictModel):
    source: Literal["emergency", "safety", "manual", "navigation", "idle"]
    linear_mps: float = 0.0
    angular_rps: float = 0.0
    timestamp: float = Field(ge=0)
    vacuum: bool = False
    main_brush: bool = False
    side_brush: bool = False


class CommandArbiter:
    PRIORITY = ("emergency", "safety", "manual", "navigation", "idle")

    def __init__(self, config: SafetyConfig) -> None:
        self.config = config
        self.commands: dict[str, VelocityCommand] = {}

    def submit(self, command: VelocityCommand) -> None:
        self.commands[command.source] = command

    def clear(self) -> None:
        self.commands.clear()

    def select(self, now: float, status: SafetyStatus) -> VelocityCommand:
        stopped = VelocityCommand(source="safety", timestamp=now)
        if not status.safe:
            return stopped
        for source in self.PRIORITY:
            command = self.commands.get(source)
            if command is None:
                continue
            if not 0 <= now - command.timestamp <= self.config.watchdog_s:
                continue
            if source in ("safety", "emergency"):
                return stopped
            selected = command.model_copy()
            selected.linear_mps = max(
                -self.config.max_linear_mps, min(self.config.max_linear_mps, command.linear_mps)
            )
            selected.angular_rps = max(
                -self.config.max_angular_rps, min(self.config.max_angular_rps, command.angular_rps)
            )
            return selected
        return VelocityCommand(source="idle", timestamp=now)

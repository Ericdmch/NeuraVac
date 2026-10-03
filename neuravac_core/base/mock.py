"""In-memory backend with real lifecycle and a latched emergency stop."""

import math
from collections import deque

from neuravac_core.base.interface import RobotBase
from neuravac_core.models import BatteryState, BumperState, CliffState, EncoderState


class MockRobotBase(RobotBase):
    def __init__(self) -> None:
        self.connected = False
        self.estopped = False
        self.velocity = (0.0, 0.0)
        self.vacuum = self.main_brush = self.side_brush = False
        self.battery = BatteryState()
        self.bumper = BumperState()
        self.cliff = CliffState()
        self.encoders = EncoderState()
        self.commands: deque[tuple[str, object]] = deque(maxlen=512)

    def _ready(self, enabled: bool = False) -> None:
        if not self.connected:
            raise ConnectionError("base disconnected")
        if enabled and self.estopped:
            raise RuntimeError("emergency stop latched")

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        await self.stop()
        self.connected = False

    async def set_velocity(self, linear_mps: float, angular_rps: float) -> None:
        self._ready(bool(linear_mps or angular_rps))
        if not all(math.isfinite(x) for x in (linear_mps, angular_rps)):
            raise ValueError("velocity must be finite")
        self.velocity = (linear_mps, angular_rps)
        self.commands.append(("velocity", self.velocity))

    async def stop(self) -> None:
        self.velocity = (0, 0)
        self.vacuum = self.main_brush = self.side_brush = False
        self.commands.append(("stop", None))

    async def set_vacuum(self, enabled: bool) -> None:
        self._ready(enabled)
        self.vacuum = enabled
        self.commands.append(("vacuum", enabled))

    async def set_main_brush(self, enabled: bool) -> None:
        self._ready(enabled)
        self.main_brush = enabled

    async def set_side_brush(self, enabled: bool) -> None:
        self._ready(enabled)
        self.side_brush = enabled

    async def get_battery_state(self) -> BatteryState:
        self._ready()
        return self.battery.model_copy()

    async def get_bumper_state(self) -> BumperState:
        self._ready()
        return self.bumper.model_copy()

    async def get_cliff_state(self) -> CliffState:
        self._ready()
        return self.cliff.model_copy()

    async def get_encoder_state(self) -> EncoderState:
        self._ready()
        return self.encoders.model_copy()

    async def emergency_stop(self) -> None:
        self.estopped = True
        await self.stop()

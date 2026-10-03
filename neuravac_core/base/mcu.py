"""Versioned serial JSON bridge; an MCU must implement documented watchdog contract."""

import asyncio
import json
from collections.abc import Callable
from typing import Any

from neuravac_core.base.mock import MockRobotBase
from neuravac_core.config import RobotConfig
from neuravac_core.models import BatteryState, BumperState, CliffState, EncoderState, StrictModel


class BridgeResponse(StrictModel):
    version: int
    seq: int
    ok: bool
    result: dict


class McuBridgeBase(MockRobotBase):
    def __init__(
        self, config: RobotConfig, serial_factory: Callable[..., Any] | None = None
    ) -> None:
        super().__init__()
        self.config = config
        self.factory = serial_factory
        self.serial: Any = None
        self.seq = 0
        self._lock = asyncio.Lock()

    async def request(self, op: str, **params: Any) -> dict:
        async with self._lock:
            self.seq += 1
            data = (
                json.dumps(
                    {"version": 1, "seq": self.seq, "op": op, "params": params}, allow_nan=False
                ).encode()
                + b"\n"
            )

            def transaction() -> dict:
                if self.serial.write(data) != len(data):
                    raise OSError("partial MCU write")
                response = BridgeResponse.model_validate_json(self.serial.readline(4096))
                if response.version != 1 or response.seq != self.seq or not response.ok:
                    raise ValueError("MCU rejected request or sequence/version mismatch")
                return response.result

            try:
                return await asyncio.to_thread(transaction)
            except (OSError, ValueError) as error:
                self.connected = False
                raise ConnectionError("MCU communication lost") from error

    async def connect(self) -> None:
        if self.factory is None:
            try:
                import serial
            except ImportError as error:
                raise RuntimeError("install neuravac[hardware]") from error
            self.factory = serial.Serial
        self.serial = await asyncio.to_thread(
            self.factory,
            port=self.config.serial_port,
            baudrate=self.config.baud_rate,
            timeout=self.config.safety.sensor_timeout_s / 2,
            write_timeout=0.1,
        )
        try:
            hello = await self.request(
                "hello", watchdog_ms=round(self.config.safety.watchdog_s * 1000)
            )
            if (
                hello.get("version") != 1
                or not 0 < hello.get("watchdog_ms", 0) <= self.config.safety.watchdog_s * 1000
            ):
                raise ValueError("MCU firmware must enforce requested actuator watchdog")
            self.connected = True
            await self.stop()
        except Exception:
            await asyncio.to_thread(self.serial.close)
            self.serial = None
            raise

    async def set_velocity(self, linear_mps: float, angular_rps: float) -> None:
        await super().set_velocity(linear_mps, angular_rps)
        if (
            abs(linear_mps) > self.config.safety.max_linear_mps
            or abs(angular_rps) > self.config.safety.max_angular_rps
        ):
            await self.stop()
            raise ValueError("MCU velocity exceeds configured limits")
        await self.request("velocity", linear_mps=linear_mps, angular_rps=angular_rps)

    async def _motors(self) -> None:
        await self.request(
            "motors", vacuum=self.vacuum, main_brush=self.main_brush, side_brush=self.side_brush
        )

    async def set_vacuum(self, enabled: bool) -> None:
        await super().set_vacuum(enabled)
        await self._motors()

    async def set_main_brush(self, enabled: bool) -> None:
        await super().set_main_brush(enabled)
        await self._motors()

    async def set_side_brush(self, enabled: bool) -> None:
        await super().set_side_brush(enabled)
        await self._motors()

    async def stop(self) -> None:
        await super().stop()
        if self.serial and self.connected:
            await self.request("stop")

    async def disconnect(self) -> None:
        try:
            await self.stop()
        finally:
            if self.serial:
                await asyncio.to_thread(self.serial.close)
            self.serial = None
            self.connected = False

    async def poll(self) -> None:
        self._ready()
        sensors = await self.request("sensors")
        self.battery = BatteryState.model_validate(sensors["battery"])
        self.bumper = BumperState.model_validate(sensors["bumper"])
        self.cliff = CliffState.model_validate(sensors["cliff"])
        self.encoders = EncoderState.model_validate(sensors["encoders"])

    async def get_battery_state(self):
        await self.poll()
        return await super().get_battery_state()

    async def get_bumper_state(self):
        await self.poll()
        return await super().get_bumper_state()

    async def get_cliff_state(self):
        await self.poll()
        return await super().get_cliff_state()

    async def get_encoder_state(self):
        await self.poll()
        return await super().get_encoder_state()

"""OI safe-mode backend, bounded serial transactions, independent command expiry."""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from neuravac_core.base.mock import MockRobotBase
from neuravac_core.base.protocol import (
    DEFAULT_PACKETS,
    decode_sensors,
    drive_direct,
    motors,
    query_list,
    response_size,
)
from neuravac_core.config import RobotConfig

logger = logging.getLogger(__name__)


class RoombaOIBase(MockRobotBase):
    def __init__(
        self, config: RobotConfig, serial_factory: Callable[..., Any] | None = None
    ) -> None:
        super().__init__()
        self.config = config
        self.serial_factory = serial_factory
        self.serial: Any = None
        self._lock = asyncio.Lock()
        self._watchdog: asyncio.Task[None] | None = None
        self._last_command = 0.0
        self._last_poll = -1.0

    async def connect(self) -> None:
        if self.connected:
            return
        if self.serial_factory is None:
            try:
                import serial
            except ImportError as error:
                raise RuntimeError("install neuravac[hardware] for serial support") from error
            self.serial_factory = serial.Serial
        self.serial = await asyncio.to_thread(
            self.serial_factory,
            port=self.config.serial_port,
            baudrate=self.config.baud_rate,
            timeout=0.1,
            write_timeout=0.1,
        )
        self.connected = True
        try:
            await self._write(bytes([128]))
            await self._write(bytes([131]))
            await self.stop()
            self._last_command = time.monotonic()
            self._watchdog = asyncio.create_task(self._watch())
        except Exception:
            await self.disconnect()
            raise

    async def _write(self, data: bytes) -> None:
        async with self._lock:
            try:
                written = await asyncio.to_thread(self.serial.write, data)
                if written != len(data):
                    raise OSError("partial serial write")
            except OSError as error:
                self.connected = False
                raise ConnectionError("OI communication lost") from error

    async def _watch(self) -> None:
        while self.connected:
            await asyncio.sleep(self.config.safety.watchdog_s / 4)
            if time.monotonic() - self._last_command > self.config.safety.watchdog_s:
                try:
                    await self.stop()
                except ConnectionError:
                    logger.error("base_watchdog_communication_lost")
                    return

    async def set_velocity(self, linear_mps: float, angular_rps: float) -> None:
        self._ready(bool(linear_mps or angular_rps))
        # Validation is shared with the mock; commands never exceed configured limits.
        await super().set_velocity(linear_mps, angular_rps)
        if (
            abs(linear_mps) > self.config.safety.max_linear_mps
            or abs(angular_rps) > self.config.safety.max_angular_rps
        ):
            await self.stop()
            raise ValueError("velocity exceeds configured safety limit")
        right = round(1000 * (linear_mps + angular_rps * self.config.wheel_base_m / 2))
        left = round(1000 * (linear_mps - angular_rps * self.config.wheel_base_m / 2))
        scale = max(1, abs(right) / 500, abs(left) / 500)
        await self._write(drive_direct(round(right / scale), round(left / scale)))
        self._last_command = time.monotonic()

    async def _motor_command(self) -> None:
        await self._write(motors(self.vacuum, self.main_brush, self.side_brush))

    async def set_vacuum(self, enabled: bool) -> None:
        await super().set_vacuum(enabled)
        await self._motor_command()

    async def set_main_brush(self, enabled: bool) -> None:
        await super().set_main_brush(enabled)
        await self._motor_command()

    async def set_side_brush(self, enabled: bool) -> None:
        await super().set_side_brush(enabled)
        await self._motor_command()

    async def stop(self) -> None:
        await super().stop()
        if self.serial:
            failures = []
            for payload in (drive_direct(0, 0), motors(False, False, False)):
                try:
                    await self._write(payload)
                except ConnectionError as error:
                    failures.append(error)
            if failures:
                logger.error("base_stop_write_failed")
                raise failures[0]

    async def disconnect(self) -> None:
        if self._watchdog:
            self._watchdog.cancel()
            try:
                await self._watchdog
            except asyncio.CancelledError:
                pass
            self._watchdog = None
        try:
            await self.stop()
        except ConnectionError:
            logger.error("base_disconnect_stop_unconfirmed")
        finally:
            if self.serial:
                await asyncio.to_thread(self.serial.close)
                self.serial = None
            self.connected = False

    async def poll(self) -> None:
        self._ready()
        packets = DEFAULT_PACKETS if self.config.encoder_supported else DEFAULT_PACKETS[:-2]
        async with self._lock:

            def transaction() -> bytes:
                request = query_list(packets)
                if self.serial.write(request) != len(request):
                    raise OSError("partial query write")
                size = response_size(packets)
                buffer = bytearray()
                deadline = time.monotonic() + self.config.safety.sensor_timeout_s / 2
                while len(buffer) < size and time.monotonic() < deadline:
                    part = self.serial.read(size - len(buffer))
                    if not part:
                        raise OSError("sensor response timeout")
                    buffer.extend(part)
                if len(buffer) != size:
                    raise OSError("truncated response")
                return bytes(buffer)

            try:
                data = decode_sensors(packets, await asyncio.to_thread(transaction))
            except (OSError, ValueError) as error:
                self.connected = False
                raise ConnectionError("OI sensor transaction failed") from error
        self.battery, self.bumper, self.cliff, self.encoders = (
            data.battery,
            data.bumper,
            data.cliff,
            data.encoders,
        )
        self._last_poll = time.monotonic()

    async def _fresh(self) -> None:
        if time.monotonic() - self._last_poll > 0.05:
            await self.poll()

    async def get_battery_state(self):
        await self._fresh()
        return await super().get_battery_state()

    async def get_bumper_state(self):
        await self._fresh()
        return await super().get_bumper_state()

    async def get_cliff_state(self):
        await self._fresh()
        return await super().get_cliff_state()

    async def get_encoder_state(self):
        await self._fresh()
        return await super().get_encoder_state()

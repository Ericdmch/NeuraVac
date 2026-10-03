"""Opt-in physical tests; movement additionally requires wheels elevated."""

import os

import pytest

from neuravac_core.base.roomba import RoombaOIBase
from neuravac_core.config import RobotConfig

pytestmark = pytest.mark.hardware


def configuration():
    port = os.environ.get("NEURAVAC_SERIAL_PORT")
    if not port:
        pytest.skip("Set NEURAVAC_SERIAL_PORT to the verified donor port")
    return RobotConfig(backend="roomba_oi", serial_port=port)


async def test_physical_connect_sensors_and_stop():
    base = RoombaOIBase(configuration())
    try:
        await base.connect()
        assert (await base.get_battery_state()).voltage > 0
        assert (await base.get_encoder_state()).supported
        await base.get_bumper_state()
        await base.get_cliff_state()
        await base.stop()
    finally:
        await base.disconnect()


async def test_elevated_wheels_and_cleaning_motors():
    if os.getenv("NEURAVAC_WHEELS_ELEVATED") != "1":
        pytest.skip("Explicitly confirm wheels elevated with NEURAVAC_WHEELS_ELEVATED=1")
    import asyncio

    base = RoombaOIBase(configuration())
    try:
        await base.connect()
        await base.set_velocity(0.05, 0)
        await asyncio.sleep(0.1)
        await base.stop()
        await base.set_vacuum(True)
        await asyncio.sleep(0.1)
        await base.stop()
    finally:
        await base.disconnect()

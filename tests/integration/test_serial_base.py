import struct

import pytest

from neuravac_core.base.roomba import RoombaOIBase
from neuravac_core.config import RobotConfig


class FakeSerial:
    def __init__(self):
        self.writes = []
        self.pending = b""
        self.closed = False
        self.lost = False

    def write(self, data):
        if self.lost:
            raise OSError("disconnected")
        self.writes.append(data)
        if data[0] == 149:
            self.pending = b"\x00" * 6 + struct.pack(">HhHHHH", 14400, -100, 1800, 2000, 10, 10)
        return len(data)

    def read(self, n):
        part, self.pending = self.pending[: min(n, 3)], self.pending[min(n, 3) :]
        return part

    def close(self):
        self.closed = True


async def test_fake_serial_partial_reads_sensor_decode_and_stop():
    serial = FakeSerial()
    base = RoombaOIBase(RobotConfig(backend="roomba_oi"), serial_factory=lambda **kwargs: serial)
    await base.connect()
    assert serial.writes[:2] == [b"\x80", b"\x83"]
    assert (await base.get_battery_state()).percent == 90
    await base.set_velocity(0.1, 0)
    assert b"\x91\x00\x64\x00\x64" in serial.writes
    await base.set_vacuum(True)
    await base.disconnect()
    assert b"\x91\x00\x00\x00\x00" in serial.writes
    assert b"\x8a\x00" in serial.writes and serial.closed


async def test_serial_disconnect_surfaces_fault_and_closes():
    serial = FakeSerial()
    base = RoombaOIBase(RobotConfig(backend="roomba_oi"), serial_factory=lambda **kwargs: serial)
    await base.connect()
    serial.lost = True
    with pytest.raises(ConnectionError):
        await base.set_velocity(0.1, 0)
    assert not base.connected
    await base.disconnect()
    assert serial.closed


async def test_sensor_timeout_still_writes_drive_and_motor_stop():
    from neuravac_core.base.driver import BaseDriver
    from neuravac_core.safety import VelocityCommand

    serial = FakeSerial()
    base = RoombaOIBase(RobotConfig(backend="roomba_oi"), serial_factory=lambda **kw: serial)
    driver = BaseDriver(base, base.config)
    await driver.connect()
    await driver.apply(
        VelocityCommand(source="navigation", linear_mps=0.1, vacuum=True, timestamp=1), 1
    )
    serial.read = lambda n: b""
    count = len(serial.writes)
    with pytest.raises(ConnectionError):
        await driver.poll(1.1)
    assert b"\x91\x00\x00\x00\x00" in serial.writes[count:]
    assert b"\x8a\x00" in serial.writes[count:]
    await driver.close()

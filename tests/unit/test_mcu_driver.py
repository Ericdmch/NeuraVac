import json

from neuravac_core.base.driver import BaseDriver
from neuravac_core.base.mcu import McuBridgeBase
from neuravac_core.base.mock import MockRobotBase
from neuravac_core.config import RobotConfig
from neuravac_core.safety import VelocityCommand


class FakeMcu:
    def __init__(self):
        self.pending = b""
        self.closed = False

    def write(self, data):
        request = json.loads(data)
        result = (
            {"version": 1, "watchdog_ms": 500}
            if request["op"] == "hello"
            else {
                "battery": {"percent": 80},
                "bumper": {},
                "cliff": {},
                "encoders": {"left": 2, "right": 2},
            }
        )
        self.pending = (
            json.dumps({"version": 1, "seq": request["seq"], "ok": True, "result": result}).encode()
            + b"\n"
        )
        return len(data)

    def readline(self, size=4096):
        result, self.pending = self.pending, b""
        return result

    def close(self):
        self.closed = True


async def test_mcu_handshake_sensors_and_shutdown():
    serial = FakeMcu()
    base = McuBridgeBase(RobotConfig(backend="mcu_bridge"), serial_factory=lambda **kw: serial)
    await base.connect()
    await base.set_velocity(0.1, 0)
    assert (await base.get_battery_state()).percent == 80
    await base.emergency_stop()
    assert base.velocity == (0, 0)
    await base.disconnect()
    assert serial.closed


async def test_driver_independent_watchdog_and_odometry():
    base = MockRobotBase()
    driver = BaseDriver(base, RobotConfig())
    await driver.connect()
    await driver.apply(VelocityCommand(source="navigation", linear_mps=0.2, timestamp=1), 1)
    assert base.velocity == (0.2, 0)
    await driver.watchdog(1.6)
    assert base.velocity == (0, 0)
    base.encoders.left = 100
    base.encoders.right = 100
    await driver.poll(2)
    base.encoders.left = 200
    base.encoders.right = 200
    await driver.poll(3)
    assert driver.pose.x > 0
    await driver.close()

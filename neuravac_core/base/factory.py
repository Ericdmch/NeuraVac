from neuravac_core.base.interface import RobotBase
from neuravac_core.base.mcu import McuBridgeBase
from neuravac_core.base.mock import MockRobotBase
from neuravac_core.base.roomba import RoombaOIBase
from neuravac_core.config import RobotConfig


def create_base(config: RobotConfig) -> RobotBase:
    if config.backend == "mock":
        return MockRobotBase()
    if config.backend == "roomba_oi":
        return RoombaOIBase(config)
    if config.backend == "mcu_bridge":
        return McuBridgeBase(config)
    from sim.sim2d.base import SimRobotBase
    from sim.sim2d.environment import Environment

    return SimRobotBase(Environment.demo(), config)

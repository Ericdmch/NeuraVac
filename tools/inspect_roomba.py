"""Explicit read-only donor inspection; never issues nonzero wheel speeds."""

import argparse
import asyncio
import json

from neuravac_core.base.roomba import RoombaOIBase
from neuravac_core.config import RobotConfig


async def inspect(port: str, baud: int, encoders: bool) -> None:
    base = RoombaOIBase(
        RobotConfig(
            backend="roomba_oi", serial_port=port, baud_rate=baud, encoder_supported=encoders
        )
    )
    try:
        await base.connect()
        print(
            json.dumps(
                {
                    "battery": (await base.get_battery_state()).model_dump(),
                    "bumper": (await base.get_bumper_state()).model_dump(),
                    "cliff": (await base.get_cliff_state()).model_dump(),
                    "encoders": (await base.get_encoder_state()).model_dump(),
                },
                indent=2,
            )
        )
    finally:
        await base.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--no-encoders", action="store_true")
    args = parser.parse_args()
    asyncio.run(inspect(args.port, args.baud, not args.no_encoders))

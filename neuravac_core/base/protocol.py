"""iRobot OI codecs; Drive Direct wheel order is RIGHT then LEFT (mm/s)."""

import struct
from dataclasses import dataclass

from neuravac_core.models import BatteryState, BumperState, CliffState, EncoderState

PACKET_FORMATS = {
    7: "B",
    9: "B",
    10: "B",
    11: "B",
    12: "B",
    19: "h",
    20: "h",
    21: "B",
    22: "H",
    23: "h",
    24: "b",
    25: "H",
    26: "H",
    43: "H",
    44: "H",
}
DEFAULT_PACKETS = [7, 9, 10, 11, 12, 21, 22, 23, 25, 26, 43, 44]


def drive_direct(right_mm_s: int, left_mm_s: int) -> bytes:
    if not all(isinstance(x, int) and -500 <= x <= 500 for x in (right_mm_s, left_mm_s)):
        raise ValueError("Drive Direct requires integer speeds within ±500 mm/s")
    return bytes([145]) + struct.pack(">hh", right_mm_s, left_mm_s)


def motors(vacuum: bool, main_brush: bool, side_brush: bool) -> bytes:
    return bytes([138, int(side_brush) | (int(vacuum) << 1) | (int(main_brush) << 2)])


def query_list(packets: list[int]) -> bytes:
    if not packets or len(packets) > 255 or any(p not in PACKET_FORMATS for p in packets):
        raise ValueError("unsupported sensor packet list")
    return bytes([149, len(packets), *packets])


def response_size(packets: list[int]) -> int:
    query_list(packets)
    return sum(struct.calcsize(">" + PACKET_FORMATS[p]) for p in packets)


@dataclass
class SensorData:
    battery: BatteryState
    bumper: BumperState
    cliff: CliffState
    encoders: EncoderState


def decode_sensors(packets: list[int], data: bytes) -> SensorData:
    if len(data) != response_size(packets):
        raise ValueError("sensor response length mismatch")
    offset = 0
    decoded = {}
    for packet in packets:
        fmt = ">" + PACKET_FORMATS[packet]
        decoded[packet] = struct.unpack_from(fmt, data, offset)[0]
        offset += struct.calcsize(fmt)
    bumps = decoded.get(7, 0)
    capacity = decoded.get(26, 0)
    return SensorData(
        BatteryState(
            percent=min(100, 100 * decoded.get(25, 0) / capacity) if capacity else 0,
            voltage=decoded.get(22, 0) / 1000,
            current=decoded.get(23, 0) / 1000,
            charging=decoded.get(21, 0) in (1, 2, 3, 4),
        ),
        BumperState(left=bool(bumps & 2), right=bool(bumps & 1), wheel_drop=bool(bumps & 0x1C)),
        CliffState(
            left=bool(decoded.get(9, 0)),
            front_left=bool(decoded.get(10, 0)),
            front_right=bool(decoded.get(11, 0)),
            right=bool(decoded.get(12, 0)),
        ),
        EncoderState(
            left=decoded.get(43, 0),
            right=decoded.get(44, 0),
            supported=43 in decoded and 44 in decoded,
        ),
    )

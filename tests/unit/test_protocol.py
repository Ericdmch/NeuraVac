import struct

import pytest

from neuravac_core.base.protocol import decode_sensors, drive_direct, motors, query_list


def test_known_signed_drive_direct_and_motor_bytes():
    assert drive_direct(200, -200) == b"\x91\x00\xc8\xff\x38"
    assert drive_direct(-500, 500) == b"\x91\xfe\x0c\x01\xf4"
    assert motors(True, True, True) == b"\x8a\x07"
    assert motors(False, False, True) == b"\x8a\x01"
    assert query_list([7, 43, 44]) == b"\x95\x03\x07\x2b\x2c"
    with pytest.raises(ValueError):
        drive_direct(501, 0)
    with pytest.raises(ValueError):
        query_list([255])


def test_known_packet_bytes_and_truncated_frames():
    packets = [7, 9, 10, 11, 12, 21, 22, 23, 25, 26, 43, 44]
    raw = b"\x09\x00\x01\x00\x00\x02" + struct.pack(">HhHHHH", 14500, -120, 1000, 2000, 65534, 3)
    sensors = decode_sensors(packets, raw)
    assert sensors.bumper.right and sensors.bumper.wheel_drop
    assert sensors.cliff.front_left
    assert sensors.battery.percent == 50
    assert sensors.battery.voltage == 14.5
    assert sensors.battery.current == -0.12
    assert sensors.encoders.left == 65534 and sensors.encoders.right == 3
    with pytest.raises(ValueError):
        decode_sensors(packets, raw[:-1])
    with pytest.raises(ValueError):
        decode_sensors(packets, raw + b"\x00")

"""Decode Roomba Open Interface sensor packets. Plain Python, no ROS or serial.

Roomba 600 OI reference (packet group 100, pages 22-31 and 38):
https://cdn-shop.adafruit.com/datasheets/create_2_Open_Interface_Spec.pdf

The "sci" layout is the older 26-byte format from the SCI manual. A Roomba 680
uses "oi", so the SCI parts are optional and can be deleted later.
"""

import math
import struct
import time


# Fields are in wire order. B/b are unsigned/signed bytes; H/h are
# unsigned/signed 16-bit values. All multi-byte fields are big-endian.
SCI_FIELDS = (
    ("bumps_wheeldrops_raw", "B"),
    ("wall", "B"),
    ("cliff_left", "B"),
    ("cliff_front_left", "B"),
    ("cliff_front_right", "B"),
    ("cliff_right", "B"),
    ("virtual_wall", "B"),
    ("motor_overcurrents_raw", "B"),
    ("dirt_detector_left", "B"),
    ("dirt_detector_right", "B"),
    ("remote_control_command", "B"),
    ("buttons_raw", "B"),
    ("distance_mm", "h"),
    ("angle_raw", "h"),
    ("charging_state", "B"),
    ("battery_voltage_mv", "H"),
    ("battery_current_ma", "h"),
    ("battery_temperature_c", "b"),
    ("battery_charge_mah", "H"),
    ("battery_capacity_mah", "H"),
)

OI_FIELDS = SCI_FIELDS[:8] + (
    ("dirt_detect", "B"),
    ("unused_16", "B"),
    ("infrared_omni", "B"),
) + SCI_FIELDS[11:] + (
    ("wall_signal", "H"),
    ("cliff_left_signal", "H"),
    ("cliff_front_left_signal", "H"),
    ("cliff_front_right_signal", "H"),
    ("cliff_right_signal", "H"),
    ("unused_32", "B"),
    ("unused_33", "H"),
    ("charging_sources_raw", "B"),
    ("oi_mode", "B"),
    ("song_number", "B"),
    ("song_playing", "B"),
    ("stream_packet_count", "B"),
    ("requested_velocity_mm_s", "h"),
    ("requested_radius_mm", "h"),
    ("requested_right_velocity_mm_s", "h"),
    ("requested_left_velocity_mm_s", "h"),
    ("encoder_counts_left", "H"),
    ("encoder_counts_right", "H"),
    ("light_bumper_raw", "B"),
    ("light_bump_left_signal", "H"),
    ("light_bump_front_left_signal", "H"),
    ("light_bump_center_left_signal", "H"),
    ("light_bump_center_right_signal", "H"),
    ("light_bump_front_right_signal", "H"),
    ("light_bump_right_signal", "H"),
    ("infrared_left", "B"),
    ("infrared_right", "B"),
    ("left_motor_current_ma", "h"),
    ("right_motor_current_ma", "h"),
    ("main_brush_current_ma", "h"),
    ("side_brush_current_ma", "h"),
    ("stasis_raw", "B"),
)

CHARGING_STATES = (
    "not_charging", "charging_recovery", "charging", "trickle_charging",
    "waiting", "charging_error",
)


def packet_layout(protocol):
    if protocol == "sci":
        return 0, SCI_FIELDS
    if protocol == "oi":
        return 100, OI_FIELDS
    raise ValueError(f"Unknown protocol: {protocol}")


def decode_sensors(payload, protocol="oi"):
    """Decode one complete response, including raw values and named bits."""
    _, fields = packet_layout(protocol)
    layout = struct.Struct(">" + "".join(kind for _, kind in fields))
    if len(payload) != layout.size:
        raise ValueError(f"Expected {layout.size} bytes, got {len(payload)}")
    result = dict(zip((name for name, _ in fields), layout.unpack(payload)))

    def bits(field, names):
        return {name: bool(result[field] & (1 << bit))
                for bit, name in names.items()}

    bump_names = {0: "bump_right", 1: "bump_left",
                  2: "wheeldrop_right", 3: "wheeldrop_left"}
    motor_names = {0: "side_brush", 2: "main_brush",
                   3: "drive_right", 4: "drive_left"}
    if protocol == "sci":
        bump_names[4] = "wheeldrop_caster"
        motor_names[1] = "vacuum"
        button_names = {0: "max", 1: "clean", 2: "spot", 3: "power"}
        # SCI reports half the wheel-distance difference, not degrees.
        result["angle_degrees"] = 360 * result["angle_raw"] / (258 * math.pi)
    else:
        button_names = dict(enumerate(
            ("clean", "spot", "dock", "minute", "hour", "day", "schedule", "clock")
        ))
        result["angle_degrees"] = result["angle_raw"]
        result["charging_sources"] = bits(
            "charging_sources_raw", {0: "internal_charger", 1: "home_base"}
        )
        result["light_bumper"] = bits("light_bumper_raw", dict(enumerate(
            ("left", "front_left", "center_left", "center_right", "front_right", "right")
        )))
        result["oi_mode_name"] = {0: "off", 1: "passive", 2: "safe", 3: "full"}.get(
            result["oi_mode"], "unknown"
        )

    result["bumps_wheeldrops"] = bits("bumps_wheeldrops_raw", bump_names)
    result["motor_overcurrents"] = bits("motor_overcurrents_raw", motor_names)
    result["buttons"] = bits("buttons_raw", button_names)
    state = result["charging_state"]
    result["charging_state_name"] = (
        CHARGING_STATES[state] if state < len(CHARGING_STATES) else "unknown"
    )
    capacity = result["battery_capacity_mah"]
    result["battery_percent"] = (
        round(100 * result["battery_charge_mah"] / capacity, 1) if capacity else None
    )
    return result


def read_exact(connection, size, timeout):
    """Accumulate partial serial reads within one overall deadline."""
    deadline = time.monotonic() + timeout
    data = bytearray()
    previous_timeout = connection.timeout
    try:
        while len(data) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Sensor response incomplete: {len(data)}/{size} bytes")
            connection.timeout = remaining
            chunk = connection.read(size - len(data))
            if not chunk:
                raise TimeoutError(f"Sensor response incomplete: {len(data)}/{size} bytes")
            data.extend(chunk)
    finally:
        connection.timeout = previous_timeout
    return bytes(data)

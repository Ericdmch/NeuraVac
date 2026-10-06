"""Poll Roomba sensors over 8N1 TTL serial and print JSON.

SCI reference: docs/Roomba_SCI_manual.md, Sensor Packets (pages 7-8).
Roomba 600 OI reference (packet group 100, pages 22-31 and 38):
https://cdn-shop.adafruit.com/datasheets/create_2_Open_Interface_Spec.pdf
The script starts passive mode, pauses any old OI stream, and polls Sensors.
"""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import struct
import sys
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


def positive_number(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path,
                        default=Path(__file__).with_name("config.json"))
    parser.add_argument("--port", help="Serial device, e.g. /dev/ttyUSB0 or COM9")
    parser.add_argument("--baud", type=int, help="Override config.json BAUD_RATE")
    parser.add_argument("--protocol", choices=("oi", "sci"), default="oi",
                        help="oi: Roomba 680, 80 bytes; sci: local manual, 26 bytes")
    parser.add_argument("--interval", type=positive_number, default=1.0,
                        help="Seconds between polls (default: 1)")
    parser.add_argument("--timeout", type=positive_number, default=2.0,
                        help="Response timeout in seconds (default: 2)")
    parser.add_argument("--once", action="store_true", help="Read one sample and exit")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args(argv)
    try:
        config = {}
        if args.config.exists():
            config = json.loads(args.config.read_text(encoding="utf-8"))
            if not isinstance(config, dict):
                raise ValueError("Configuration must be a JSON object")
        port = args.port or config.get("PORT")
        baud = args.baud if args.baud is not None else config.get(
            "BAUD_RATE", 115200 if args.protocol == "oi" else 57600
        )
        if not port:
            raise ValueError("Specify --port or set PORT in config.json")
        if not isinstance(baud, int) or isinstance(baud, bool) or baud <= 0:
            raise ValueError("BAUD_RATE must be a positive integer")
        try:
            import serial
        except ImportError:
            print("Install pyserial: python3 -m pip install pyserial", file=sys.stderr)
            return 1

        group, fields = packet_layout(args.protocol)
        size = struct.calcsize(">" + "".join(kind for _, kind in fields))
        with serial.Serial(port, baud, timeout=args.timeout,
                           write_timeout=args.timeout) as connection:
            connection.write(bytes([128]))  # Start SCI/OI in passive mode.
            connection.flush()
            time.sleep(0.2)
            # No other process may use this port or leave an OI stream running.
            if args.protocol == "oi":
                connection.write(bytes([150, 0]))  # Pause any previous sensor stream.
                connection.flush()
                time.sleep(0.05)
            connection.reset_input_buffer()
            while True:
                started = time.monotonic()
                connection.write(bytes([142, group]))
                connection.flush()
                payload = read_exact(connection, size, args.timeout)
                sample = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "protocol": args.protocol,
                    "packet_group": group,
                    "raw_hex": payload.hex(),
                    "sensors": decode_sensors(payload, args.protocol),
                }
                print(json.dumps(sample, indent=2 if args.pretty else None), flush=True)
                if args.once:
                    return 0
                time.sleep(max(0, args.interval - (time.monotonic() - started)))
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError, TimeoutError) as error:
        print(f"Sensor read failed: {error}", file=sys.stderr)
        print("Check power, baud rate, RX/TX wiring, and wake the Roomba with CLEAN. "
              "Close other programs using its serial port.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

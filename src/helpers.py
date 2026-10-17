import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


def _config_path():
    """Use the repository config in source checkouts or the ROS share copy."""
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    try:
        from ament_index_python.packages import get_package_share_directory
        return Path(get_package_share_directory("neuravac_ros")) / "config.json"
    except (ImportError, LookupError):
        return CONFIG_PATH

def getConfig(key:str):
    """Read a setting from config.json in the working directory, or return None."""
    # Reload the file each time so callers see the current configuration.
    with _config_path().open("r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get(key)

def split16(value):
    """Return [high_byte, low_byte] of a signed 16-bit value."""
    # Mask each byte to preserve the low 16 bits, including negative values'
    # two's-complement representation and protocol sentinel values like 0x8000.
    high = (value >> 8) & 0xFF
    low = value & 0xFF
    return [high, low]

def parse_opcode(message):
    """Parse a space- or comma-separated sequence of serial opcode bytes."""
    parts = message.replace(",", " ").split()
    try:
        code = [int(part, 0) for part in parts]
    except ValueError as error:
        raise ValueError("opcodes must be decimal or hexadecimal bytes") from error

    if not code:
        raise ValueError("enter at least one opcode byte")
    if any(byte < 0 or byte > 255 for byte in code):
        raise ValueError("each opcode byte must be between 0 and 255")

    return code


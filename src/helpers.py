import json

def getConfig(key:str):
    """Read a setting from config.json in the working directory, or return None."""
    # Reload the file each time so callers see the current configuration.
    with open("config.json", "r") as f:
        config = json.load(f)
    return config.get(key)

def split16(value):
    """Return [high_byte, low_byte] of a signed 16-bit value."""
    # Mask each byte to preserve the low 16 bits, including negative values'
    # two's-complement representation and protocol sentinel values like 0x8000.
    high = (value >> 8) & 0xFF
    low = value & 0xFF
    return [high, low]

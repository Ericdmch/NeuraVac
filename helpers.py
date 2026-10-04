import json

def getConfig(key:str):
    with open("config.json", "r") as f:
        config = json.load(f)
    return config.get(key)

def split16(value):
    """Return [high_byte, low_byte] of a signed 16-bit value."""
    high = (value >> 8) & 0xFF
    low = value & 0xFF
    return [high, low]
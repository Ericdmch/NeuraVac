"""Fail closed on missing, stale, or hazardous independent drive inputs."""
import math
from .autonomy_drive import safety_from_group_zero


def motion_fault(inputs, now, max_age=.5):
    if not isinstance(inputs, dict) or not math.isfinite(now):
        return 'safety inputs unavailable'
    for name in ('sensors', 'scan', 'pose', 'odom', 'status'):
        item = inputs.get(name)
        if not isinstance(item, tuple) or len(item) != 2:
            return f'{name} unavailable'
        stamp, value = item
        if not isinstance(stamp, (float, int)) or not math.isfinite(stamp) or not 0 <= now - stamp <= max_age:
            return f'{name} stale'
        if name == 'sensors':
            fault = safety_from_group_zero(value)
            if fault:
                return fault
        elif name == 'status':
            if value != 'TRACKING':
                return 'localization not tracking'
        elif value is not True:
            return f'{name} invalid'
    return None


def scan_clear(ranges, range_min, range_max, stop_radius):
    if (not ranges or not all(math.isfinite(v) for v in (range_min, range_max, stop_radius))
            or not 0 <= range_min < range_max or stop_radius <= 0):
        return False
    valid = [v for v in ranges if math.isfinite(v) and range_min <= v <= range_max]
    if len(valid) < max(1, math.ceil(len(ranges) * .5)):
        return False
    # Require evidence in every 45-degree index sector, not just an aggregate
    # count; this assumes a complete 360-degree scan with regular binning.
    if len(ranges) < 8:
        return False
    for sector in range(8):
        chunk = ranges[sector * len(ranges) // 8:(sector + 1) * len(ranges) // 8]
        if not any(math.isfinite(v) and range_min <= v <= range_max for v in chunk):
            return False
    return min(valid) > stop_radius

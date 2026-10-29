"""Read optional Raspberry Pi diagnostics without requiring hardware-specific Python packages."""
import re
import subprocess
import threading


def command(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=1, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def decode_throttled(value):
    try:
        bits = int(value.split('=', 1)[1], 16)
    except (AttributeError, IndexError, ValueError):
        return None
    labels = ['Undervoltage', 'Frequency capped', 'Throttling', 'Soft temperature limit']
    return {'raw': f'0x{bits:x}', 'current': [label for bit, label in enumerate(labels) if bits & (1 << bit)],
            'history': [label for bit, label in enumerate(labels) if bits & (1 << (bit + 16))]}


def parse_usb(value):
    return [m.group(1) for line in (value or '').splitlines()
            if (m := re.search(r'ID ([0-9a-fA-F]{4}:[0-9a-fA-F]{4} .+)', line))
            and not m.group(1).lower().startswith('1d6b:')]


_cpu_lock = threading.Lock()
_cpu_previous = None


def cpu_usage():
    global _cpu_previous
    try:
        with open('/proc/stat', encoding='ascii') as stream:
            fields = stream.readline().split()
        if fields[0] != 'cpu' or len(fields) < 5:
            return None
        values = [int(value) for value in fields[1:]]
        total = sum(values[:8])
        idle = values[3] + (values[4] if len(values) > 4 else 0)
    except (OSError, ValueError, IndexError):
        return None
    with _cpu_lock:
        previous, _cpu_previous = _cpu_previous, (total, idle)
    if previous is None or total <= previous[0]:
        return None
    return round(100 * (1 - (idle - previous[1]) / (total - previous[0])), 1)


def snapshot():
    temperature = command('vcgencmd', 'measure_temp')
    match = re.search(r"temp=([0-9.]+)", temperature or '')
    usb = command('lsusb')
    return {'temperature_c': float(match.group(1)) if match else None,
            'throttled': decode_throttled(command('vcgencmd', 'get_throttled')),
            'usb_devices': parse_usb(usb) if usb is not None else None,
            'cpu_percent': cpu_usage()}

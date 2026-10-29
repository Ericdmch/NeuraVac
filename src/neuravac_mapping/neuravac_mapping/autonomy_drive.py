"""Validate Roomba safety telemetry and encode bounded differential drive."""
import math


def safety_from_group_zero(packet):
    if not isinstance(packet, (bytes, bytearray, list, tuple)) or len(packet) != 26:
        return 'Roomba safety readings unavailable'
    if any(not isinstance(v, int) or not 0 <= v <= 255 for v in packet):
        return 'Roomba safety readings invalid'
    if packet[0] & 0x03:
        return 'bumper'
    if packet[0] & 0x1c:
        return 'wheel drop'
    if any(packet[2:6]):
        return 'cliff'
    if packet[6]:
        return 'virtual wall'
    if packet[7]:
        return 'motor overcurrent'
    if packet[16] not in (0, 4):
        return 'charging or invalid charging state'
    return None


def drive_command(linear_m_s, angular_rad_s, track_m=.235, max_wheel_m_s=.15):
    if not all(math.isfinite(v) for v in (linear_m_s, angular_rad_s, track_m, max_wheel_m_s)) or track_m <= 0 or max_wheel_m_s <= 0:
        raise ValueError('Invalid drive values')
    right = linear_m_s + angular_rad_s * track_m / 2
    left = linear_m_s - angular_rad_s * track_m / 2
    if max(abs(right), abs(left)) > max_wheel_m_s:
        raise ValueError('Wheel speed exceeds autonomous limit')
    def encode(v):
        return int(v * 1000).to_bytes(2, 'big', signed=True)
    return bytes((145,)) + encode(right) + encode(left)

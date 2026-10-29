"""Fail-closed safety checks for autonomous motion inputs.

This is a policy helper, not a watchdog or a physical motor interlock.
"""
import math

HAZARDS = ('bump_left', 'bump_right', 'wheel_drop_left', 'wheel_drop_right',
           'cliff_left', 'cliff_right', 'cliff_front_left', 'cliff_front_right',
           'overcurrent', 'virtual_wall')


def safety_fault(robot, mapping_ready, max_sensor_age=0.5):
    if mapping_ready is not True:
        return 'mapping data unavailable or stale'
    if not isinstance(robot, dict) or robot.get('online') is not True or robot.get('bridge_connected') is not True:
        return 'Roomba telemetry unavailable'
    age = robot.get('age_seconds')
    if isinstance(age, bool) or not isinstance(age, (int, float)) or not math.isfinite(age) or not 0 <= age <= max_sensor_age:
        return 'Roomba telemetry stale'
    values = robot.get('values')
    if not isinstance(values, dict):
        return 'Roomba safety readings unavailable'
    for name in HAZARDS:
        if values.get(name) is True:
            return name
        if values.get(name) is not False:
            return 'Roomba safety readings unavailable'
    return None

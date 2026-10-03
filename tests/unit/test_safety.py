import pytest

from neuravac_core.config import SafetyConfig
from neuravac_core.models import BatteryState, BumperState, CliffState
from neuravac_core.safety import CommandArbiter, SafetyMonitor, SensorSnapshot, VelocityCommand


def healthy(now=1):
    return SensorSnapshot(
        base_timestamp=now,
        scan_timestamp=now,
        camera_timestamp=now,
        heartbeat_timestamp=now,
        battery=BatteryState(),
    )


def test_startup_missing_sensors_inhibits_and_expired_commands_stop():
    safety = SafetyMonitor(SafetyConfig())
    assert not safety.evaluate(SensorSnapshot(), 1).safe
    arbiter = CommandArbiter(SafetyConfig())
    status = safety.evaluate(healthy(), 1)
    arbiter.submit(VelocityCommand(source="navigation", linear_mps=0.2, timestamp=1))
    assert arbiter.select(1.1, status).linear_mps == 0.2
    assert arbiter.select(1.51, status).linear_mps == 0
    assert arbiter.select(0.9, status).linear_mps == 0


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("bumper", "bumper"),
        ("cliff", "cliff"),
        ("wheel_drop", "wheel_drop"),
        ("base", "base_stale"),
        ("scan", "lidar_stale"),
        ("camera", "camera_stale"),
        ("heartbeat", "heartbeat_stale"),
        ("battery", "critical_battery"),
        ("current", "motor_current"),
        ("disconnected", "base_disconnected"),
    ],
)
def test_fault_injection(fault, reason):
    s = healthy(2)
    if fault == "bumper":
        s.bumper = BumperState(left=True)
    elif fault == "cliff":
        s.cliff = CliffState(front_left=True)
    elif fault == "wheel_drop":
        s.bumper = BumperState(wheel_drop=True)
    elif fault in ("base", "scan", "camera", "heartbeat"):
        setattr(s, f"{fault}_timestamp", None)
    elif fault == "battery":
        s.battery = BatteryState(percent=3)
    elif fault == "current":
        s.battery = BatteryState(current=9)
    elif fault == "disconnected":
        s.connected = False
    monitor = SafetyMonitor(SafetyConfig())
    status = monitor.evaluate(s, 2)
    assert not status.safe and reason in status.reasons
    arbiter = CommandArbiter(SafetyConfig())
    arbiter.submit(VelocityCommand(source="manual", linear_mps=0.2, timestamp=2))
    assert arbiter.select(2, status).linear_mps == 0


def test_emergency_latch_and_manual_priority():
    monitor = SafetyMonitor(SafetyConfig())
    safe = monitor.evaluate(healthy(), 1)
    arbiter = CommandArbiter(SafetyConfig())
    arbiter.submit(VelocityCommand(source="navigation", linear_mps=0.1, timestamp=1))
    arbiter.submit(VelocityCommand(source="manual", linear_mps=0.2, timestamp=1))
    assert arbiter.select(1, safe).source == "manual"
    monitor.emergency_stop()
    assert not monitor.evaluate(healthy(), 1).safe
    assert not monitor.reset(SensorSnapshot(), 1)
    assert monitor.reset(healthy(), 1)
    assert monitor.evaluate(healthy(), 1).safe


def test_nonfinite_velocity_rejected():
    with pytest.raises(ValueError):
        VelocityCommand(source="manual", linear_mps=float("nan"), timestamp=1)

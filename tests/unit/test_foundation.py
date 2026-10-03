import io
import json
import logging

import pytest
from pydantic import ValidationError

from neuravac_core.base.mock import MockRobotBase
from neuravac_core.config import RobotConfig, load_config
from neuravac_core.models import Decision, Detection, Pose
from neuravac_core.utils.logging import JsonFormatter, redact


def test_config_defaults_and_unknown_options(tmp_path):
    assert RobotConfig().safety.watchdog_s == 0.5
    path = tmp_path / "config.yaml"
    path.write_text("backend: mock\nwheel_base_m: 0.235\n")
    assert load_config(path).backend == "mock"
    path.write_text("backend: magic\n")
    with pytest.raises(ValidationError):
        load_config(path)
    with pytest.raises(ValidationError):
        RobotConfig(wheel_base_m=-1)
    with pytest.raises(ValidationError):
        RobotConfig(typo=True)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_finite_pose(value):
    with pytest.raises(ValidationError):
        Pose(x=value)


def test_strict_ai_output_rejects_motion_and_bad_confidence():
    with pytest.raises(ValidationError):
        Decision(action="clean_region", target_id="d1", priority=0.9, reason="go", wheel_pwm=255)
    with pytest.raises(ValidationError):
        Detection(class_name="cable", confidence=2, timestamp=0, source="mock")


async def test_mock_connect_velocity_emergency_latch():
    base = MockRobotBase()
    with pytest.raises(ConnectionError):
        await base.set_velocity(0.2, 0)
    await base.connect()
    await base.set_velocity(0.2, 0)
    await base.set_vacuum(True)
    await base.emergency_stop()
    assert base.velocity == (0, 0)
    assert not base.vacuum
    with pytest.raises(RuntimeError):
        await base.set_velocity(0.2, 0)
    await base.disconnect()
    assert not base.connected


def test_json_logging_redacts_nested_secrets():
    assert redact({"Authorization": "Bearer secret", "nested": {"api_key": "secret"}}) == {
        "Authorization": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]"},
    }
    stream = io.StringIO()
    logger = logging.Logger("test")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.info("connected", extra={"event": "startup", "data": {"token": "secret"}})
    payload = json.loads(stream.getvalue())
    assert payload["event"] == "startup"
    assert "secret" not in stream.getvalue()


def test_logs_preserve_numeric_token_usage_but_hide_credentials():
    data = redact(
        {
            "usage": {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16},
            "token": "private",
        }
    )
    assert data["usage"]["total_tokens"] == 16
    assert data["token"] == "[REDACTED]"


async def test_base_command_history_is_bounded_on_long_running_service():
    base = MockRobotBase()
    await base.connect()
    for _ in range(1000):
        await base.set_velocity(0, 0)
    assert len(base.commands) <= 512
    await base.disconnect()

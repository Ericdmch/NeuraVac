import pytest

from sim.sim2d.environment import Environment


def test_showcase_yaml_load_matches_deterministic_defaults():
    env = Environment.from_yaml("config/demo.yaml")
    assert env.width == 6 and len(env.dirt) == 2
    assert env.dirt[0].removal_rate == 0.72
    assert env.obstacles[0].class_name == "cable"


def test_environment_rejects_unknown_and_invalid_geometry(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("room: {width: -1, height: 4}\nrobot_start: {x: 0, y: 0}\n")
    with pytest.raises(ValueError):
        Environment.from_yaml(path)

"""Run without ROS; transport contracts reject stale/nonfinite and ambiguous observations."""

import ast
import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "ros2_ws/src/neuravac_base/neuravac_base/contracts.py"


def contracts():
    spec = importlib.util.spec_from_file_location("ros_contracts", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_detection_envelope_distinguishes_unavailable_from_empty():
    c = contracts()
    good = c.envelope("detections", 10, {"available": True, "detections": []})
    assert c.decode(good, "detections", 10.1, 0.5)["payload"]["available"]
    with pytest.raises(ValueError):
        c.decode(good, "detections", 11, 0.5)
    with pytest.raises(ValueError):
        c.decode(good, "detections", 9, 0.5)
    bad = json.loads(good)
    bad["schema_version"] = 2
    with pytest.raises(ValueError):
        c.decode(json.dumps(bad), "detections", 10, 0.5)
    with pytest.raises(ValueError):
        c.envelope("detections", float("nan"), {})


def test_snapshot_roundtrip_and_keepout_are_conservative():
    from neuravac_core.config import RobotConfig
    from neuravac_core.models import Detection
    from neuravac_core.world import WorldModel

    c = contracts()
    world = WorldModel(RobotConfig())
    world.observe(
        [
            Detection(
                class_name="cable", confidence=0.99, timestamp=10, source="test", position=(1, 1)
            )
        ],
        10,
    )
    restored = c.restore_world(world.to_dict(), RobotConfig())
    assert not restored.safe_point((1, 1))
    cells = c.keepout_cells(restored, 30, 30, 0.1, (0, 0))
    assert cells[10 * 30 + 10] == 100
    assert cells[0] == 0


def test_package_and_launch_contracts():
    packages = list((ROOT / "ros2_ws/src").glob("neuravac_*"))
    assert len(packages) == 10
    for package in packages:
        xml = ET.parse(package / "package.xml").getroot()
        assert xml.findtext("export/build_type") == "ament_python"
        assert (package / "resource" / package.name).exists()
        assert "script_dir=$base/lib/" + package.name in (package / "setup.cfg").read_text()
        ast.parse((package / "setup.py").read_text())
    launch = (ROOT / "ros2_ws/src/neuravac_bringup/launch/bringup.launch.py").read_text()
    assert 'src="docking_server:cmd_vel"' in launch
    assert 'src="/cmd_vel"' not in launch
    import yaml

    params = yaml.safe_load((ROOT / "config/navigation.yaml").read_text())
    assert params["collision_monitor"]["ros__parameters"]["cmd_vel_out_topic"] == "/nav/cmd_vel"
    assert params["collision_monitor"]["ros__parameters"]["cmd_vel_in_topic"] == "cmd_vel_smoothed"
    assert params["velocity_smoother"]["ros__parameters"]["enable_stamped_cmd_vel"] is False
    assert "navigation_launch.py" in launch and "online_async_launch.py" in launch
    assert "semantic_filter_lifecycle" in launch


def test_only_safety_publishes_actuator_topics():
    for file in (ROOT / "ros2_ws/src").rglob("*.py"):
        tree = ast.parse(file.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "create_publisher"
                and len(node.args) > 1
                and isinstance(node.args[1], ast.Constant)
            ):
                if node.args[1].value in ("/cmd_vel", "/base/vacuum_cmd"):
                    assert file.parent.name == "neuravac_safety"


def test_empty_inference_requires_calibration_and_tf():
    from neuravac_core.models import Detection, Pose

    c = contracts()

    class Projector:
        image_size = (320, 320)

        def project_pixel(self, u, v, pose):
            assert 0 <= u < 320 and 0 <= v < 320
            return (pose.x + u / 100, pose.y + v / 100)

    with pytest.raises(ValueError):
        c.project_observations([], None, Pose())
    with pytest.raises(ValueError):
        c.project_observations([], Projector(), None)
    assert c.project_observations([], Projector(), Pose()) == []
    floor = Detection(
        class_name="clean_floor",
        confidence=0.99,
        timestamp=1,
        source="test",
        bbox=(10, 10, 320, 320),
    )
    result = c.project_observations([floor], Projector(), Pose())[0]
    assert len(result.polygon) == 4 and result.position is not None


def test_historical_unresolved_regions_remain_fail_closed():
    from neuravac_core.config import RobotConfig
    from neuravac_core.models import Detection
    from neuravac_core.world import WorldModel

    world = WorldModel(RobotConfig())
    world.observe(
        [
            Detection(
                class_name="debris",
                confidence=0.95,
                timestamp=1,
                source="test",
                position=(1, 1),
                debris_score=1,
            )
        ],
        1,
    )
    world.expire(100)
    restored = contracts().restore_world(world.to_dict(), RobotConfig())
    assert len(restored.regions) == 1
    assert not next(iter(restored.regions.values())).reachable
    with pytest.raises(ValueError):
        restored.score(next(iter(restored.regions)), 100)
    invalid = world.to_dict()
    invalid["regions"][0]["reachable"] = True
    with pytest.raises(ValueError):
        contracts().restore_world(invalid, RobotConfig())

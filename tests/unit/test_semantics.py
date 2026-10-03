import pytest

from neuravac_core.config import RobotConfig
from neuravac_core.mission import MissionMachine
from neuravac_core.models import Decision, Detection
from neuravac_core.world import WorldModel


def debris(x=1, score=1, t=1):
    return Detection(
        class_name="debris",
        confidence=0.9,
        timestamp=t,
        source="test",
        position=(x, 1),
        debris_score=score,
    )


def test_tracking_fusion_clusters_and_stale_removal():
    world = WorldModel(RobotConfig())
    world.observe([debris(), debris(1.15)], 1)
    assert len(world.regions) == 1
    object_ids = set(world.objects)
    world.observe([debris(1.01, t=2), debris(1.16, t=2)], 2)
    assert set(world.objects) == object_ids
    assert len(world.regions) == 1
    world.expire(40)
    assert not world.objects


def test_low_confidence_sock_and_cable_are_prohibited_and_ai_cannot_clean_them():
    world = WorldModel(RobotConfig())
    world.observe(
        [
            debris(),
            Detection(
                class_name="clothing", confidence=0.4, timestamp=1, source="test", position=(1, 1)
            ),
            Detection(
                class_name="cable", confidence=0.98, timestamp=1, source="test", position=(2, 2)
            ),
        ],
        1,
    )
    assert all(not o.traversable for o in world.objects.values() if o.class_name != "debris")
    target = next(iter(world.regions.values()))
    assert not target.reachable
    with pytest.raises(ValueError):
        world.validate_decision(
            Decision(action="clean_region", target_id=target.id, reason="go"), 1
        )
    with pytest.raises(ValueError):
        world.validate_decision(Decision(action="finish", reason="done"), 1)


def test_missing_after_observation_never_becomes_clean():
    world = WorldModel(RobotConfig())
    world.observe([debris()], 1)
    region = next(iter(world.regions.values()))
    assert world.score(region.id, 1) == 1
    world.observe([], 2)
    with pytest.raises(ValueError):
        world.score(region.id, 2)
    assert not region.cleaned


def test_mission_illegal_transition_and_explicit_start():
    machine = MissionMachine()
    with pytest.raises(ValueError):
        machine.transition("CLEANING")
    machine.transition("SELF_TEST")
    machine.transition("IDLE")
    assert machine.state == "IDLE"
    machine.transition("SCANNING")
    machine.transition("PLANNING")
    machine.transition("NAVIGATING")


def test_stale_debris_keeps_unresolved_evidence_until_fresh_inspection():
    world = WorldModel(RobotConfig())
    world.observe([debris(t=1)], 1)
    region_id = next(iter(world.regions))
    world.observe([], 40)
    assert not world.objects
    assert world.regions[region_id].debris_score == 1
    assert not world.regions[region_id].reachable
    with pytest.raises(ValueError):
        world.validate_decision(Decision(action="finish", reason="done"), 40)
    with pytest.raises(ValueError):
        world.score(region_id, 40)
    world.observe([debris(score=0, t=41)], 41)
    assert region_id in world.regions
    assert world.score(region_id, 41) == 0


def test_only_explicit_confident_clear_floor_polygon_can_verify_absent_debris():
    world = WorldModel(RobotConfig())
    world.observe([debris(t=1)], 1)
    target = next(iter(world.regions))
    world.observe([], 2)
    with pytest.raises(ValueError):
        world.score(target, 2)
    world.observe(
        [
            Detection(
                class_name="clean_floor",
                confidence=0.95,
                timestamp=3,
                source="onnx",
                position=(1, 1),
                polygon=[(0.7, 0.7), (1.3, 0.7), (1.3, 1.3), (0.7, 1.3)],
            )
        ],
        3,
    )
    assert world.score(target, 3) == 0


def test_clear_floor_never_overwrites_concurrent_debris_or_hazard():
    world = WorldModel(RobotConfig())
    floor = Detection(
        class_name="clean_floor",
        confidence=0.95,
        timestamp=2,
        source="onnx",
        position=(1, 1),
        polygon=[(0.7, 0.7), (1.3, 0.7), (1.3, 1.3), (0.7, 1.3)],
    )
    world.observe([debris(t=1)], 1)
    target = next(iter(world.regions))
    world.observe([debris(t=2), floor], 2)
    assert world.score(target, 2) == 1


def test_planning_weights_can_prefer_large_far_target():
    from neuravac_core.models import Pose

    world = WorldModel(RobotConfig(planning={"distance_weight": 10, "amount_weight": 1}))
    world.observe([debris(x=0.5, score=1), debris(x=4, score=3)], 1)
    close = world.choose(Pose(x=0.5, y=1))
    assert close.position[0] == 0.5
    world.config.planning.distance_weight = 0
    assert world.choose(Pose(x=0.5, y=1)).position[0] == 4

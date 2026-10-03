import math

import pytest

from neuravac_core.runtime import SimulationRuntime


async def test_definition_of_done_with_retry_chair_replan_and_cable_avoidance(tmp_path):
    runtime = SimulationRuntime(db_path=tmp_path / "mission.db")
    await runtime.initialize()
    assert runtime.machine.state == "IDLE"
    assert runtime.base.velocity == (0, 0)
    runtime.start()
    await runtime.run_until_terminal()
    assert runtime.machine.state == "COMPLETE"
    assert len(runtime.attempts) >= 3
    assert any(not a["success"] for a in runtime.attempts)
    assert all(
        d.score <= runtime.config.cleaning.success_threshold for d in runtime.environment.dirt
    )
    assert any(e["event"] == "environment_changed" for e in runtime.events)
    assert any(e["event"] == "route_replanned" for e in runtime.events)
    cable = next(o for o in runtime.environment.obstacles if o.id == "cable")
    assert all(
        math.hypot(x - cable.x, y - cable.y) > cable.radius + runtime.config.robot_radius_m
        for x, y in runtime.base.trajectory
    )
    assert not runtime.base.vacuum and runtime.base.velocity == (0, 0)
    rows = runtime.store.export_table("cleaning_attempts")
    assert len(rows) == len(runtime.attempts)
    await runtime.close()


@pytest.mark.parametrize(
    "fault", ["cliff", "bumper", "serial", "camera", "lidar", "heartbeat", "battery"]
)
async def test_fault_during_motion_stops_and_surfaces(fault, tmp_path):
    runtime = SimulationRuntime(db_path=tmp_path / f"{fault}.db")
    await runtime.initialize()
    runtime.start()
    for _ in range(20):
        await runtime.tick()
    runtime.inject_fault(fault)
    await runtime.tick()
    assert runtime.machine.state == "FAULT"
    assert not runtime.safety_status.safe
    assert runtime.base.velocity == (0, 0) and not runtime.base.vacuum
    assert runtime.events[-1]["event"] == "safety_fault"
    await runtime.close()


async def test_pause_clears_old_commands_and_resume_requires_healthy_sensors(tmp_path):
    runtime = SimulationRuntime(db_path=tmp_path / "pause.db")
    await runtime.initialize()
    runtime.start()
    for _ in range(20):
        await runtime.tick()
    await runtime.pause()
    assert runtime.base.velocity == (0, 0)
    runtime.inject_fault("camera")
    await runtime.tick()
    with pytest.raises(ValueError):
        runtime.resume()
    await runtime.close()


async def test_idle_metrics_do_not_claim_dirty_room_clean():
    runtime = SimulationRuntime()
    await runtime.initialize()
    assert runtime.metrics()["regions_remaining"] == 2
    assert runtime.metrics()["cleanliness_percent"] == 0
    await runtime.close()


async def test_cables_and_unknown_possessions_block_targets_without_false_complete():
    from sim.sim2d.environment import Environment, Obstacle

    env = Environment.demo()
    env.obstacles = [
        Obstacle("cable", 1.6, 1, 0.3, "cable"),
        Obstacle("unknown", 4.7, 2.8, 0.3, "unknown"),
    ]
    runtime = SimulationRuntime(environment=env, move_chair=False)
    await runtime.initialize()
    runtime.start()
    await runtime.run_until_terminal()
    assert runtime.machine.state == "PAUSED"
    assert runtime.metrics()["regions_remaining"] == 2
    assert runtime.base.velocity == (0, 0)
    assert not runtime.attempts
    await runtime.close()


async def test_reserve_battery_returns_home_then_waits_for_charge():
    runtime = SimulationRuntime(move_chair=False)
    await runtime.initialize()
    runtime.start()
    for _ in range(80):
        await runtime.tick()
    runtime.base.battery.percent = 15
    await runtime.run_until_terminal()
    assert runtime.machine.state == "PAUSED"
    assert any(t["to"] == "RETURNING_HOME" for t in runtime.machine.transitions)
    assert abs(runtime.base.pose.x - runtime.environment.start.x) < 0.08
    assert abs(runtime.base.pose.y - runtime.environment.start.y) < 0.08
    assert not runtime.base.vacuum
    await runtime.close()


async def test_low_startup_battery_fails_readiness_and_cannot_start():
    runtime = SimulationRuntime()
    runtime.base.battery.percent = 15
    await runtime.initialize()
    assert runtime.self_test["status"] == "NOT_READY"
    with pytest.raises(ValueError):
        runtime.start()
    assert runtime.base.velocity == (0, 0)
    await runtime.close()

import json

import pytest

from neuravac_core.recording import SessionRecorder, replay_events, replay_world
from neuravac_core.runtime import SimulationRuntime


async def test_record_and_replay_world_no_secret_or_actuation(tmp_path):
    path = tmp_path / "session.jsonl"
    recorder = SessionRecorder(path)
    recorder.write("cloud_request", 0, {"authorization": "secret", "reasoning_content": "private"})
    runtime = SimulationRuntime(recorder=recorder)
    await runtime.initialize()
    runtime.start()
    await runtime.run_until_terminal()
    final = runtime.snapshot()
    await runtime.close()
    assert "secret" not in path.read_text() and "private" not in path.read_text()
    events = list(replay_events(path))
    assert events[-1]["data"]["state"]["state"] == "COMPLETE"
    world = replay_world(path, runtime.config)
    assert (
        sum(r.debris_score for r in world.regions.values())
        == final["metrics"]["current_debris_score"]
    )


def test_replay_rejects_out_of_order_and_bad_schema(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text(
        json.dumps({"version": 1, "event": "x", "timestamp": 2, "data": {}})
        + "\n"
        + json.dumps({"version": 1, "event": "x", "timestamp": 1, "data": {}})
        + "\n"
    )
    with pytest.raises(ValueError):
        list(replay_events(path))


async def test_recording_can_feed_perception_replay(tmp_path):
    from neuravac_core.perception import ReplayProvider

    path = tmp_path / "sensor.jsonl"
    runtime = SimulationRuntime(recorder=SessionRecorder(path))
    await runtime.initialize()
    runtime.start()
    for _ in range(5):
        await runtime.tick()
    await runtime.close()
    provider = ReplayProvider(path)
    assert provider.labels

from types import SimpleNamespace

import pytest

from neuravac_core.models import Decision
from neuravac_core.runtime import SimulationRuntime


class FaultyCloud:
    config = SimpleNamespace(model="nvidia/test-Nemotron")
    last_telemetry = {"status": "error", "model": "nvidia/test-Nemotron", "latency_ms": 1}

    def __init__(self, failure):
        self.failure = failure

    async def decide(self, world):
        if self.failure == "timeout":
            raise TimeoutError("cloud deadline")
        if self.failure == "malformed":
            raise ValueError("bad JSON")
        return Decision(action="clean_region", target_id="nonexistent", reason="unsafe target")

    async def aclose(self):
        pass


@pytest.mark.parametrize("failure", ["timeout", "malformed", "unsafe_target"])
async def test_cloud_failure_conservative_fallback_and_local_safety(failure):
    runtime = SimulationRuntime(cloud=FaultyCloud(failure))
    await runtime.initialize()
    runtime.start()
    await runtime.run_until_terminal()
    assert runtime.machine.state == "COMPLETE"
    assert runtime.cloud_status["status"] == "degraded"
    assert any(e["event"] == "cloud_fallback" for e in runtime.events)
    assert all(a["after_score"] <= a["before_score"] for a in runtime.attempts)
    await runtime.close()


async def test_cloud_timeout_pause_policy():
    runtime = SimulationRuntime(cloud=FaultyCloud("timeout"), cloud_fallback="pause")
    await runtime.initialize()
    runtime.start()
    await runtime.run_until_terminal()
    assert runtime.machine.state == "PAUSED"
    assert runtime.base.velocity == (0, 0) and not runtime.base.vacuum
    await runtime.close()


async def test_safety_tick_remains_live_during_pending_cloud():
    import asyncio

    class SlowCloud(FaultyCloud):
        async def decide(self, world):
            await asyncio.sleep(30)
            return Decision(action="pause", reason="late")

    runtime = SimulationRuntime(cloud=SlowCloud("timeout"))
    await runtime.initialize()
    runtime.start()
    for _ in range(5):
        await runtime.tick()
    assert runtime._cloud_task and not runtime._cloud_task.done()
    runtime.inject_fault("cliff")
    await runtime.tick()
    assert runtime.machine.state == "FAULT"
    assert runtime.base.velocity == (0, 0)
    await runtime.close()


async def test_self_test_cloud_ready_requires_verified_model():
    class UnreachableCloud(FaultyCloud):
        async def verify_model(self):
            raise TimeoutError("discovery unavailable")

    runtime = SimulationRuntime(cloud=UnreachableCloud("timeout"))
    await runtime.initialize()
    assert runtime.self_test["status"] == "READY_WITH_DEGRADED_CLOUD"
    assert runtime.self_test["checks"]["cloud"] is False
    assert runtime.base.velocity == (0, 0)
    await runtime.close()

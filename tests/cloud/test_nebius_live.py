"""Real, potentially billed inference requires an explicit flag plus credentials."""

import json
import os

import pytest

pytestmark = pytest.mark.cloud


async def test_live_nemotron_decision(record_property):
    if os.environ.get("NEURAVAC_ALLOW_CLOUD_TESTS") != "1":
        pytest.skip("set NEURAVAC_ALLOW_CLOUD_TESTS=1 to authorize real billed cloud calls")
    if not os.environ.get("NEBIUS_API_KEY") or not os.environ.get("NEBIUS_MODEL"):
        pytest.skip("NEBIUS_API_KEY and account-selected NEBIUS_MODEL are required")

    from neuravac_core.cloud import NebiusClient, NebiusConfig
    from neuravac_core.models import Decision

    config = NebiusConfig.from_env()
    async with NebiusClient(config) as client:
        await client.verify_model()
        decision = await client.decide(
            {
                "mission": "PAUSED",
                "battery_percent": 80,
                "dirty_regions": [],
                "hazards": [],
                "recent_changes": ["No floor observation available; pause for inspection"],
            }
        )
        assert isinstance(decision, Decision)
        assert client.last_telemetry["status"] == "success"
        assert client.last_telemetry["model"] == config.model
        assert client.last_telemetry["request_id"]
        assert client.last_telemetry["usage"].get("total_tokens", 0) > 0
        record_property("cloud_telemetry", json.dumps(client.last_telemetry))

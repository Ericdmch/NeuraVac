"""Exercise real client behavior through HTTPX's in-process transport, never live APIs."""

import asyncio
import json
import logging

import httpx
import pytest
from pydantic import ValidationError

MODEL = "nvidia/Nemotron-3_5-Lightning"
KEY = "unit-test-secret"
WORLD = {"dirty_regions": [{"id": "r1", "debris_score": 0.8, "reachable": True}]}
DECISION = {
    "action": "clean_region",
    "target_id": "r1",
    "priority": 0.8,
    "reason": "Debris observed",
}


def cloud_types():
    from neuravac_core.cloud import CloudError, NebiusClient, NebiusConfig

    return CloudError, NebiusClient, NebiusConfig


def completion(content=None, **extra):
    return {
        "id": "chat-1",
        "model": MODEL,
        "choices": [
            {
                "message": {"content": json.dumps(DECISION) if content is None else content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35},
        **extra,
    }


def transport_for(handler):
    async def wrapped(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": MODEL}]})
        return await handler(request)

    return httpx.MockTransport(wrapped)


def test_typed_environment_configuration_and_secret_repr():
    _, _, Config = cloud_types()
    config = Config.from_env(
        {
            "NEBIUS_API_KEY": KEY,
            "NEBIUS_MODEL": MODEL,
            "NEBIUS_TIMEOUT_S": "1.5",
            "NEBIUS_MAX_RETRIES": "2",
        }
    )
    assert config.timeout_s == 1.5
    assert config.max_retries == 2
    assert config.base_url == "https://api.tokenfactory.nebius.com/v1"
    assert KEY not in repr(config)
    assert KEY not in config.model_dump_json()
    with pytest.raises((ValueError, ValidationError)):
        Config.from_env({"NEBIUS_API_KEY": KEY})


@pytest.mark.parametrize(
    "changes",
    [
        {"base_url": "http://example.test/v1"},
        {"base_url": "https://user:password@example.test/v1"},
        {"base_url": "https://example.test/v1?token=secret"},
        {"timeout_s": 0},
        {"timeout_s": float("nan")},
        {"max_retries": 11},
        {"model": "other/unverified"},
        {"api_key": ""},
    ],
)
def test_configuration_rejects_unsafe_values(changes):
    _, _, Config = cloud_types()
    with pytest.raises((ValueError, ValidationError)):
        Config(**({"api_key": KEY, "model": MODEL} | changes))


async def test_discovery_genuine_request_strict_decision_and_telemetry(caplog):
    _, Client, Config = cloud_types()
    requests = []

    async def handle(request):
        requests.append(request)
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": MODEL}, {"id": "other/model"}]})
        body = json.loads(request.content)
        assert request.url == "https://api.tokenfactory.nebius.com/v1/chat/completions"
        assert request.headers["authorization"] == f"Bearer {KEY}"
        assert body["model"] == MODEL and body["stream"] is False
        assert body["store"] is False
        assert "secret-world" not in request.content.decode()
        assert json.loads(body["messages"][1]["content"])["dirty_regions"] == WORLD["dirty_regions"]
        assert request.extensions["timeout"]["read"] == 1
        return httpx.Response(200, json=completion(), headers={"x-request-id": "req-1"})

    caplog.set_level(logging.INFO)
    async with Client(
        Config(api_key=KEY, model=MODEL, timeout_s=1), transport=httpx.MockTransport(handle)
    ) as client:
        decision = await client.decide(WORLD | {"api_key": "secret-world"})
        assert decision.action == "clean_region" and decision.target_id == "r1"
        assert client.last_telemetry["status"] == "success"
        assert client.last_telemetry["request_id"] == "req-1"
        assert client.last_telemetry["model"] == MODEL
        assert client.last_telemetry["latency_ms"] >= 0
        assert client.last_telemetry["usage"]["total_tokens"] == 35
        await client.decide(WORLD)
    assert [r.method for r in requests] == ["GET", "POST", "POST"]
    assert KEY not in caplog.text and "secret-world" not in caplog.text


async def test_account_model_unavailable_prevents_inference():
    Error, Client, Config = cloud_types()
    paths = []

    async def handle(request):
        paths.append(request.url.path)
        return httpx.Response(200, json={"data": [{"id": "other/model"}]})

    async with Client(
        Config(api_key=KEY, model=MODEL), transport=httpx.MockTransport(handle)
    ) as client:
        with pytest.raises(Error, match="model_unavailable"):
            await client.decide(WORLD)
        assert client.last_telemetry["status"] == "error"
    assert paths == ["/v1/models"]


@pytest.mark.parametrize("status", [429, 500, 502, 503])
async def test_retryable_status_has_bounded_backoff(status):
    _, Client, Config = cloud_types()
    attempts = 0
    sleeps = []

    async def handle(request):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(status, text=KEY, headers={"Retry-After": "999999"})
        return httpx.Response(200, json=completion())

    async def sleep(delay):
        sleeps.append(delay)

    async with Client(
        Config(api_key=KEY, model=MODEL, max_retries=2, max_backoff_s=0.2),
        transport=transport_for(handle),
        sleep=sleep,
    ) as client:
        assert (await client.decide(WORLD)).target_id == "r1"
        assert client.last_telemetry["attempts"] == 3
    assert attempts == 3
    assert len(sleeps) == 2 and all(0 <= delay <= 0.2 for delay in sleeps)


@pytest.mark.parametrize("failure", ["timeout", "server", "auth"])
async def test_network_failure_is_bounded_sanitized_and_recorded(failure, caplog):
    Error, Client, Config = cloud_types()
    attempts = 0

    async def handle(request):
        nonlocal attempts
        attempts += 1
        if failure == "timeout":
            raise httpx.ReadTimeout(f"Bearer {KEY}", request=request)
        return httpx.Response(
            500 if failure == "server" else 401,
            text=f"token={KEY}",
            headers={"x-request-id": f"Bearer {KEY}"},
        )

    async def sleep(delay):
        pass

    caplog.set_level(logging.INFO)
    async with Client(
        Config(api_key=KEY, model=MODEL, max_retries=2),
        transport=transport_for(handle),
        sleep=sleep,
    ) as client:
        with pytest.raises(Error) as error:
            await client.decide(WORLD)
        assert KEY not in str(error.value)
        assert KEY not in json.dumps(client.last_telemetry)
        assert client.last_telemetry["status"] == "error"
        assert client.last_telemetry["error"]
    assert attempts == (1 if failure == "auth" else 3)
    assert KEY not in caplog.text


@pytest.mark.parametrize(
    "content",
    [
        "{broken",
        "```json\n{}\n```",
        json.dumps(DECISION | {"wheel_pwm": 255}),
        json.dumps(DECISION | {"priority": 2}),
        json.dumps(DECISION | {"priority": "0.8"}),
        json.dumps(DECISION | {"priority": True}),
        json.dumps(DECISION | {"target_id": None}),
        json.dumps(DECISION | {"priority": float("nan")}),
        json.dumps(DECISION | {"reasoning_content": "private"}),
    ],
)
async def test_malformed_or_invalid_decision_fails_closed(content):
    Error, Client, Config = cloud_types()

    async def handle(request):
        return httpx.Response(200, json=completion(content))

    async with Client(Config(api_key=KEY, model=MODEL), transport=transport_for(handle)) as client:
        with pytest.raises(Error, match="invalid_response"):
            await client.decide(WORLD)
        assert client.last_telemetry["error"] == "invalid_response"


@pytest.mark.parametrize(
    "payload",
    [
        {"choices": []},
        {"choices": [{"message": {"content": None}, "finish_reason": "stop"}]},
        completion()
        | {"choices": [{"message": {"content": json.dumps(DECISION)}, "finish_reason": "length"}]},
        completion() | {"model": "other/model"},
    ],
)
async def test_invalid_or_incomplete_envelope_is_rejected(payload):
    Error, Client, Config = cloud_types()

    async def handle(request):
        return httpx.Response(200, json=payload)

    async with Client(Config(api_key=KEY, model=MODEL), transport=transport_for(handle)) as client:
        with pytest.raises(Error):
            await client.decide(WORLD)


async def test_hidden_reasoning_and_untrusted_usage_are_not_persisted(caplog):
    _, Client, Config = cloud_types()
    private = "hidden-thought-that-must-not-be-recorded"
    payload = completion()
    payload["choices"][0]["message"]["reasoning_content"] = private
    payload["usage"]["secret"] = KEY
    payload["usage"]["completion_tokens_details"] = {"reasoning_content": private}

    async def handle(request):
        return httpx.Response(200, json=payload)

    caplog.set_level(logging.INFO)
    async with Client(Config(api_key=KEY, model=MODEL), transport=transport_for(handle)) as client:
        decision = await client.decide(WORLD)
        saved = json.dumps(client.last_telemetry) + decision.model_dump_json() + caplog.text
        assert private not in saved and KEY not in saved
        assert client.last_telemetry["usage"] == {
            "prompt_tokens": 20,
            "completion_tokens": 15,
            "total_tokens": 35,
        }


async def test_cancelled_call_does_not_retry():
    _, Client, Config = cloud_types()
    started = asyncio.Event()

    async def handle(request):
        started.set()
        await asyncio.Event().wait()

    async with Client(Config(api_key=KEY, model=MODEL), transport=transport_for(handle)) as client:
        task = asyncio.create_task(client.decide(WORLD))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert client.last_telemetry["status"] == "cancelled"


async def test_physical_reasoning_is_disabled_and_never_guesses_endpoint():
    from neuravac_core.cloud import CloudError, PhysicalReasoningConfig, PhysicalReasoningProvider

    provider = PhysicalReasoningProvider()
    with pytest.raises(CloudError, match="disabled"):
        await provider.decide(WORLD)
    await provider.aclose()
    with pytest.raises((ValueError, ValidationError)):
        PhysicalReasoningConfig(enabled=True)


async def test_physical_reasoner_verifies_exact_configured_model_endpoint():
    from neuravac_core.cloud import PhysicalReasoningConfig, PhysicalReasoningProvider

    paths = []

    async def handle(request):
        paths.append(request.url.path)
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "verified-vision-model"}]})
        body = json.loads(request.content)
        assert body["model"] == "verified-vision-model"
        payload = completion(model="verified-vision-model")
        return httpx.Response(200, json=payload)

    config = PhysicalReasoningConfig(
        enabled=True,
        completion_url="https://vision.test/custom/completion",
        models_url="https://vision.test/catalog",
        model="verified-vision-model",
        api_key=KEY,
    )
    async with PhysicalReasoningProvider(config, transport=httpx.MockTransport(handle)) as provider:
        assert (await provider.decide(WORLD)).target_id == "r1"
        assert provider.last_telemetry["status"] == "success"
    assert paths == ["/catalog", "/custom/completion"]


async def test_inference_request_id_never_reuses_discovery_id():
    _, Client, Config = cloud_types()

    async def handle(request):
        if request.method == "GET":
            return httpx.Response(
                200, json={"data": [{"id": MODEL}]}, headers={"x-request-id": "discovery-id"}
            )
        return httpx.Response(200, json=completion())

    async with Client(
        Config(api_key=KEY, model=MODEL), transport=httpx.MockTransport(handle)
    ) as client:
        await client.decide(WORLD)
        assert client.last_telemetry["request_id"] == "chat-1"


@pytest.mark.parametrize("world", [[{"id": "r1"}], {"battery_percent": float("nan")}])
async def test_invalid_world_is_rejected_before_any_network(world):
    Error, Client, Config = cloud_types()
    requests = []

    async def handle(request):
        requests.append(request)
        return httpx.Response(200, json={"data": [{"id": MODEL}]})

    async with Client(
        Config(api_key=KEY, model=MODEL), transport=httpx.MockTransport(handle)
    ) as client:
        with pytest.raises(Error, match="invalid_world"):
            await client.decide(world)
    assert requests == []


async def test_response_body_limit_aborts_stream_without_reading_remainder():
    Error, Client, Config = cloud_types()
    chunks = 0

    class Body(httpx.AsyncByteStream):
        async def __aiter__(self):
            nonlocal chunks
            for _ in range(20):
                chunks += 1
                yield b"x" * 1024

    async def handle(request):
        return httpx.Response(200, stream=Body())

    async with Client(
        Config(api_key=KEY, model=MODEL, max_response_bytes=1024), transport=transport_for(handle)
    ) as client:
        with pytest.raises(Error, match="response_too_large"):
            await client.decide(WORLD)
    assert chunks == 2


async def test_explicit_model_verification_refresh_fails_closed(caplog):
    Error, Client, Config = cloud_types()
    available = True

    async def handle(request):
        return httpx.Response(200, json={"data": [{"id": MODEL}] if available else []})

    caplog.set_level(logging.INFO)
    async with Client(
        Config(api_key=KEY, model=MODEL), transport=httpx.MockTransport(handle)
    ) as client:
        await client.verify_model()
        available = False
        with pytest.raises(Error, match="model_unavailable"):
            await client.verify_model()
        assert client.last_telemetry["status"] == "error"
        assert caplog.records[-1].data["status"] == "error"


async def test_physical_scene_image_uses_verified_model_without_persisting_image(caplog):
    import base64

    from neuravac_core.cloud import PhysicalReasoningConfig, PhysicalReasoningProvider

    image = b"\xff\xd8" + b"private-test-camera-image" * 8
    encoded = base64.b64encode(image).decode()

    async def handle(request):
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "verified-vision-model"}]})
        body = json.loads(request.content)
        content = body["messages"][1]["content"]
        assert '"hazard_score"' in body["messages"][0]["content"]
        assert '"clean_region"' not in body["messages"][0]["content"]
        assert content[1]["image_url"]["url"] == "data:image/jpeg;base64," + encoded
        assert json.loads(content[0]["text"])["location"] == "floor"
        assert "api_key" not in content[0]["text"] or KEY not in content[0]["text"]
        answer = {
            "class_name": "cable",
            "confidence": 0.95,
            "hazard_score": 0.9,
            "traversable": False,
            "reason": "Cable visible on the floor",
        }
        return httpx.Response(
            200, json=completion(json.dumps(answer), model="verified-vision-model")
        )

    caplog.set_level(logging.INFO)
    config = PhysicalReasoningConfig(
        enabled=True,
        completion_url="https://vision.test/completion",
        models_url="https://vision.test/models",
        model="verified-vision-model",
        api_key=KEY,
    )
    async with PhysicalReasoningProvider(config, transport=httpx.MockTransport(handle)) as provider:
        assessment = await provider.assess_scene(
            image, "image/jpeg", {"location": "floor", "api_key": KEY}
        )
        assert assessment.class_name == "cable" and not assessment.traversable
        assert encoded not in json.dumps(provider.last_telemetry) + caplog.text
        assert KEY not in json.dumps(provider.last_telemetry) + caplog.text


@pytest.mark.parametrize(
    "answer",
    [
        {
            "class_name": "cable",
            "confidence": 2,
            "hazard_score": 0.9,
            "traversable": False,
            "reason": "Visible cable",
        },
        {
            "class_name": "unknown",
            "confidence": 0.5,
            "hazard_score": 0.9,
            "traversable": "false",
            "reason": "Uncertain",
        },
        {
            "class_name": "liquid",
            "confidence": 0.9,
            "hazard_score": 0.9,
            "traversable": False,
            "reason": "Wet floor",
            "wheel_pwm": 255,
        },
    ],
)
async def test_physical_scene_assessment_rejects_invalid_schema(answer):
    from neuravac_core.cloud import CloudError, PhysicalReasoningConfig, PhysicalReasoningProvider

    async def handle(request):
        return httpx.Response(
            200, json=completion(json.dumps(answer), model="verified-vision-model")
        )

    async def wrapped(request):
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "verified-vision-model"}]})
        return await handle(request)

    config = PhysicalReasoningConfig(
        enabled=True,
        completion_url="https://vision.test/completion",
        models_url="https://vision.test/models",
        model="verified-vision-model",
        api_key=KEY,
    )
    async with PhysicalReasoningProvider(
        config, transport=httpx.MockTransport(wrapped)
    ) as provider:
        with pytest.raises(CloudError, match="invalid_response"):
            await provider.assess_scene(b"\xff\xd8test", "image/jpeg", {})


async def test_disabled_scene_assessment_and_bad_image_never_make_calls():
    from neuravac_core.cloud import CloudError, PhysicalReasoningProvider

    async with PhysicalReasoningProvider() as provider:
        with pytest.raises(CloudError, match="disabled"):
            await provider.assess_scene(b"image", "image/jpeg", {})

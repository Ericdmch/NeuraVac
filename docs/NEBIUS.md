# Nebius / NVIDIA Nemotron

`neuravac_core.cloud.NebiusClient` performs genuine asynchronous HTTP requests to Nebius Token Factory. Simulation and ordinary tests use no account, network call, or billed inference. Successful mock tests are not evidence of genuine cloud use.

The official [model-list API](https://docs.tokenfactory.nebius.com/api-reference/models/list-models) exposes `GET https://api.tokenfactory.nebius.com/v1/models`. The official [chat API](https://docs.tokenfactory.nebius.com/api-reference/inference/create-chat-completion) documents `POST /v1/chat/completions`, Bearer authentication, response model identity, completion status and numeric token usage.

Nebius's [NVIDIA Nemotron page](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference) documents `nvidia/Nemotron-3_5-Lightning`. This is an example, not a promised entitlement. Nebius's [physical-AI integration guide](https://github.com/nebius/nebius-physical-ai/blob/main/docs/workbench/token-factory.md) also warns that default model IDs are not guaranteed to be available to each key. Availability changes; select an exact NVIDIA Nemotron ID from your authenticated account catalog. The client rejects any model absent from that catalog before sending inference.

## Configure

Supply a Token Factory API key through your protected process environment as `NEBIUS_API_KEY`; it is distinct from a Nebius Cloud IAM token. The application never searches credential files, reads a `.env` file, or prints the key. Set `NEBIUS_MODEL` to the exact account-available NVIDIA Nemotron ID. Configuration refuses empty keys, non-Nemotron IDs, nonfinite timeouts, and HTTP URLs. It also refuses credentials, query parameters and fragments inside endpoint URLs.

| Environment variable | Default | Meaning |
| --- | --- | --- |
| `NEBIUS_API_KEY` | required | Token Factory key; excluded from dumps and representation |
| `NEBIUS_MODEL` | required | Exact account-listed NVIDIA Nemotron ID |
| `NEBIUS_BASE_URL` | `https://api.tokenfactory.nebius.com/v1` | HTTPS API base |
| `NEBIUS_TIMEOUT_S` | `8` | Whole-attempt deadline plus each HTTP I/O deadline |
| `NEBIUS_MAX_RETRIES` | `2` | Additional attempts after 429, 5xx, transport error or timeout |
| `NEBIUS_BACKOFF_S` | `0.25` | Initial exponential retry delay |
| `NEBIUS_MAX_BACKOFF_S` | `2` | Upper bound on each delay, including numeric Retry-After |
| `NEBIUS_MAX_TOKENS` | `512` | Maximum completion budget |

`config/nebius.yaml` is a credential-free reference for constructor settings; the runtime environment loader does not load YAML automatically. Constructor configuration also supports `max_response_bytes`, default 1 MiB. Input world JSON is bounded to 128 KiB. Responses are read in bounded streams. HTTPS certificate verification stays enabled, redirects are refused, and inherited HTTP proxy settings are ignored.

## Use and verify

```python
from neuravac_core.cloud import CloudError, NebiusClient, NebiusConfig

async def advise(world: dict):
    async with NebiusClient(NebiusConfig.from_env()) as client:
        await client.verify_model()  # authenticated discovery; no inference
        try:
            decision = await client.decide(world)
        except CloudError:
            # Mission policy chooses pause or its conservative local planner.
            raise
        return decision, client.last_telemetry.copy()
```

`await client.discover_models()` returns model IDs. `await client.verify_model()` explicitly refreshes availability. `decide()` checks once per client session if verification has not happened. Keep one client for the mission and close it using the context manager or `await client.aclose()`.

The world request contains mission state, battery percentage, dirty regions, hazards and recent changes. Every returned decision must pass the shared Pydantic schema with strict type validation. Extra fields, motor commands, unknown actions, missing target IDs, nonfinite priorities, string priorities and incomplete completions are rejected. JSON fences, duplicate JSON keys and malformed envelopes are rejected. The authoritative world model separately checks target identity, freshness, reachability and safety before any action.

`last_telemetry` contains `status`, configured `model`, sanitized `request_id`, `latency_ms`, numeric `usage`, `error`, attempt count and HTTP status when available. A successful call is `success`; rejected or failed calls are `error`; task cancellation is `cancelled`. Error codes never contain provider bodies or exception details. Prompts, raw completions, images and hidden `reasoning_content` are not logged or retained. A decision's `reason` is a short observable explanation, not hidden reasoning. Request payloads explicitly set `store: false`; provider retention still follows the provider's terms. Retries can incur additional inference cost after a timeout.

## Cloud tests and evidence

Ordinary tests use `httpx.MockTransport` to exercise real client serialization, parsing, retries and telemetry. They cover timeouts, 429/5xx, authentication errors, malformed JSON, extra/motion fields, nonfinite values, private reasoning, cancellation, large responses and optional scene assessment.

```sh
.venv/bin/python -m pytest tests/unit/test_cloud.py
```

A real, potentially billed smoke test requires both credentials and the exact opt-in flag. Load the key securely first, then run:

```sh
NEURAVAC_ALLOW_CLOUD_TESTS=1 .venv/bin/python -m pytest -o addopts= -m cloud tests/cloud --junitxml=/tmp/neuravac-cloud.xml
```

The test skips before credential loading when the flag is absent, and also skips without a key or model. It verifies authenticated model availability, performs real inference, checks strict output and records sanitized telemetry in the JUnit property. Keep that evidence with your runtime recording. A skipped test, offline simulation, documented model ID or fabricated request ID cannot establish genuine cloud use.

## Optional physical scene assessment

`PhysicalReasoningProvider` is disabled by default. No public Nebius physical-reasoning URL or model capability is assumed. Configure an operator-verified OpenAI-compatible vision endpoint that accepts inline images and supports JSON output. Both exact endpoint URLs must have the same HTTPS origin:

| Environment variable | Meaning |
| --- | --- |
| `PHYSICAL_REASONING_ENABLED=1` | Explicitly enable remote assessment |
| `PHYSICAL_REASONING_COMPLETION_URL` | Exact chat-completion URL; no path is appended |
| `PHYSICAL_REASONING_MODELS_URL` | Exact model-list URL; no path is appended |
| `PHYSICAL_REASONING_MODEL` | Exact verified vision model ID |
| `PHYSICAL_REASONING_API_KEY` | Key for the configured endpoint |

Construct it with `PhysicalReasoningConfig.from_env()`. `await provider.assess_scene(image_bytes, mime_type, context)` returns strict `HazardAssessment(class_name, confidence, hazard_score, traversable, reason)`. JPEG, PNG and WebP bytes are limited to 4 MiB. The provider checks that its configured model is account-listed before sending a frame. Model-list membership alone cannot establish vision capability; the operator must verify the endpoint's documented image and JSON contracts. Assessment is advisory and cannot certify the whole scene clear, calibrate floor geometry, establish cleaning success or override local safety. Raw images and base64 payloads are not logged or stored by the provider. It also supports `decide(world)` with the same strict high-level Decision contract.

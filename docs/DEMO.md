# NeuraVac demonstration

Run `make demo` for a repeatable two-target simulation, then `make dashboard` and press Start for the live visualization. Offline mode remains labeled offline. Supply Nebius environment variables and run `.venv/bin/python -m neuravac_core.cli dashboard --cloud` for actual Nemotron decisions. Record model ID/request latency; do not edit offline logs to imply cloud calls.

##≤3minute hardware video

| Time | Shot |
|---|---|
|0:00–0:20|Problem: geometric coverage doesn't prove cleaning|
|0:20–0:40|NeuraVac: perceive, understand, act, verify|
|0:40–1:50|Continuous genuine hardware operation: detect debris and cable, select target, drive safely, activate vacuum|
|1:50–2:15|Move a chair; show detection, changed path and cable avoidance while robot remains visible|
|2:15–2:35|Close-up BEFORE/AFTER floor observations and a retry caused by remaining debris|
|2:35–2:50|Architecture and dashboard showing actual Nebius/Nemotron request metadata|
|2:50–3:00|Result and long-term household-robot impact|

This outline allocates more than a minute to visible physical robot operation. Simulation may explain architecture but cannot replace the robot footage for this hardware project. Do not film a floor trial until HARDWARE.md safety bringup passes.

## Showcase evidence

The deterministic room has two labeled dirt clusters, a cable and a movable chair. First-pass residual debris forces a second pass. Moving the chair into the next route invalidates it and triggers replanning. The simulator checks the full robot footprint against hazards. SQLite and JSONL contain scores/pass counts/events. Demo assertions are in tests/scenarios/test_closed_loop.py. Dashboard camera previews are explicitly labeled simulated.

For a physical mission, stage a supervised bounded room, record a genuine camera/LiDAR bag, trigger Start explicitly and retain fresh before/after observations. Label any unsupported real-world scene as unknown and request inspection. Never hide a failed stop or incomplete verification in the submitted video.

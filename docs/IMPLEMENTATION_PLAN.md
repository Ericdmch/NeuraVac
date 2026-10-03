# NeuraVac implementation plan

Goal: deliver the user's complete physical-AI loop with testable hardware and cloud boundaries.
Architecture: a shared Python core, ROS 2 Jazzy adapters, deterministic simulator, and static React dashboard. Safety is local; cloud decisions are advisory high-level actions.
Spec: ARCHITECTURE.md and the user's full NeuraVac requirements.

Global constraints: Pi 4 CPU-only; 500 ms configurable watchdog; explicit mission start after reboot; no hardware or billed cloud tests in ordinary CI; strict schemas; honest unknown perception; no credentials in recordings; Nav2 for production routes.
Review focus: startup without sensors, stale commands during cloud requests, serial partial reads/disconnect, targets invalidated by hazards, observation failure during verification.

Each milestone follows: add behavioral tests, observe failure, implement, run the full available suite, record evidence below. No automatic commits or publishing are needed to make the repository reviewable.

- [x] 1. Foundation: `config/`, schemas, structured logs, mock base, packaging and CI. Validate bad YAML, finite values, mock shutdown and redaction with `pytest tests/unit`.
- [x] 2. Simulation: differential-drive motion, footprint collisions, safety, arbitration and mission states. Inject all safety faults and expired commands.
- [x] 3. OI layer: tested binary codec, fake serial, capability-dependent odometry and MCU transport; explicit gated hardware tests.
- [x] 4. ROS: node packages, odometry and transforms, Nav2 action adapter, semantic keepout mask, SLAM and all launch modes; validate in Jazzy CI.
- [x] 5. Perception: camera, replay, ONNX, remote providers; FloorMess collection/splits/labels/export/evaluation; synthetic and missing-model tests.
- [x] 6. Semantics: calibrated floor projection, tracking, decay, debris grouping, authoritative world snapshot; association and hazards tests.
- [x] 7. Cleaning: before/after observations, retry budget, safe actuator shutdown, dynamic route replanning, SQLite summaries and replay; run definition-of-done scenario.
- [x] 8. Nebius: bounded HTTP client, model discovery, strict Nemotron decisions, telemetry and optional physical reasoner. Mock timeouts/500/malformed JSON; gate real cloud test.
- [x] 9. Dashboard: FastAPI and bounded WebSockets, explicit controls, polished static React map/status/metrics/reasoning/camera. API, frontend tests, lint and production build.
- [x] 10. Delivery: Pi install/systemd, scripts and Make UX, CI, source references, benchmark, README, video outline and genuine-feedback template. Re-run complete checks and fresh review.

## Verification ledger

Repository inspected: only initial README; no AGENTS.md or implementation. Host has Python 3.14 and Node 22, no ROS installation. Use a Python 3.12 environment for deployment-compatible checks.

Milestones 1–10 implementation delivered. “Checked” means repository implementation and available local checks, not physical/cloud/ROS deployment certification. The original requirements remain the acceptance brief.

2026-10-01 verification: independent reviews reproduced serial sensor-timeout stop suppression, expired unresolved dirt, repeated camera timestamps, unbounded actuator history, remote vision deadlines, ROS velocity routing/calibration/interpreter/origin issues. Regression tests were observed failing and then passing after fixes. No reviewer findings were silently discarded. Fresh clear-floor polygon evidence reconciles absence; an empty image response does not. Rank weights and deployment thresholds are typed YAML.

Local evidence: Python core type checks; full ordinary Python suite; strict frontend lint/tests/build; deterministic demo COMPLETE with two verified targets, two retries, cable avoidance and moved-chair replanning; recorded replay; package wheel build; shell syntax/adapter compilation; source secret audit. Full output retained under ignored artifacts/. ROS contract checks run locally; live ROS tests and physical/billed tests are skipped behind their explicit requirements.

Final clean-install check: 150 ordinary Python tests pass on Python 3.11 and 3.12; 20 frontend tests pass. The source audit reports zero findings across 207 files. OpenCV is included in development dependencies so video-extraction tests run in a fresh environment.

Outstanding deployment evidence: Jazzy/Nav2 runtime CI, donor sensor/actuator/power-loss validation, FloorMess trained checkpoint and calibrated clear-floor accuracy, real ONNX export/ARM64 runtime and Pi thermal profiling, account-verified real Nebius mission, public repository/video and genuine tooling feedback. No Docker daemon is running on this host, so no local Jazzy container validation was claimed.

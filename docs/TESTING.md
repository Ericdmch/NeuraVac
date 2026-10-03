# Testing and validation status

`make check` runs Python lint/format/type checks, all ordinary tests, frontend ESLint/Vitest/build and the source secret audit. CI repeats Python checks on 3.11/3.12 and builds frontend static assets. The separate Jazzy workflow builds ROS packages and exercises ROS simulation contracts on Ubuntu without physical equipment.

## Ordinary checks

Unit tests cover typed YAML, finite schemas, OI known bytes/signed data, encoder wrap/arc motion, semantic tracking/clustering/expiry, hazard rejection, transition legality, cloud strict output/deadline/retry, model availability, floor projection, provider contracts, grouped FloorMess splits, label validation, and measured metrics.

Fake-device integration covers serial partial reads, missing response bytes, sensor disconnect, actuator stop, MCU watchdog negotiation, independent driver expiry, dashboard API/auth/controls, SQLite attempts and replay without actuators.

Scenarios cover two debris targets, cable avoidance, first-pass failure followed by successful retry, chair movement and replanning, pause/resume, low confidence clothing and unknowns, bumper/cliff/serial/camera/LiDAR/heartbeat/battery faults, pending cloud inference while safety remains live, cloud timeout/malformed/unsafe-target fallback and pause policy. Stale unresolved dirt remains pending until fresh inspection.

Run groups with `make test-unit`, `make test-integration`, `make test-scenarios`. `make demo` produces inspectable outcome evidence and `make replay` rebuilds semantics from recorded observations. Seeded simulator sensors and routes make repeated results reproducible. Simulator truth labels are explicitly marked simulated_camera; no real inference accuracy is inferred from them.

## Opt-in validation

Final local verification: 150 ordinary Python tests pass on both Python 3.11 and 3.12; 20 frontend tests pass. Python lint, format and type checks, frontend lint and production build, wheel packaging, deterministic demo/replay and the secret audit pass. Six ROS contract tests run in the ordinary suite; two live ROS test modules skip because this host has no `rclpy`. The clean development install includes the OpenCV dependency required by the video-extraction test.

The implemented ordinary suite passes locally. One upstream Starlette/AnyIO deprecation warning is present; it does not affect test outcomes. Default pytest excludes hardware and cloud. `NEURAVAC_ALLOW_HARDWARE_TESTS=1 NEURAVAC_SERIAL_PORT=<port> make test-hardware` opens the actual donor; movement additionally needs `NEURAVAC_WHEELS_ELEVATED=1`. `NEURAVAC_ALLOW_CLOUD_TESTS=1 make test-cloud` requires actual NEBIUS_API_KEY and NEBIUS_MODEL. Ordinary CI never invokes billed cloud or physical motors.

External validation outstanding: ROS Jazzy runtime/container workflow execution, actual donor wheels/sensor capabilities, power-loss stop, calibrated camera projection, trained detector accuracy/cable recall, ONNX export with a real checkpoint, ARM64 ONNX execution/latency, Pi thermals and scheduler behavior, real Nebius access/model availability and measured feedback. A saved local launch file or a mocked successful response does not prove these.

## Benchmarks

`python tools/benchmark_pi.py --duration 10` measures the installed core on the current host. Optional camera/model/cloud flags exercise supplied resources. Null fields mean unavailable/not measured. The current host is macOS ARM64, not a Raspberry Pi; do not present its numbers as Pi performance. See PERFORMANCE.md.

## Recording

JSONL stores monotonic timestamps, observations, commands, sensor state, world snapshots, events and redacted decisions; camera images are not fabricated. For ROS, `NEURAVAC_RECORD_ROS=1 ./scripts/start_recording.sh` records rosbag2 topics including camera/LiDAR. JSONL replay creates no base object. ROS replay uses a separate domain99 by default and should run with production base processes stopped. Raw model hidden reasoning and credentials are never persisted.

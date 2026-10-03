# Deterministic safety

Safety has no cloud dependency. Emergency > safety > manual > navigation > idle. All command sources pass through one arbiter; the base driver independently checks limits, expiry and command heartbeat. Default watchdog500ms, control20Hz. Every actuator stop includes vacuum and brush shutdown.

Missing/future/stale base, LiDAR, camera or mission heartbeat prevents motion. Bumper, cliff, wheel drop, serial failure, critical battery and excessive current inhibit motion. The emergency stop latches; reset requires healthy sensors and an explicit action. Sensor faults put the mission in FAULT; restoring a camera alone does not restart motion. Mission start and resume are explicit. Base reconnect/reboot must default to IDLE.

OI uses Safe mode, never Full mode. Cliff/wheel-drop protections remain on the donor. Sensor read failures still attempt zero wheel speeds and cleaning-motors OFF through an open serial transport, even when sensor health has failed. Failed write delivery is surfaced; software cannot deliver a serial command over a broken wire. Pi process death/power loss can prevent host watchdog action, so deployment needs a physical cutoff and an independently enforced MCU/robot watchdog. Linux/Python scheduling is not a hard real-time guarantee.

Low-confidence clothing, paper, liquids, shoes and unknowns are possessions/hazards; only sufficiently confident debris is vacuumable. Hazard footprints expand before routing. Expiring tracks never erase unresolved dirt evidence. Cleaning success requires fresh target observations; missing/occluded AFTER data never means a zero score. Exhausted retry budgets and unreachable regions request inspection rather than COMPLETE.

The cloud can suggest strict high-level tasks only. Local validation rejects stale/missing/prohibited targets and premature finish. Slow requests remain outside the control loop; timeouts and malformed replies pause or use deterministic safe ranking. No freeform model text is executed, and hidden model reasoning is not shown.

Default dashboard binding is localhost. Remote binding requires a token, and every state/control/history/camera endpoint is guarded when configured. WebSocket authentication uses a first message so credentials do not enter URL logs. Use an authenticated encrypted tunnel for remote access. ROS itself is trusted-local communication here; configure SROS2/enclave policy before exposing its network outside the robot's controlled LAN.

Fault evidence: tests/unit/test_safety.py, tests/scenarios/test_closed_loop.py, tests/scenarios/test_cloud_fallback.py, tests/integration/test_serial_base.py. Physical safety validation remains mandatory before floor operation.

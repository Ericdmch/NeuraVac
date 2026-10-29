# Autonomous mapping: staged implementation and verification

The autonomous mapping components are experimental. On 2026-10-29 they were
installed on the Pi, with autonomous motion disabled and no physical driving
test. The Pi's existing source and maps were backed up at
`~/neuravac-backups/autonomy-20261029-170738/`; the live legacy map at the
switch was saved separately as `room-at-switch.npz` in that directory.
The legacy mapper service was disabled and replaced by SLAM Toolbox.

The Pi runs `neuravac-toolbox.service` and `neuravac-autonomy.service` as
enabled user services. The latter starts with `enable_motion:=false`. The
operator page is available on the Pi's Tailscale address at port 5050. The
existing dashboard remains on port 5000. SLAM Toolbox starts a fresh map; the
legacy map is not imported as a Toolbox pose graph.

## What is implemented

- `autonomy_node` selects reachable frontiers in the complete SLAM grid, sends
  Nav2 goals, and returns to a selected reachable map-frame point. It stops and
  waits when the return is unreachable, navigation repeatedly fails, a goal
  times out, or the driver reports a fault. Route searches run outside the ROS
  callback thread. The node defaults to `enable_motion:=false`.
- `driver_watchdog` is an extension running inside the existing
  Pi Roomba serial owner. It uses fresh Roomba group-0 data, LiDAR, localization
  and odometry, and a short command lease; bumper, wheel drop, cliff, virtual
  wall, overcurrent, charging, stale input, and manual preemption latch a stop.
  The applied change to the Pi's exact source is
  `src/neuravac_mapping/deployment/patches/pi-roomba-watchdog.patch`.
- `autonomy.launch.py` starts the Nav2 planner, controller, no-recovery behavior
  tree, coordinator and an operator page. Its motion flag remains false by
  default. The Pi service binds the page to its Tailscale address; the code's
  default when run separately is localhost:5050.
- The operator page displays the SLAM map, permits selecting a known free cell,
  and offers start, end-and-return, and stop-and-wait commands. Requests are
  asynchronous; the displayed coordinator state indicates acceptance or refusal.

## Evidence and limits

The Pi's isolated ROS domain 87 ran the Nav2 stack against a synthetic map,
TF, odometry, LiDAR and a fake serial port. The fake robot moved toward a
frontier and returned to the selected point. A second test injected a bumper
and observed a zero drive command, cancellation and a latched bumper reason.
The operator page returned the synthetic map, pose and mission state. These
checks did not move or communicate with the physical Roomba.

One simulated run experienced an autonomous command timeout under load and
stopped; other runs completed. Timer scheduling gaps were observed during Pi
startup. The cause of the intermittent timeout has not been established, so the
0.3-second command lease was not relaxed. Further testing must characterize
latency with the actual camera, SLAM, dashboard and ROS processes active.

The watchdog is in the serial owner process: it stops when the coordinator
fails, but it cannot guarantee a stop if the serial owner, operating system,
USB link, or power itself fails after a drive command. An independent physical
or firmware-level motor timeout/interlock must be established before unattended
operation. LiDAR coverage, robot footprint, velocity, braking distance, bumper,
cliff and wheel-drop behavior still require supervised physical validation.
The tests cannot establish that a map is physically accurate, that Nav2 can
successfully navigate the real room, or that the robot can return home.

## Supervised physical calibration and verification (2026-10-29)

Supervised low-speed physical tests were conducted on the Pi (`100.106.145.39`)
with `enable_motion` temporarily enabled only during bounded runs and restored
to `false` (`disarm` called) immediately afterward:

1. **LiDAR mounting yaw calibration (`mapping.launch.py`):**
   - A 1.0 s straight-forward command (`linear.x = 0.08 m/s`, `odom_move_m = 0.0842 m`)
     showed mean range changes of `-0.0782 m` at `-90°` in `lidar_link` and
     `+0.0817 m` at `+90°` in `lidar_link`, confirming that `-90°` in `lidar_link`
     points forward (`+X` in `base_link`).
   - Updated `lidar_yaw_rad` default in `mapping.launch.py` from `0.0` to
     `1.5707963267948966` (`+pi/2` rad). This eliminated the 90° disagreement
     between wheel odometry and LiDAR scan matching during translation (`map -> odom`
     drift dropped from ~47 cm to `1.6 cm` over a 21 cm turn-and-drive).
2. **SLAM Toolbox free-space raytracing (`toolbox.yaml`):**
   - Reduced `min_pass_through` from `2` to `1` so rays passing once through a
     cell clear it to `0` (`free`) rather than leaving `-1` (`unknown`) speckles
     that block frontier BFS and `NavfnPlanner`.
3. **Nav2 goal tolerance, minimum velocity, and clearance alignment (`autonomy_nav2.yaml`, `autonomy_node.py`):**
   - Set `general_goal_checker.yaw_goal_tolerance: 3.15` and `xy_goal_tolerance: 0.15`
     so 2D `(x, y)` frontier and return goals succeed upon entering `0.15 m`
     without spinning in place to `yaw = 0.0`.
   - Set `FollowPath.min_approach_linear_velocity: 0.05` and
     `regulated_linear_scaling_min_speed: 0.05` so approach and curve velocities
     remain above the Roomba's `0.0285 m/s` wheel speed step.
   - Aligned obstacle clearance across all three layers:
     - `driver_watchdog` hard LiDAR stop threshold: `0.25 m` (`5.0` cells).
     - `local_costmap` and `global_costmap` `robot_radius`: `0.255 m` (`5.1` cells,
       `inflation_radius: 0.45 m`) with `GridBased.tolerance: 0.15 m`.
     - `autonomy_node` `clearance_m`: `0.30 m` (`6` cells), keeping selected
       frontier goals outside the costmap's `99` inscribed ring and well outside
       the watchdog's `0.25 m` tripwire.
4. **Physical supervised mission runs verified:**
   - **Multi-frontier chaining + 1.29 m return-to-origin:** Starting at
     `[1.040, -1.150]` with `return_goal: [1.912, -0.968]`, the robot armed,
     navigated to Frontier #1 (`[0.624, -1.123]`), automatically chained to
     Frontier #2 (`[-0.156, -1.080]`), accepted `command: "return"`, drove
     `1.29 m` back across the room around obstacles to `[1.780, -0.919]`
     (`0.141 m <= 0.15 m` of `return_goal`), disarmed (`armed: false`), and
     finished with `state: "complete"`, `reason: "Returned to selected spot"`.
   - **Watchdog proximity stop:** Confirmed that when a LiDAR return reaches
     `0.250 m`, `driver_watchdog` immediately disarms and halts the mission with
     `Driver watchdog stopped: scan invalid; waiting for operator`.
   - **Operator stop:** Confirmed that `POST /api/mission {"command": "stop"}`
     during active exploration immediately cancels navigation, disarms the
     watchdog (`armed: false`), and transitions to `state: "stopped"`,
     `reason: "operator stop"`.
   - All 61 unit and isolated ROS tests (`ROS_DOMAIN_ID=55`) pass on the Pi.

## Remaining limits before unattended operation

1. The watchdog runs in the serial owner process: it stops when the coordinator
   fails, but it cannot guarantee a stop if the serial owner, operating system,
   USB link, or power itself fails after a drive command. An independent physical
   or firmware-level motor timeout/interlock must be established before unattended
   operation.
2. Keep `enable_motion:=false` by default in `neuravac-autonomy.service` and
   supervise all physical runs. Keep cloud advice outside the motor path.

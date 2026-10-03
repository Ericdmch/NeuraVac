# ROS 2 Jazzy runtime

The adapters under `ros2_ws/src` are ten connected `ament_python` packages. ROS 2 Jazzy on Ubuntu 24.04 supplies `rclpy`, Nav2, TF, standard messages, and slam_toolbox; the repository's Python package supplies the shared typed configuration and safety/semantics/cleaning/cloud logic. The macOS development host does not have ROS installed. Local contract and syntax checks cannot validate Nav2 activation, DDS timing, serial hardware, camera calibration, or a complete ROS mission. The separate Jazzy workflow builds and runs live transport and Nav2 mission tests; inspect its actual results before claiming ROS runtime validation.

## Build and run

On Ubuntu 24.04 with ROS 2 Jazzy installed:

```bash
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox ros-jazzy-usb-cam python3-colcon-common-extensions python3-venv
source /opt/ros/jazzy/setup.bash
python3 -m venv --system-site-packages .venv-ros
source .venv-ros/bin/activate
pip install -e '.[dev,hardware,vision]'
python /usr/bin/colcon build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install
source ros2_ws/install/setup.bash
ros2 launch neuravac_bringup bringup.launch.py mode:=simulation dashboard:=false
```

The labeled simulator uses `SimRobotBase` for encoder/motor physics and physical removal of dirt, publishes a known occupancy map, laser scans, synthetic black camera frames, and honest `simulated_camera` object labels including zero-score debris. Nav2 executes all routes; the deterministic CI grid planner is not used by this launch. The synthetic RGB image is not a trained detector or a rendered hardware camera. Wall-clock ROS time is used by this lightweight simulator; `use_sim_time` remains false because it does not publish `/clock`.

Self-test waits for fresh base, lidar, image, perception/world and safety observations and an available Nav2 action server. The mission then stays IDLE. Start explicitly:

```bash
ros2 service call /mission/start std_srvs/srv/Trigger '{}'
ros2 service call /mission/pause std_srvs/srv/Trigger '{}'
ros2 service call /mission/resume std_srvs/srv/Trigger '{}'
ros2 service call /mission/return_home std_srvs/srv/Trigger '{}'
ros2 service call /emergency_stop std_srvs/srv/Trigger '{}'
ros2 service call /safety/reset std_srvs/srv/Trigger '{}'
```

`simulation.launch.py` and `demo.launch.py` select the labeled simulation. `hardware.launch.py`, `mapping.launch.py` and `saved_map.launch.py` select physical operation; no physical process is launched by ordinary tests. Direct `bringup.launch.py` exposes all parameters.

For hardware, first configure the shared robot YAML and validate wheel direction, battery/cliff/wheel-drop/current packets, hardware stop and calibrated sensor transforms with wheels raised. The physical launch rejects `mock`/`sim` backends:

```bash
ros2 launch neuravac_bringup bringup.launch.py mode:=hardware mapping:=true backend:=roomba_oi robot_config:=/absolute/path/robot.yaml perception_config:=/absolute/path/perception.yaml provider:=onnx lidar_launch:=/absolute/path/lidar.launch.py start_camera:=true
# After saving a map:
ros2 launch neuravac_bringup bringup.launch.py mode:=hardware backend:=mcu_bridge map:=/absolute/path/map.yaml robot_config:=/absolute/path/robot.yaml perception_config:=/absolute/path/perception.yaml provider:=onnx lidar_launch:=/absolute/path/lidar.launch.py start_camera:=true
```

Saved-map operation includes Nav2 AMCL and requires a measured initial pose on `/initialpose`. Mapping includes `slam_toolbox/online_async_launch.py`. The donor's encoders must be supported; a missing encoder packet causes the driver to stop and suppress odometry. External odometry adapters for encoderless donors are not included. The lidar driver is supplied explicitly via `lidar_launch` and must publish `/scan` in `laser_frame`. Camera startup is optional because deployments may supply a different ROS camera driver. The image topic is `/camera/image_raw` with RGB/BGR8 encoding. Measure and replace `laser_x`, `laser_z`, `camera_x`, `camera_z` and the camera calibration; the sample offsets are placeholders.

## Transport contracts

JSON carried by `std_msgs/String` is a bounded strict envelope:

```json
{"schema_version":1,"kind":"detections","stamp":123.5,"frame_id":"map","payload":{"available":true,"detections":[]}}
```

Envelope stamps use ROS seconds, and all semantic coordinates are map-frame meters. Nodes reject unsupported versions, duplicate keys, stale/future stamps and nonfinite JSON. Freshness is checked again downstream; republishing a snapshot cannot refresh its `observed_at`. An unavailable observation uses `available:false` and a reason; it cannot become an empty clean-floor observation. Safety translates source age to process monotonic time for the shared monitor. Unstamped `Twist` commands use local receipt time and a 500 ms deadline by default. This local DDS command interface must remain on a trusted robot network; DDS security is not configured here.

| Topic | Type | Publisher → consumer |
|---|---|---|
| `/nav/cmd_vel` | `geometry_msgs/Twist` | Nav2 → safety arbiter |
| `/manual/cmd_vel` | `geometry_msgs/Twist` | explicit operator tool → safety arbiter |
| `/cmd_vel` | `geometry_msgs/Twist` | safety arbiter → base driver only |
| `/mission/cleaning_cmd` | `std_msgs/String`, `cleaning_command` | cleaning verifier → arbiter |
| `/base/vacuum_cmd` | `std_msgs/String`, `vacuum` | arbiter → base driver only |
| `/base/status` | `std_msgs/String`, `base` | fresh connected/battery/bumper/cliff/encoder health → safety/world |
| `/battery_state`, `/base/battery` | `sensor_msgs/BatteryState` | base → telemetry |
| `/base/encoders` | `sensor_msgs/JointState` | measured wheel encoder positions → telemetry |
| `/base/bumper`, `/base/cliff` | `std_msgs/Bool` | derived sensor flags → telemetry |
| `/odom`, `/tf` | `nav_msgs/Odometry`, TF | measured encoder integration, odom → base_link |
| `/scan` | `sensor_msgs/LaserScan` | lidar or simulator → safety/SLAM/Nav2 |
| `/camera/image_raw` | `sensor_msgs/Image` | camera or simulator → safety/perception/dashboard |
| `/perception/detections` | `std_msgs/String`, `detections` | inference → mapper |
| `/semantic_map` | `std_msgs/String`, `semantic_map` | tracker snapshot → world model |
| `/debris_regions`, `/hazards` | `std_msgs/String` | semantic mapper → observers |
| `/semantic_keepout` | `nav_msgs/OccupancyGrid` | expanded hazards → both Nav2 costmaps |
| `/semantic_filter_info` | `nav2_msgs/CostmapFilterInfo` | lifecycle-managed filter info server → KeepoutFilter |
| `/world_model` | `std_msgs/String`, `world_model` | validated world with availability/base/safety → planner/cleaning/dashboard |
| `/mission/heartbeat`, `/mission_state` | `std_msgs/String` | planner → safety/dashboard |
| `/cloud/request`, `/cloud/result`, `/ai_decisions` | `std_msgs/String` | planner ↔ optional reasoning worker; sanitized telemetry |
| `/cleaning/request`, `/cleaning/cancel`, `/cleaning/result` | `std_msgs/String` | planner ↔ fresh-observation cleaning worker |

The arbiter runs at 20 Hz and the base at the typed `control_hz` (at least 10 Hz). Emergency > safety > manual > navigation > idle priority comes from the shared core. Cleaning commands expire independently. Stationary cleaning inhibits navigation velocity while its fresh motor request is active. A separate asynchronous base-local watchdog stops wheels and cleaning motors when arbiter output expires. Emergency-stop is latched; reset fails until every required sensor and mission heartbeat is healthy. A driver IO error or missing encoders closes the base and requires restarting/reconnecting after diagnosis. Physical stop and MCU watchdog remain necessary for Pi power failure.

## Perception, navigation, verification and cloud

Perception holds a single newest Image slot; inference/HTTP runs on a persistent asyncio worker thread. `onnx` needs explicitly supplied compatible weights; `remote` needs explicit same-origin health/model verification; `replay` needs an explicit `replay_path` and timestamp-matched recordings. Mock inference is only enabled through labeled `sim` input. Bbox detections require the configured intrinsics, rigid camera-to-robot extrinsics and image-time map/base TF before projection to floor coordinates. Missing weights, missing calibration, failed projection or missing TF yields unavailable observations. A deployed replay with preprojected coordinates must declare its source as `replay` and use matching ROS timestamps.

The semantic mapper clusters only confidently identified debris, tracks hazards and rasterizes conservative circles around hazard polygons, expanded by the robot radius plus semantic margin. Occupancy geometry comes from `/map`; rotated map origins are rejected. Both costmaps subscribe to the KeepoutFilter and to laser obstacles. The launch merges `config/navigation.yaml` overrides onto the installed Jazzy Nav2 defaults, then derives robot radius and velocity caps from the same typed config. This accommodates servers present in the installed Jazzy release. The controller→velocity-smoother→collision-monitor chain retains its internal topics. The final collision-monitor output is `/nav/cmd_vel`; a node-scoped docking-server remap also routes through the arbiter. Broad global cmd_vel remapping is deliberately avoided because it can override Nav2 internal remappings. `enable_stamped_cmd_vel:false` keeps this adapter's `Twist` contract explicit. Reference: [Jazzy velocity smoother](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/configuring_velocity_smoother/), [Jazzy navigation launch](https://api.nav2.org/nav2-jazzy/html/navigation__launch_8py_source.html), [KeepoutFilter](https://api.nav2.org/nav2-jazzy/html/classnav2__costmap__2d_1_1KeepoutFilter.html).

Mission controls dispatch `NavigateToPose`. A safety inhibit pauses and cancels; a changed hazard snapshot cancels and replans. An unreachable target is excluded and remains unresolved. Cleaning waits for a new BEFORE observation after arrival, runs a bounded motor pass, stops, then requires a new AFTER observation of every tracked target object. The shared `evaluate_pass`/`should_retry` config determines success and bounded retry. Missing/disappeared target or failed perception never counts as clean. Low return-battery threshold dispatches Nav2 to the measured startup map pose, or pauses if that pose is unavailable or unsafe. Arrival pauses for human charging assistance; autonomous docking and an unobserved global floor-coverage claim are not implemented.

Set `cloud_enabled:=true` only with `NEBIUS_API_KEY` and an explicitly selected `NEBIUS_MODEL`. The cloud node calls shared `NebiusClient` in its worker, verifies model availability, validates strict response schemas, and publishes sanitized telemetry. The planner validates every decision against the current world. Errors, unavailable configuration and elapsed planning deadline select conservative local planning. Late cloud responses are ignored. ONNX debris scores use the core bbox-area/confidence proxy. Fresh confidently observed clean-floor polygons are projected from all four bbox corners and may reconcile previously detected debris through the shared world model; an empty frame does not prove regional cleanliness. Tune the proxy threshold against real detector data before deployment.

No credentials are embedded in YAML or ROS topics; no cloud/runtime evidence is fabricated.

## Dashboard bridge

Enable `dashboard:=true static_dir:=/absolute/path/dashboard/frontend/dist` after building the React assets. The ROS bridge serves `/api/state`, `/api/health`, `/api/mission/{start,pause,resume,estop,reset}`, `/api/camera`, and `/ws` at `127.0.0.1:8000`. It subscribes to actual ROS world/mission/safety/cloud/cleaning/image/map/path messages and calls ROS Trigger services; it does not instantiate the standalone Python simulation backend. Camera PNG encoding needs Pillow. `/api/demo/move-chair` calls the simulator's `/sim/move_chair` service. The bridge writes actual mission transitions, cleaning regions/attempts, changed safety status and sanitized AI decisions to SQLite through the shared MissionStore; its database defaults to `artifacts/ros-missions.db`. rosbag recording remains a separate deployment step. Unknown metrics are omitted. Remote binding requires `NEURAVAC_API_TOKEN`, with HTTP Bearer and first-WebSocket-message token authentication. A stale ROS world sets `connected:false`.

## Verification

Without ROS: `pytest tests/unit/test_ros_contracts.py` validates the pure codecs, conservative keepouts, package manifests, launch wiring and publisher ownership. With Jazzy: `python /usr/bin/colcon test` runs real DDS safety command, dead-heartbeat, emergency latch/reset tests and a real-Nav2 labeled simulation mission with fresh BEFORE/AFTER cleaning. The GitHub workflow contains those commands, but has not been executed by the macOS editor session. Physical motion, actual camera detection accuracy, timing on Pi 4, network cloud access, calibration and real environment behavior require explicit deployment testing.

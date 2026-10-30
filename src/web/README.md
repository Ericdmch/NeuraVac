# ROS dashboard with USB camera

`web_node` serves serial controls, LiDAR, and a live USB camera panel on port
5000. Camera capture is shared across viewers. The browser requests a fresh
JPEG up to five times per second; unavailable or stale frames show OFFLINE
and reconnect automatically. This feed shows the raw camera image.

The dashboard polls Roomba 680 OI group 0 and wheel encoders 43/44 together
(`149 3 0 43 44`, 30-byte response) at up to 20 Hz via the
existing `serial_tx` / `serial_rx` ROS topics. `/telemetry` returns battery,
charging, current, temperature, bumpers, cliffs, wheel drops, wall flags,
overcurrent, and incremental distance/turn readings. Replies are accumulated
across serial chunks; incomplete, invalid, or late responses are ignored.
Readings older than two seconds are hidden rather than shown as current.
The web node owns sensor queries; avoid manually sending sensor-query or
stream commands through the raw console while it is polling.

Protocol references: `docs/Roomba/Roomba_SCI_manual.md` confirms the basic
26-byte layout, flags, and battery units. That document is the 2005 SCI
specification, which predates the 680. For 600-series differences (angle in
degrees, one dirt detector, no caster wheel-drop field), use iRobot's
[600-series/Create 2 OI specification](https://cdn-shop.adafruit.com/datasheets/create_2_Open_Interface_Spec.pdf).
Distance and angle are raw incremental robot reports, not calibrated odometry.

On the Pi, install `python3-opencv`, or use a virtual environment with system
packages enabled and install `opencv-python-headless` there. Flask and the
ROS 2 Jazzy packages must be available to the same Python interpreter.

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Neuravac
colcon build --packages-select web --symlink-install
source install/setup.bash
~/neuravac-web-venv/bin/python -c 'from web.web_node import main; main()'
```

Camera defaults: `/dev/neuravac_camera` (see `src/bringup/README.md`), 1920×1080, MJPEG capture. Override with
`NEURAVAC_CAMERA_DEVICE`, `NEURAVAC_CAMERA_WIDTH`, and
`NEURAVAC_CAMERA_HEIGHT` environment variables before starting the node.
Only one process should own the camera device. Set `NEURAVAC_CAMERA_SOURCE=ros`
to show the frames a running vision node publishes on `camera/image/compressed`
(`NEURAVAC_CAMERA_TOPIC` overrides the topic) instead of opening the webcam;
`ros2 launch bringup robot.launch.py` does this automatically.

Verification (with ROS messages built and sourced):

```bash
PYTHONPATH=src/web:$PYTHONPATH python3 -m unittest discover -s src/web/tests
curl -f http://localhost:5000/camera/frame -o /tmp/camera.jpg
```

The Pi deployment made on October 24 uses `~/neuravac-web-venv`, writes its
output to `~/neuravac-web-camera.log`, and runs until stopped or the Pi
reboots. It is not configured to start on boot.

`NEURAVAC_WEB_ROOT` can point to a directory containing `templates` and
`static` when running a frozen dashboard release independently of ROS's
installed asset directory.

The telemetry deployment runs from `~/neuravac-dashboard/20261024-telemetry`
to avoid concurrent checkout edits replacing the running version. The Pi's
checkout was also restored to the camera, speed-control, and telemetry code.
To restart that deployed release after stopping the existing web process:

```bash
source /opt/ros/jazzy/setup.bash
source ~/Neuravac/install/setup.bash
export PYTHONPATH="$HOME/neuravac-dashboard/20261024-telemetry:$PYTHONPATH"
export NEURAVAC_WEB_ROOT="$HOME/neuravac-dashboard/20261024-telemetry/web"
~/neuravac-web-venv/bin/python -c 'from web.web_node import main; main()'
```

## Motion-compensated LiDAR display

The previous display overlaid 0.5 seconds of robot-relative returns as if the
robot were stationary. The live ROS dashboard now integrates measured wheel
encoder differences (including 16-bit rollover), interpolates poses at point
receipt times, and transforms recent returns into the latest robot frame.
D6 clockwise angles are converted to counterclockwise robot coordinates.
Forward is up on the canvas. Zero-distance returns are discarded.

Only points bracketed by encoder feedback are shown; new points wait for the
next encoder reply. A feedback gap over 250 ms resets the short pose history,
so missing feedback produces an empty scan rather than falsely aligned walls.
The group-0 distance/angle fields remain raw telemetry and are not used for
alignment: the 600-series spec lists firmware bugs in these packets.

Calibration environment variables (set before starting the web node):

- `NEURAVAC_MM_PER_TICK`: defaults to pi * 72 / 508.8 from the OI spec.
- `NEURAVAC_WHEELBASE_MM`: defaults to 235; a nominal starting estimate to
  calibrate against measured rotation on this robot.
- `NEURAVAC_LIDAR_X_MM`, `NEURAVAC_LIDAR_Y_MM`: sensor offset from wheel-axis
  midpoint, forward/left positive (defaults 0; measure the actual mount).
- `NEURAVAC_LIDAR_YAW_DEG`: counterclockwise mounting yaw of D6 zero-angle
  relative to robot forward (default 0; verify against a target ahead).

References in this checkout: `docs/2021-04-13_iRobot_Roomba_600_Open_Interface_Spec-3.md`,
packets 43/44 on pages 30–31, distance/angle on page 26, firmware bugs on page 39;
`docs/Lidar/agents/COIN-D6 Instruction Manual.md` for clockwise scan angles.

This is a recent, motion-compensated scan, not a persistent room map. It does
not correct wheel slip or close loops. True room mapping still requires
encoder `/odom`, timestamped `LaserScan`, calibrated TF, and a SLAM system.
Receipt timestamps approximate acquisition times; serial/ROS queue latency
and movement within a LiDAR packet can still distort fast turns. Do not lift
or push the robot during mapping: its encoders infer direction from commands.

After rebuilding/restarting the current checkout's web package (ensure an old
`PYTHONPATH` dashboard release is not taking precedence), verify `/telemetry`
contains changing `left_encoder`/`right_encoder` values. Check a wall while
stationary, then drive straight and turn slowly in place. Confirm the wall
stays straight during motion; calibrate wheelbase/mount if it bends or doubles.
These physical checks have not been performed by the local automated tests.

## Cleaning motor controls & SLAM map click-to-move

Inside the **Drive & vacuum controls** (`RemoteOverride`) panel on `:5000`, the
dashboard sends Roomba 600 OI Motors opcode `138` via `GET`/`POST /roomba/cleaning`:

- **VACUUM (`V`)**: toggles the vacuum fan motor (bit 1, mask `2`; keyboard shortcut `V` while manual controls are enabled).
- **MAIN BRUSH**: toggles the main brush roller (bit 2, mask `4`).
- **SIDE BRUSH**: toggles the side brush (bit 0, mask `1`).
- **ALL MOTORS ON / STOP ALL MOTORS**: sends `[138, 7]` or `[138, 0]` to toggle all three motors together.

In the **Room map & autonomous navigation** (`SlamMapView`) panel on `:5000`:

- **CLICK-TO-MOVE: ON** (default): clicking any free or grey (unexplored) cell on the SLAM map immediately sends `{"command": "goto", "return_goal": [x, y]}` to `autonomy_node` so Nav2 drives the Roomba to that point. Clicks inside the `0.10 m` red wall buffer zone are automatically snapped to the nearest clear cell outside the buffer.
- **BUFFER ON (`0.10m`)**: overlays the red obstacle buffer zone (`buffer_zone_radius_m: 0.10`) and soft orange inflation halo (`inflation_radius_m: 0.18`), configured in [`config/web_params.yaml`](config/web_params.yaml).

## Nebius room planning

The Cleaning workflow panel requires fresh Roomba group-0 sensors, a recent
`/slam/map`, `/slam/pose`, `/slam/status=TRACKING`, `/scan`, and camera frame.
The dashboard compresses the occupancy grid to at most 48 by 48 cells and
summarizes nearest valid LiDAR returns in front/left/right sectors. On request,
it sends the image and this compact state to Nebius Token Factory. Nemotron 3.5
Super VL describes the image; Nemotron 3 Ultra combines that description with
the map and sensor snapshot into a proposed ordered workflow. Configure
`NEBIUS_API_KEY`; optional overrides are `NEBIUS_BASE_URL`, `NEBIUS_VISION_MODEL`,
and `NEBIUS_MODEL`.

The camera image and robot/map data leave the Pi for cloud inference when the
operator presses the planning button. The model receives one bounded snapshot,
not a continuous stream. Its response is advice only: this project does not
execute model-generated plans or accept model-produced motor commands. Review
map, localization, and sensor data locally before any manual operation. The
map/pose freshness gate is not a substitute for physical navigation safety.

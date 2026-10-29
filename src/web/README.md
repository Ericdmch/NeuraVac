# ROS dashboard with USB camera

`web_node` serves serial controls, LiDAR, and a live USB camera panel on port
5000. Camera capture is shared across viewers. The browser requests a fresh
JPEG up to five times per second; unavailable or stale frames show OFFLINE
and reconnect automatically. This feed shows the raw camera image.

The **LEDs & songs** panel controls the Roomba power LED's color and intensity
through OI command 139. Its song editor accepts note tokens such as
`C4:32 D4:32`, converts them to MIDI note numbers, and sends song definition
and play commands 140/141. The SCI supports song slots 0–15 and up to 16 notes
per song. Durations use 1/64-second units. See
[`docs/Roomba/Roomba_SCI_manual.md`](../../docs/Roomba/Roomba_SCI_manual.md)
for the device's LED and note ranges.

The LiDAR panel receives points through a server-sent event stream. The web
node sends incremental, timestamped batches with at most 20 ms coalescing, and
the browser redraws on its next animation frame instead of waiting for another
HTTP poll. The display
keeps points from the preceding 250 ms, up to the latest 1,440 buffered points.
The polar scan uses a fixed 8 m display scale so nearby returns remain visibly
close to the robot marker. The **Room map** panel displays `/slam/map`, the
occupancy grid published by `neuravac_slam`. Its blue marker follows the
scan-matched position from `/slam/pose`, rather than staying at the map origin.

The Roomba node queries group 0 and encoders (`149 3 0 43 44`) at 10 Hz.
Odometry uses the wheel counts; the dashboard reads cached telemetry every five seconds;
**Request now** calls the `/request_telemetry` ROS service, which returns an
immediate 26-byte sample. `/telemetry` returns battery,
charging, current, temperature, bumpers, cliffs, wheel drops, wall flags,
overcurrent, and incremental distance/turn readings. Replies are accumulated
across serial chunks; incomplete, invalid, or late responses are ignored.
Readings older than 15 seconds are hidden rather than shown as current.
Use the `/request_telemetry` service instead of issuing sensor queries from
the raw serial console. Encoder-derived `/odom` supplies the scan matcher's motion prior.

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
colcon build --packages-up-to web --symlink-install
source install/setup.bash
~/neuravac-web-venv/bin/python -c 'from web.web_node import main; main()'
```

Camera defaults: `/dev/neuravac_camera` (see `src/bringup/README.md`), 1280×720, MJPEG capture. Override with
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

## LiDAR-only mapping

`neuravac_slam` consumes `lidar_points`, groups full rotations, estimates pose
by scan matching against its occupancy grid, and publishes `slam/map` at 2
Hz. It uses encoder-derived Roomba odometry; the camera is not used for mapping. Launch it by default with
`ros2 launch bringup robot.launch.py`; use `use_slam:=false` to turn mapping
off. Maps persist for the life of the node and reset on restart. Run the robot
slowly in a room with relatively stationary walls; this initial mapper has no
loop closure, so accumulated pose drift can distort large or repeated paths.

On the encoder branch, telemetry uses `roomba/sensors` (complete 26-byte packets).
`serial_rx` is retained for the raw log only. The arrow calibrates from short
straight W/S travel, with reverse handled, as on `codex/slam-collision-icp`.

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

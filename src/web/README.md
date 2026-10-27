# ROS dashboard with USB camera

`web_node` serves serial controls, LiDAR, and a live USB camera panel on port
5000. Camera capture is shared across viewers. The browser requests a fresh
JPEG up to five times per second; unavailable or stale frames show OFFLINE
and reconnect automatically. This feed shows the raw camera image.

The LiDAR panel uses a persistent `/lidar/stream` server-sent-events connection.
It batches incoming ROS points at up to 50 Hz and sends only newly received
points; the browser keeps a rolling 200 ms view. This avoids repeatedly opening
HTTP requests and retransmitting the entire scan. The occupancy panel uses a
compact binary map response and refreshes less often to leave more CPU and
network capacity for the live scan.

The dashboard polls Roomba 680 OI sensor group 0 (`142 0`) at 2 Hz via the
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
colcon build --packages-select roomba_interfaces lidar neuravac_slam web --symlink-install
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

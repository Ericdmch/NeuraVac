# bringup

Starts the whole robot with one command and keeps the USB devices from
swapping names between plugs.

## One-time setup: stable USB names

Linux numbers `/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/video0` in the order devices
are plugged in, so the Roomba cable and the LiDAR can swap. Give each device a
fixed name instead:

```bash
sudo usermod -aG dialout,video $USER      # once, then log out and back in
ros2 run bringup neuravac_udev_setup --install
ls -l /dev/neuravac_*
```

The tool asks you to unplug and replug the Roomba cable, the LiDAR and the
webcam one at a time, then installs `/etc/udev/rules.d/99-neuravac.rules` so
that these always exist, whichever `ttyUSBn` / `videoN` they land on:

| Name | Device | Used by |
| --- | --- | --- |
| `/dev/neuravac_roomba` | Roomba serial cable | `roomba_node` |
| `/dev/neuravac_lidar` | LiDAR | `lidar_node` |
| `/dev/neuravac_camera` | Webcam (capture node) | `vision_node` / `web_node` |

How each device is recognised is printed by the tool:

* **serial** - the adapter has a unique USB serial number, so it is found on any
  port.
* **port** - cheap USB-serial chips (CH340, many CP210x) have no serial number,
  and two identical adapters are indistinguishable. These are matched by
  physical USB port, so each device must stay in the same port (or hub port)
  after setup. Re-run the tool if you move one.

If `ls -l /dev/neuravac_*` shows a link missing, unplug and replug that device.
To configure only missing or moved devices, pass their names with `--only`,
for example `ros2 run bringup neuravac_udev_setup --only lidar camera --install`;
existing rules for the other devices are preserved. Without `--install` the
tool only prints the rules.

## Run everything

```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch bringup robot.launch.py
```

| Argument | Default | Effect |
| --- | --- | --- |
| `use_roomba` | `true` | Roomba serial node |
| `use_lidar` | `true` | LiDAR node |
| `use_vision` | `true` | Camera + detection node |
| `use_web` | `true` | Flask dashboard on port 5000 |
| `camera_device` | `/dev/neuravac_camera` | Webcam used by the dashboard when `use_vision:=false` |

Example without the model running: `ros2 launch bringup robot.launch.py use_vision:=false`.

Parameters still live in each package's `config/` YAML
(`roomba_params.yaml`, `lidar_params.yaml`, `vision_params.yaml`); the launch
file loads them. The web dashboard is configured with `NEURAVAC_*` environment
variables as described in `src/web/README.md`.

`roomba_node` requests sensor group 0 twice per second and publishes
incremental wheel odometry on `/odom`. The web dashboard only refreshes its
telemetry display every five seconds; **Request now** or
`ros2 service call /request_telemetry roomba_interfaces/srv/RequestTelemetry "{}"`
triggers an immediate sample. The SLAM matcher uses `/odom` as a prediction
and aligns each LiDAR scan against the map to correct wheel slip.

## Things to know

* **One process owns the webcam.** With `use_vision:=true` the vision node opens
  it and the dashboard shows the frames vision publishes on
  `camera/image/compressed` (about `camera_publish_hz` frames per second,
  independently of the slower `inference_hz` object detection). With
  `use_vision:=false` the dashboard opens `camera_device` itself.
* **Unplugged devices.** `roomba_node` and `lidar_node` exit if their port is
  missing; the launch file retries every 3 seconds, so you can plug them in
  after launching.
* **One Python environment.** The vision README builds the workspace from a
  venv created with `--system-site-packages` so the generated executables use
  it. `web_node` needs Flask and OpenCV in that same interpreter for the launch
  file to start it, instead of the separate `~/neuravac-web-venv` used for
  manual runs.
* **Without udev rules** you can instead point each YAML at
  `/dev/serial/by-path/...` or `/dev/v4l/by-path/...`, which are also tied to
  the physical port.

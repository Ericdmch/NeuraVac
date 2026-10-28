# NeuraVac camera vision node

`vision_node` wraps the existing `floor-vision-pi` inference bundle in ROS 2. It
publishes a JPEG-compressed camera stream, an optional annotated stream, and a
detection batch for every camera update. Suggested actions are metadata only;
the node does not publish Roomba drive commands.

## Topics

| Topic | Type | Purpose |
| --- | --- | --- |
| `camera/image/compressed` | `sensor_msgs/msg/CompressedImage` | JPEG camera frames |
| `camera/image_annotated/compressed` | `sensor_msgs/msg/CompressedImage` | JPEG frames with model boxes and labels |
| `camera/detections` | `roomba_interfaces/msg/VisionDetectionArray` | Frame status and zero or more detections |

Each detection includes the class, confidence, pixel bounding box, normalized
center and size, and an advisory `suggested_action`. Normalized coordinates
describe position within the image only. They are not distance or map
coordinates. `frame_valid` is false when camera recovery has not produced a
valid image for that update; its detection list is empty.

Current action mapping:

| Class | Suggested action |
| --- | --- |
| `solid_debris` | `clean` |
| `cable`, `shoe`, `large_debris` | `avoid` |
| `liquid_spill` | `avoid_and_review` |
| Other labels | `observe` |

## Deploy the inference bundle

Copy the generated `deployment/floor-vision-pi` directory from the vision
project to the Pi, for example to `~/floor-vision-pi`. Keep its model files,
`runtime.json`, and Python modules together: the ROS node imports the bundle's
camera recovery, calibration profile, NCNN setup, and detection functions.
Install the dependencies listed in that bundle's `requirements-pi.txt` in a
Python virtual environment that can see the ROS Python packages. On Ubuntu,
create it with `--system-site-packages`, source ROS before activating it, then
build the workspace from the activated environment so the generated ROS
executable uses the same interpreter:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
python3 -m venv --system-site-packages ~/neuravac-vision-venv
source ~/neuravac-vision-venv/bin/activate
python -m pip install -r ~/floor-vision-pi/requirements-pi.txt
cd ~/NeuraVac
colcon build --packages-up-to vision
source install/setup.bash
```

Use the Python version that matches the ROS installation. For example, ROS 2
Jazzy on Ubuntu 24.04 uses Python 3.12; check `python3 --version` after sourcing
ROS before creating the virtual environment. Keep ROS packages such as `rclpy`,
`sensor_msgs`, and generated workspace messages supplied by the ROS installation
and visible through `--system-site-packages`; install the model runtime from the
Pi bundle's pip requirements.

The virtual environment needs to retain access to the ROS installation's
`rclpy`, generated messages, and `sensor_msgs`. The Pi bundle's Ultralytics,
NCNN, PyTorch, and OpenCV dependencies must also import from this environment.

## Run and inspect

```bash
ros2 run vision vision_node --ros-args \
  -p bundle_dir:=$HOME/floor-vision-pi \
  -p camera_index:=0 \
  -p inference_hz:=5.0
```

Set `camera_index` to the USB camera's device index. `model_path` can override
the bundle default. On Linux ARM64, the bundle selects its NCNN model when it is
present; otherwise it selects the PyTorch checkpoint. The default is three
inference threads, 512-pixel model input, JPEG quality 80, and observation
logging to `observations/` inside the bundle. The bundle's calibrated
per-class thresholds remain in force.

Inspect detections and images with:

```bash
ros2 topic echo /camera/detections
ros2 topic hz /camera/detections
ros2 topic list
```

Use an image viewer that supports `sensor_msgs/msg/CompressedImage` to inspect
`/camera/image/compressed` or `/camera/image_annotated/compressed`. Image topics
use best-effort QoS and keep only the newest frame to avoid building a backlog.

For early integration, run with the robot stationary. The model bundle reports
that actual Pi inference performance has not yet been measured, and its current
large-debris and small-debris recall has known limitations. Suggested actions
do not prove an object is on the floor and must not directly control the robot.

## Parameters

| Parameter | Default | Purpose |
| --- | --- | --- |
| `bundle_dir` | `~/floor-vision-pi` | Deployed model bundle directory |
| `model_path` | empty | Optional `.pt` file or NCNN model directory override |
| `camera_index` | `0` | OpenCV camera device index |
| `camera_device` | empty | Camera path such as `/dev/neuravac_camera`; empty uses `camera_index` |
| `camera_fourcc` | `MJPG` | Camera pixel format; empty keeps the driver default |
| `camera_width` | `1280` | Requested USB camera width |
| `camera_height` | `720` | Requested USB camera height |
| `camera_frame_id` | `camera_optical_frame` | ROS image frame identifier |
| `device` | `cpu` | Ultralytics inference device |
| `threads` | `3` | CPU thread limit |
| `camera_publish_hz` | `12.0` | Compressed camera preview publish rate, independent of object detection |
| `inference_hz` | `5.0` | Maximum requested inference update rate |
| `imgsz` | `0` | Use calibrated profile size; nonzero must match profile |
| `publish_annotated_image` | `true` | Publish the boxed JPEG preview |
| `jpeg_quality` | `80` | JPEG quality from 1 to 100 |
| `save_observations` | `true` | Save sampled model observations via the bundle |
| `observations_dir` | empty | Override observation output directory |
| `observation_interval` | `2.0` | Minimum seconds between saved detections |

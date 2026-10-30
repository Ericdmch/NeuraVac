# NeuraVac

<p align="center">
  <img src="docs/Neuravac/LogoWhite.svg" alt="NeuraVac" width="320">
</p>

NeuraVac is a ROS 2 robot platform built around an iRobot Roomba. It combines
direct Roomba control, USB LiDAR, SLAM Toolbox 2D mapping, Nav2 autonomous
frontier exploration, camera-based floor-object detection, and a browser
dashboard into one ROS 2 workspace.

The project is designed so that hardware drivers publish and consume ROS
topics instead of depending on each other directly:

- The Roomba node owns the Roomba's Open Interface serial connection, publishes
  wheel encoder odometry (`/odom`), and runs the safety watchdog (`driver_watchdog`).
- The LiDAR node parses scan packets and publishes individual range points (`/lidar_points`).
- The mapping package (`neuravac_mapping`) deskews 360° LiDAR revolutions against
  `/odom`, runs SLAM Toolbox (`async_slam_toolbox_node`), bridges `/slam/map` and
  `/slam/pose` for the dashboard, and coordinates Nav2 autonomous frontier mapping.
- The vision node publishes camera frames and object detections.
- The web node bridges ROS topics to a unified Flask dashboard (`:5000`) for
  monitoring, manual drive & vacuum/brush motor control (`WASD` + `V` / opcode `138`),
  Nav2 costmap buffer visualization, click-to-move navigation, and autonomous room mapping.
- The bringup package starts the complete robot with one launch command and
  provides stable USB device names.
- The interfaces package contains the messages shared by those nodes.

## System overview

```mermaid
flowchart LR
    Roomba[ iRobot Roomba ] <-->|USB serial<br/>115200 baud| R[roomba_node +<br/>driver_watchdog]
    Lidar[USB LiDAR] -->|USB serial<br/>230400 baud| L[lidar_node]
    L -->|lidar_points| SB[scan_bridge]
    R -->|odom + roomba/sensors| SB
    SB -->|/scan + TF<br/>base_link to lidar_link| ST[slam_toolbox]
    ST -->|/map + TF<br/>map to odom| DB[dashboard_bridge]
    Camera[USB camera] --> V[vision_node]
    Bundle[(floor-vision-pi<br/>inference bundle)] --> V

    R -->|serial_rx / roomba/sensors| W[web_node :5000]
    DB -->|slam/map + slam/pose| W
    DB -->|slam/map + slam/pose| AN[autonomy_node + Nav2]
    AN -->|autonomy/cmd_vel| R
    AN <-->|/global_costmap/costmap + /plan<br/>autonomy/state + autonomy/request| W
    L -->|lidar_points<br/>20 ms incremental batches| W
    V -->|camera frames<br/>detections| W
    W --> Browser[Unified Web Dashboard<br/>:5000]
```

The hardware nodes can run independently. ROS 2 provides the transport and
the dashboard subscribes to the topics it needs. Vision detections contain
advisory actions such as `clean`, `avoid`, and `avoid_and_review`; the vision
node does **not** drive the Roomba.

The LiDAR reader polls every 2 ms and drains all complete packets from the
serial buffer, avoiding stale packet backlogs. The dashboard streams new
points incrementally in timestamped batches of up to 20 ms; the browser draws
on its next frame and keeps a rolling 250 ms visible.

The `roomba_node` requests `[149, 3, 0, 43, 44]` at 10 Hz and calculates
`/odom` from wheel encoder changes. Its 30-byte response contains 26 bytes of
group-0 telemetry followed by two bytes per wheel. `scan_bridge` deskews each
complete 360° LiDAR scan against `/odom` (using the physical mounting offset
`lidar_yaw_rad = +pi/2`, since `-90°` in `lidar_link` points forward along
`+X` of `base_link`) and publishes `/scan` to `slam_toolbox`. `dashboard_bridge`
republishes the resulting occupancy grid on `/slam/map` and the localized
`map -> base_link` transform on `/slam/pose`. Use **Reset & Remap** in the Room
map panel (or call `/slam/reset`) to clear the occupancy grid and restart mapping
from the robot's current position.

Collision handling discards partial, queued, and in-flight contact scans before
map insertion. Encoder counts received with bumper or wheel-drop flags are
consumed without advancing the pose, because spinning wheels need not mean
chassis motion.

The dashboard reads cached telemetry every five seconds and has a **Request
now** button. The `request_telemetry` ROS service requests and returns
fresh group-0 telemetry from the same serialized encoder query. The service
joins an outstanding query instead of inserting another serial transaction.
Only `roomba/sensors` carries the extracted 26-byte telemetry payload;
`serial_rx` remains the complete raw stream, including encoder bytes.

## ROS 2 packages

| Package | Type | Responsibility |
| --- | --- | --- |
| [`roomba`](src/roomba) | `ament_python` | Owns the Roomba serial port, publishes raw serial bytes and wheel odometry, runs the `driver_watchdog`, and serves on-demand telemetry requests. See [`src/roomba/README.md`](src/roomba/README.md). |
| [`lidar`](src/lidar) | `ament_python` | Reads the LiDAR serial stream, validates packets, decodes angle/distance/intensity, and publishes points. |
| [`neuravac_mapping`](src/neuravac_mapping) | `ament_python` | Deskews LiDAR scans (`scan_bridge`), runs SLAM Toolbox (`mapping.launch.py`), bridges `/slam/map` and `/slam/pose` (`dashboard_bridge`), and runs Nav2 autonomous frontier exploration (`autonomy.launch.py`). |
| [`neuravac_slam`](src/neuravac_slam) | `ament_python` | Legacy scan matcher (`slam_backend:=legacy`). Replaced by `neuravac_mapping` (`slam_backend:=toolbox`) by default. |
| [`roomba_interfaces`](src/roomba_interfaces) | `ament_cmake` | Builds the custom ROS 2 messages shared by the nodes. |
| [`vision`](src/vision) | `ament_python` | Captures camera frames, runs the deployed floor-vision model, and publishes detections. |
| [`web`](src/web) | `ament_python` | Runs the Flask dashboard and bridges browser actions and telemetry to ROS 2. |
| [`bringup`](src/bringup) | `ament_python` | Launches the robot nodes together and creates stable USB device names. |

### Interfaces and topics

#### Roomba serial bridge

| Topic | Type | Direction | Purpose |
| --- | --- | --- | --- |
| `serial_rx` | `roomba_interfaces/msg/SerialData` | Roomba -> ROS | Raw bytes received from the Roomba. |
| `serial_tx` | `roomba_interfaces/msg/SerialData` | ROS -> Roomba | Raw bytes sent to the Roomba. |
| `odom` | `nav_msgs/msg/Odometry` | Roomba -> ROS | Pose and velocity from encoder packets 43 and 44. |
| `roomba/sensors` | `roomba_interfaces/msg/SerialData` | Roomba -> ROS | Extracted 26-byte OI sensor group-0 packet. |
| `request_telemetry` | `roomba_interfaces/srv/RequestTelemetry` | ROS -> Roomba | Requests and returns a fresh 26-byte OI sensor group 0 response. |

`SerialData` contains a `uint8[] data` field. The Roomba node starts the
robot in safe mode and uses 115200 baud by default.

Read current telemetry from the dashboard or request an immediate sample from
ROS:

```bash
ros2 service call /request_telemetry roomba_interfaces/srv/RequestTelemetry "{}"
```

The SCI manual documents opcode 142 as the sensor request, packet code 0 as
the 26-byte all-sensor packet, and the distance/angle values as signed,
big-endian increments. See
[`docs/Roomba/Roomba_SCI_manual.md`](docs/Roomba/Roomba_SCI_manual.md).

#### LiDAR and SLAM mapping

| Topic or service | Type | Purpose |
| --- | --- | --- |
| `lidar_points` | `roomba_interfaces/msg/LidarPoint` | Decoded points containing `angle_deg`, `distance_mm`, and `intensity`. |
| `scan` | `sensor_msgs/msg/LaserScan` | Deskewed 360° scan in `lidar_link` published by `scan_bridge`. |
| `slam/map` | `nav_msgs/msg/OccupancyGrid` | 2D room occupancy grid in the `map` frame (`0` free, `100` occupied, `-1` unknown). |
| `slam/pose` | `geometry_msgs/msg/PoseStamped` | Localized robot position and heading in the `map` frame. |
| `slam/status` | `std_msgs/msg/String` | Mapping status (`TRACKING` or `WAITING FOR SCANS`). |
| `slam/reset` | `std_srvs/srv/Trigger` | Clears the SLAM Toolbox map and pose graph so fresh scans start a new map. |

The dashboard's **Reset & Remap** button calls `/slam/reset`. To reset from a
terminal:

```bash
ros2 service call /slam/reset std_srvs/srv/Trigger "{}"
```

The LiDAR node expects the D6 packet format described in the source and uses
230400 baud by default.

#### Autonomous mapping and click-to-move (`neuravac_mapping` + `web`)

| Topic, action, or service | Type | Purpose |
| --- | --- | --- |
| `autonomy/request` | `std_msgs/msg/String` | JSON mission commands (`goto` to drive to `return_goal`, `start` to explore frontiers and return to `return_goal`, `return`, `stop`). |
| `autonomy/state` | `std_msgs/msg/String` | JSON mission state (`idle`, `exploring`, `returning`, `complete`, `stopped`, `motion_enabled`). |
| `autonomy/cmd_vel` | `geometry_msgs/msg/Twist` | Coordinator velocity commands forwarded to `driver_watchdog`. |
| `autonomy/driver_status` | `std_msgs/msg/String` | Watchdog state (`ARMED`, `DISARMED`, or latched stop reason). |
| `autonomy/arm` / `autonomy/disarm` | `std_srvs/srv/Trigger` | Arms or disarms autonomous motor output in `roomba_node`. |
| `navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | Nav2 action server used for click-to-move, frontier, and return navigation. |
| `/global_costmap/costmap` | `nav_msgs/msg/OccupancyGrid` | Nav2 global costmap overlaid on the `:5000` Room map. |
| `/plan` | `nav_msgs/msg/Path` | Active Nav2 global path rendered in green on the `:5000` Room map. |

The red high-cost obstacle buffer zone and drive speeds on the `:5000` dashboard
are configured in [`src/web/config/web_params.yaml`](src/web/config/web_params.yaml):

```yaml
web_node:
  ros__parameters:
    default_drive_speed_mm_s: 200
    min_drive_speed_mm_s: 50
    max_drive_speed_mm_s: 500
    drive_speed_step_mm_s: 50
    buffer_zone_radius_m: 0.10    # Red lethal/inscribed buffer zone around walls (meters)
    inflation_radius_m: 0.18      # Soft cost falloff zone around obstacles (meters)
    high_cost_threshold: 99       # Costmap threshold (0-100) rendered as red buffer zone
    show_costmap_by_default: true
```

To adjust the obstacle buffer across both the web dashboard and the Nav2/Roomba
safety controllers, edit these three YAML files:

1. **Dashboard map buffer & click-to-move clearance** — [`src/web/config/web_params.yaml`](src/web/config/web_params.yaml):
   - `buffer_zone_radius_m` (default `0.10`): radius in meters of the solid red high-cost buffer zone around walls.
   - `inflation_radius_m` (default `0.18`): radius in meters of the soft orange cost falloff halo around walls.
   - `high_cost_threshold` (default `99`): Nav2 costmap threshold (`0–100`) drawn in red.
2. **Nav2 planner/controller & coordinator clearance** — [`src/neuravac_mapping/config/autonomy_nav2.yaml`](src/neuravac_mapping/config/autonomy_nav2.yaml):
   - `local_costmap.local_costmap.ros__parameters.robot_radius` (default `0.10`)
   - `local_costmap.local_costmap.ros__parameters.inflation_layer.inflation_radius` (default `0.18`)
   - `global_costmap.global_costmap.ros__parameters.robot_radius` (default `0.10`)
   - `global_costmap.global_costmap.ros__parameters.inflation_layer.inflation_radius` (default `0.18`)
   - `autonomous_mapping.ros__parameters.clearance_m` (default `0.10`)
3. **Roomba LiDAR watchdog stop distance** — [`src/roomba/config/roomba_params.yaml`](src/roomba/config/roomba_params.yaml):
   - `min_obstacle_distance_m` (default `0.10`): minimum forward LiDAR distance before `driver_watchdog` stops autonomous motion.

#### Click-to-move & autonomous navigation speed

Click-to-move and autonomous travel speeds are configured in
[`src/neuravac_mapping/config/autonomy_nav2.yaml`](src/neuravac_mapping/config/autonomy_nav2.yaml)
and [`src/roomba/config/roomba_params.yaml`](src/roomba/config/roomba_params.yaml):

- **`desired_linear_vel`** (`controller_server.ros__parameters.FollowPath` in `src/neuravac_mapping/config/autonomy_nav2.yaml`, default `0.22`): base Nav2 linear travel speed in `m/s` (`0.22 m/s` = `220 mm/s`).
- **`rotate_to_heading_angular_vel`** (`controller_server.ros__parameters.FollowPath` in `src/neuravac_mapping/config/autonomy_nav2.yaml`, default `1.0`): in-place turning speed toward the clicked point in `rad/s`.
- **`click_to_move_speed_multiplier`** (`autonomous_mapping.ros__parameters` in `src/neuravac_mapping/config/autonomy_nav2.yaml`, default `1.25`): multiplier applied on top of Nav2's velocity specifically when moving to a clicked point on the SLAM map (`0.22 * 1.25 = 0.275 m/s` / `275 mm/s`).
- **`max_autonomous_linear_vel_m_s`** & **`max_autonomous_angular_vel_rad_s`** (`autonomous_mapping.ros__parameters` in `src/neuravac_mapping/config/autonomy_nav2.yaml`, defaults `0.35` m/s and `1.5` rad/s): upper bounds for scaled click-to-move velocities.
- **`max_goto_retries`** (`autonomous_mapping.ros__parameters` in `src/neuravac_mapping/config/autonomy_nav2.yaml`, default `5`): automatic retry count when driving toward a clicked point if Nav2 replans around a newly discovered obstacle.
- **`allow_unknown: true` & `tolerance: 0.50`** (`planner_server.ros__parameters.GridBased` in `src/neuravac_mapping/config/autonomy_nav2.yaml`): allows clicking on grey (unexplored) areas on the SLAM map to drive directly into/toward them, and automatically snaps clicks near walls to the nearest clear cell outside the red buffer zone.
- **`autonomous_max_wheel_speed_m_s`** (`roomba_node.ros__parameters` in `src/roomba/config/roomba_params.yaml`, default `0.45`): safety ceiling on individual wheel speed in `driver_watchdog` (`0.45 m/s` = `450 mm/s`).

#### Vacuum and cleaning motor controls

Inside the **Drive & vacuum controls** panel on `:5000`, you can toggle the
Roomba's cleaning motors (Open Interface opcode `138` via `GET`/`POST /roomba/cleaning`):

- **VACUUM (`V`)**: toggles the vacuum fan motor (bit 1, mask `2`; keyboard shortcut `V` while manual controls are enabled).
- **MAIN BRUSH**: toggles the under-chassis main brush roller (bit 2, mask `4`).
- **SIDE BRUSH**: toggles the spinning side brush (bit 0, mask `1`).
- **ALL MOTORS ON / STOP ALL MOTORS**: toggles all three cleaning motors together (mask `7` / `0`).

#### Draggable Roomba task queue, polygon region cleaning & dock seeking (`TaskQueuePanel` & `task_queue.py`)

The unified `:5000` dashboard includes a live **Roomba task queue** panel
([`TaskQueuePanel`](src/web/web/static/components.js) backed by
[`TaskQueueManager`](src/web/web/task_queue.py)) that executes tasks in order:

- **Drag-and-drop reordering**: Drag any task card (or use its `↑` / `↓` buttons) to reorder priority (`PUT /tasks/reorder`). Dragging a queued task to the top immediately preempts the current autonomous task and starts the new top task.
- **Automatic Manual Override preemption**: Holding `WASD` in the manual override panel (or clicking **INSERT OVERRIDE**) automatically inserts a `Manual Override` task at index `0` (`status: active`) and pauses/demotes the active autonomous task back to `queued` so it resumes once manual override ends.
- **Interactive Polygon Region Drawing & Cleaning (`GET`/`POST /regions`, `DELETE /regions/<id>`)**:
  - Click **DRAW POLYGON** on the SLAM map (or **+ Draw Cleaning Polygon on Map** in the Task Queue), click 3 or more points on the SLAM map to outline any region, name the region, and click **CLEAN THIS POLYGON** (or **SAVE REGION**).
  - **Purple Cleaning Tiles & Live Sweep Progress**: The moment a region is instructed to be cleaned, all floor tiles inside the polygon turn vibrant **purple** (`#8b5cf6`). As the Roomba drives through the region with vacuum and brushes spinning (`[138, 7]`), the tiles underneath the robot's cleaning sweep radius (`0.18 m`) automatically turn back to the dark-slate background color in real time, with the live coverage percentage displayed on the map badge and task card (e.g. `Rug Zone · 74% CLEANED`).
  - [`generate_polygon_waypoints`](src/web/web/task_queue.py) computes a boustrophedon (lawnmower zig-zag) coverage path (`0.25 m` stripe spacing) inside the polygon, steps through every waypoint in the polygon (`Cleaning waypoint i/N`), skips blocked points rather than aborting, and turns off the cleaning motors when finished.
- **Computer Vision Debris & Obstacle Detection (`[CLEAN]` / `[AVOID]`)**:
  - `vision_node` runs the floor-vision NCNN/YOLO model on `/dev/neuravac_camera`, streaming annotated frames with bounding box tags to `/camera/image_annotated/compressed` and object detections to `/camera/detections`.
  - The live camera feed includes a one-click **`[FLIP 180°]`** toggle in the header to invert the video display orientation between 0° and 180°.
  - Detected objects are classified into two advisory actions:
    - **`[CLEAN]`** (emerald diamond badge): Floor debris (`solid_debris`, small debris, dust, crumbs) with a one-click `Clean` button to send the Roomba directly to spot-clean that target.
    - **`[AVOID]`** (red/amber hazard badge): Obstacles and cords (`cable`, `shoe`, `large_debris`, `liquid_spill`, `obstacle`) placed as persistent obstacle markers on the 2D SLAM map.
  - **Dismiss Markers as False Positives**: Markers can be dismissed either by clicking **`[✕ False]`** in the camera detection strip, clicking the marker on the SLAM map canvas and selecting **`DISMISS FALSE`**, or sending `POST /vision/markers/<marker_id>/dismiss`. Dismissed locations are recorded and suppressed so continuous camera inferences do not re-add false positives. A **Reset False Positives** button (`DELETE /vision/markers/dismissed`) allows clearing dismissed filters when desired.
  - **Avoidance Identifiers Section (`GET`/`POST /vision/avoid-identifiers`)**: A dedicated panel in the dashboard allows toggling individual obstacle classes (`Cables & Wires`, `Footwear & Shoes`, `Liquid Spills`, `Large Debris`, `General Obstacles`, `Unknown`) ON or OFF. When an identifier is toggled OFF, existing avoid markers of that class are pruned and subsequent detections of that category are ignored rather than mapped as obstacles.
  - Markers are exposed via `GET`/`POST`/`DELETE /vision/markers` and rendered live on both the SLAM map and the Camera feed strip.
- **Clicking points on the SLAM map**: With `CLICK-TO-MOVE: ON`, clicking points on the SLAM map queues `Go to (x, y) m` tasks in order and renders numbered waypoint badges (`1`, `2`, `3`…) on the map canvas.
- **Built-in task types (`GET`/`POST /tasks`, `DELETE /tasks/<id>`, `POST /tasks/clear`, `POST /tasks/control`, `POST /roomba/dock`)**:
  - **Clean Polygon Region (`clean_polygon`)**: Runs lawnmower coverage across a user-drawn polygon region with vacuum + brushes enabled.
  - **Scan Area (`scan_area`)**: Runs persistent SLAM Toolbox + Nav2 frontier exploration (`start`). If the Roomba starts inside or enters a red buffer zone, [`_explore_next_with_escape`](src/neuravac_mapping/neuravac_mapping/autonomy_node.py) automatically drives out to the nearest clear cell and continues scanning with relaxed clearance instead of halting.
  - **Go to Map Target (`goto`)**: Navigates to `[x, y]` via Nav2.
  - **Return to Dock (`return_home`) & Seek Dock (`seek_dock`)**: Navigates back to `(0, 0)` near the home base, stops the cleaning motors, and sends Roomba SCI/OI **Seek Dock opcode `143` (`Force-Seeking-Dock`)** (`[143]`) so the Roomba locks onto the docking station IR beams.

#### Vision

| Topic | Type | Purpose |
| --- | --- | --- |
| `camera/image/compressed` | `sensor_msgs/msg/CompressedImage` | JPEG camera frames. |
| `camera/image_annotated/compressed` | `sensor_msgs/msg/CompressedImage` | JPEG frames with model annotations. |
| `camera/detections` | `roomba_interfaces/msg/VisionDetectionArray` | Object detections and advisory actions. |

See [`src/vision/README.md`](src/vision/README.md) for the model bundle,
parameters, detection labels, and deployment notes.

## Requirements

- Ubuntu/Linux with ROS 2 (the deployment documentation targets ROS 2 Jazzy)
- Python 3.10 or newer
- `colcon`, `rosdep`, and the ROS 2 packages required by the package manifests
  (including `ros-jazzy-slam-toolbox` and `ros-jazzy-navigation2` / `ros-jazzy-nav2-bringup`)
- `pyserial` for the USB serial devices
- Flask and OpenCV for the dashboard/camera features
- A deployed `floor-vision-pi` bundle for the vision node
- User access to the serial and camera devices (`dialout` and `video` groups
  are commonly required on Linux)

The project also declares the main Python dependencies in
[`pyproject.toml`](pyproject.toml).

## Build

Source ROS 2, install dependencies, build the workspace, and source the
generated setup file:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Neuravac
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

When only core robot and mapping packages are needed:

```bash
colcon build --packages-select roomba_interfaces roomba lidar neuravac_mapping neuravac_slam vision web bringup --symlink-install
```

Build `vision` after its model bundle dependencies are installed:

```bash
colcon build --packages-up-to vision --symlink-install
```

## Configure the hardware and USB names

The Roomba and LiDAR must use different serial devices. Do not configure both
nodes to use the same `/dev/ttyUSB*` path. The bringup package supports stable
names so the devices do not swap when they are plugged in in a different
order.

Install the udev rules once. The setup command asks you to unplug and replug
the Roomba cable, LiDAR, and webcam one at a time:

```bash
sudo usermod -aG dialout,video $USER
ros2 run bringup neuravac_udev_setup --install
ls -l /dev/neuravac_*
```

Log out and back in after changing groups. The resulting device names are:

| Device | Stable path |
| --- | --- |
| Roomba serial adapter | `/dev/neuravac_roomba` |
| LiDAR serial adapter | `/dev/neuravac_lidar` |
| Webcam | `/dev/neuravac_camera` |

The serial ports and baud rates are configured in:

- [`src/roomba/config/roomba_params.yaml`](src/roomba/config/roomba_params.yaml)
- [`src/lidar/config/lidar_params.yaml`](src/lidar/config/lidar_params.yaml)

The YAML files default to the physical USB port paths currently wired on the Pi
(`/dev/serial/by-path/platform-xhci-hcd.0-usb-0:1:1.0-port0` for the Roomba and
`/dev/serial/by-path/platform-xhci-hcd.1-usb-0:2:1.0-port0` for the LiDAR) so
that both `systemctl --user` and `ros2 launch bringup robot.launch.py` open the
correct serial ports even if `/etc/udev/rules.d/99-neuravac.rules` was generated
when the cables were in different USB sockets. Because CH340 (`1a86:7523`)
USB-serial adapters do not have unique serial numbers, they are identified by
their physical USB port — keep each adapter in the same USB port, or re-run
`ros2 run bringup neuravac_udev_setup --install` if you move a cable.

## Start the robot (with SLAM mapping and all nodes running)

Before starting, wake the Roomba by pressing **CLEAN** on the robot if it is
asleep. Make sure you only run **one** startup method at a time (either the
`systemd --user` services or manual `ros2 launch` terminals) so duplicate nodes
do not compete for the USB serial ports.

### Option A: Start all nodes via `systemd --user` services (recommended on the Pi)

On the Raspberry Pi, five user services manage the hardware drivers, SLAM
Toolbox mapping, Nav2 autonomous navigation stack, and the unified `:5000` web
dashboard:

| Service | Nodes started | Purpose |
| --- | --- | --- |
| `neuravac-roomba.service` | `roomba_node` | Roomba serial owner, `/odom` encoder odometry, `/roomba/sensors`, and `driver_watchdog`. |
| `neuravac-lidar.service` | `lidar_node` | D6 USB LiDAR driver publishing `/lidar_points`. |
| `neuravac-toolbox.service` | `scan_bridge`, `slam_toolbox`, `dashboard_bridge` | Deskews `/lidar_points` into `/scan`, runs SLAM Toolbox, and publishes `/slam/map`, `/slam/pose`, and TF (`map -> odom -> base_link -> lidar_link`). |
| `neuravac-dashboard.service` | `web_node` | Unified Flask dashboard on `http://<pi-ip>:5000` (telemetry, manual drive override, SLAM map, Nav2 costmap buffer, click-to-move, and autonomous mapping). |
| `neuravac-autonomy.service` | `controller_server`, `planner_server`, `bt_navigator`, `lifecycle_manager_autonomy`, `autonomy_node` | Nav2 planner/controller/BT stack and autonomous coordinator (`enable_dashboard:=false` so everything runs on `:5000`). |

Start all five services together:

```bash
systemctl --user start \
  neuravac-roomba.service \
  neuravac-lidar.service \
  neuravac-toolbox.service \
  neuravac-dashboard.service \
  neuravac-autonomy.service
```

Check that all services are `active (running)`:

```bash
systemctl --user status \
  neuravac-roomba.service \
  neuravac-lidar.service \
  neuravac-toolbox.service \
  neuravac-dashboard.service \
  neuravac-autonomy.service \
  --no-pager
```

Stop all services cleanly and restart the Roomba:

```bash
systemctl --user stop \
  neuravac-autonomy.service \
  neuravac-toolbox.service \
  neuravac-dashboard.service \
  neuravac-lidar.service \
  neuravac-roomba.service

systemctl --user start \
  neuravac-roomba.service \
  neuravac-lidar.service \
  neuravac-toolbox.service \
  neuravac-dashboard.service \
  neuravac-autonomy.service
```

#### Using Click-to-Move, Autonomous Mapping, and Manual Override on `:5000`

1. Open the unified dashboard at `http://<pi-ip>:5000` (e.g., `http://100.106.145.39:5000`).
2. **Manual Drive Controls (`WASD` / Arrow keys):**
   - Manual drive controls are enabled by default in the **Drive controls** panel.
   - Hold or click **W / A / S / D** (or the arrow keys) to drive forward, turn left, reverse, or turn right; use **Q / E** to decrease or increase speed (`50–500 mm/s`).
   - Any manual drive command immediately preempts autonomous navigation.
3. **Click-to-Move & Costmap Buffer Zone (`Room map & autonomous navigation`):**
   - Walls are rendered in orange, the forbidden high-cost buffer zone (`buffer_zone_radius_m`, default `0.255 m`) is rendered in **red**, and safe known-free floor space is rendered in **blue-slate**.
   - With **CLICK-TO-MOVE: ON** (default), clicking any blue-slate free cell outside the red buffer zone places an orange target marker and immediately commands Nav2 to drive the Roomba to that point (drawing the planned Nav2 path in green).
   - You can also toggle **CLICK-TO-MOVE: OFF** to preview target coordinates first and then click **GO TO POINT** to drive there.
   - Click **AUTO-MAP ROOM** to autonomously explore all reachable frontiers in the room and return to the selected target point when mapping completes.
   - Click **END & RETURN** to finish exploration early and return to the selected point, or click **STOP** for an immediate halt and watchdog disarm.
   - Use **BUFFER ON / BUFFER OFF** to toggle the red costmap buffer overlay, and **MOTION ENABLED / MOTION LOCKED** to enable or lock autonomous motion.

### Option B: Start all nodes manually via `ros2 launch`

If you prefer to run the nodes interactively in terminals (including
`vision_node`), first ensure the background systemd services are stopped:

```bash
systemctl --user stop \
  neuravac-autonomy.service \
  neuravac-toolbox.service \
  neuravac-dashboard.service \
  neuravac-lidar.service \
  neuravac-roomba.service
```

**Terminal 1 — Hardware drivers, SLAM Toolbox mapping, vision, and main dashboard (`:5000`):**

```bash
source /opt/ros/jazzy/setup.bash
source ~/neuravac-web-venv/bin/activate
source ~/Neuravac/src/neuravac_mapping/deployment/runtime-env.sh
source ~/Neuravac/install/setup.bash
ros2 launch bringup robot.launch.py slam_backend:=toolbox
```

This single launch command starts:
- `roomba_node` (Roomba serial bridge, encoder `/odom`, `driver_watchdog`)
- `lidar_node` (USB LiDAR driver)
- `neuravac_mapping/mapping.launch.py` (`scan_bridge`, `slam_toolbox`, `dashboard_bridge`)
- `vision_node` (floor-vision camera model)
- `web_node` (main dashboard at `http://localhost:5000`)

Useful `robot.launch.py` arguments:

```bash
# Run without the floor-vision model (web_node captures /dev/neuravac_camera directly)
ros2 launch bringup robot.launch.py slam_backend:=toolbox use_vision:=false camera_device:=/dev/neuravac_camera

# Record diagnostic rosbags to ~/Neuravac/logs/
ros2 launch bringup robot.launch.py slam_backend:=toolbox use_diagnostics:=true

# Use the legacy scan matcher instead of SLAM Toolbox
ros2 launch bringup robot.launch.py slam_backend:=legacy
```

**Terminal 2 — Nav2 autonomous navigation stack and mapping coordinator (controlled from `:5000`):**

```bash
source /opt/ros/jazzy/setup.bash
source ~/Neuravac/src/neuravac_mapping/deployment/runtime-env.sh
source ~/Neuravac/install/setup.bash
ros2 launch neuravac_mapping autonomy.launch.py enable_motion:=true enable_dashboard:=false
```

### Start vision standalone

Deploy the inference bundle as described in
[`src/vision/README.md`](src/vision/README.md), then start the node with its
bundle path:

```bash
ros2 run vision vision_node --ros-args \
  -p bundle_dir:=$HOME/floor-vision-pi \
  -p camera_index:=0 \
  -p inference_hz:=5.0
```

The vision node publishes detections and annotated images, but it does not
publish Roomba drive commands.

## Inspect the ROS graph

Useful commands while the system is running:

```bash
source /opt/ros/jazzy/setup.bash
source ~/Neuravac/src/neuravac_mapping/deployment/runtime-env.sh
source ~/Neuravac/install/setup.bash

ros2 node list
ros2 topic list
ros2 topic echo /slam/status --once
ros2 topic echo /slam/pose --once
ros2 topic echo /autonomy/state --once
ros2 topic echo /autonomy/driver_status --once
ros2 topic hz /scan
```

To confirm which nodes own a topic:

```bash
ros2 topic info /serial_tx
ros2 topic info /lidar_points
ros2 topic info /slam/map
```

## Testing

Run the package tests after sourcing ROS:

```bash
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

Run the `neuravac_mapping` unit and isolated ROS test suite (`61` tests):

```bash
source /opt/ros/jazzy/setup.bash
source ~/Neuravac/install/setup.bash
cd ~/Neuravac/src/neuravac_mapping
ROS_DOMAIN_ID=55 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The web package also has focused unit tests:

```bash
PYTHONPATH=src/web:$PYTHONPATH python3 -m unittest discover -s src/web/tests
```

## Repository layout

```text
.
├── docs/                   Hardware manuals, architecture plans, and NeuraVac logo assets
├── src/
│   ├── bringup/            Full-robot launch file and USB udev setup
│   ├── lidar/              LiDAR ROS 2 node and configuration
│   ├── neuravac_mapping/   SLAM Toolbox bridge, Nav2 config, frontier planner, and watchdog
│   ├── neuravac_slam/      Legacy LiDAR scan matcher and 2D occupancy mapper
│   ├── roomba/             Roomba serial ROS 2 node, encoder odometry, and configuration
│   ├── roomba_interfaces/  Custom ROS 2 messages and services
│   ├── vision/             Camera and floor-object detection node
│   └── web/                Flask dashboard and ROS bridge
├── build/                  Colcon build output (generated)
├── install/                Colcon install output (generated)
└── pyproject.toml          Python project metadata and dependencies
```

## Hardware and protocol references

The web dashboard has an **LEDs & songs** panel for the power LED and short
Roomba tunes. The editor accepts note tokens such as `C4:32 D4:32`; durations
are measured in 1/64-second units. LED and song command limits are documented
in the [SCI manual](docs/Roomba/Roomba_SCI_manual.md).

- [Roomba SCI manual](docs/Roomba/Roomba_SCI_manual.md)
- [LiDAR documentation](docs/Lidar)
- [Autonomous mapping status](docs/plans/autonomous-mapping-status.md)
- [SLAM Toolbox migration](docs/plans/slam-toolbox-migration.md)
- [Vision package guide](src/vision/README.md)
- [Web dashboard guide](src/web/README.md)
- [Bringup package guide](src/bringup/README.md)

## Encoder positioning configuration

`src/roomba/config/roomba_params.yaml` contains nominal wheel diameter (0.072 m),
encoder counts per revolution (508.8), wheel track (0.235 m), left/right scale
factors, polling rate, query timeout, and startup delay. Wheel track is the
distance between wheel contact centers across the robot.

`roomba/encoder_counts` is `std_msgs/UInt16MultiArray`, ordered `[left, right]`,
preserving raw 16-bit patterns. Signed modular differences handle rollover in
both directions; the first sample establishes a baseline. Implausible jumps and
gaps over two seconds rebaseline without moving the estimated pose. Group-0
distance and angle are not used for positioning.

`roomba/sensors` contains the extracted 26-byte group-0 payload for web
telemetry, `scan_bridge` contact rejection, and `driver_watchdog` hazard checks.
Wake the robot with CLEAN if asleep before launching. Startup sends Start,
waits two seconds, then enters Safe mode and sends stop. Avoid injecting sensor
queries or stream commands through the manual serial console while the driver
owns the port.

# NeuraVac SLAM Toolbox integration

This package replaces the custom grid mapper with official ROS Jazzy SLAM
Toolbox (correlative scan matching, Ceres pose-graph optimization, loop closure).
The legacy mapper and its saved grid remain available; that grid is not imported
as a pose graph. First startup starts a fresh map.

## Data and coordinate contracts

- Native D6 driver keeps `/lidar_points` and also publishes `/scan_raw`:
  clockwise angular order, measured revolution period, estimated first-ray
  timestamp, positive per-ray time increment. D6 serial protocol has no hardware
  clock; seam arrival/phase reconstruct acquisition timing, so unmeasured serial
  latency and rate variation remain limitations.
- Scan bridge brackets every valid return with timestamped wheel poses, handles
  yaw wrapping, and transforms it to the scan-end sensor pose. It re-bins CCW
  `/scan` in `lidar_link`, with positive angle increment and zero time increment
  because all corrected rays now share one reference time. Missing/gapped
  odometry, insufficient returns, and contact/wheel-drop scan intervals are
  rejected, not extrapolated into a map.
- Single TF owners: scan bridge publishes `odom -> base_link` from encoders and
  static `base_link -> lidar_link`; SLAM Toolbox publishes `map -> odom`.
- User reports LiDAR centered between wheels with aligned zero-angle direction;
  default mount is `(0, 0, 0)`. Launch args `lidar_x_m`, `lidar_y_m`,
  `lidar_yaw_rad` allow measured calibration later. Positive x is forward,
  positive y left, yaw counterclockwise.
- Dashboard bridge relays `/map` to `/slam/map` and map/base TF to `/slam/pose`.
  TRACKING means fresh TF and scans, not independently verified physical accuracy.
  `/slam/reset` clears the Toolbox graph; `/slam/save` serializes graph and scans
  to `~/Neuravac/maps/toolbox.{posegraph,data}`. Existing raw telemetry/controls
  and dashboard endpoints remain intact.
- Arrow display was rotated another 180 degrees from its previous +90-degree
  offset: total +270 degrees clockwise. This changes no TF, odometry, or SLAM yaw.

## Pi installation and operation

All source backups: `~/neuravac-backups/toolbox-migration/source-before.tgz`,
`preexisting.patch`, and `room.npz`. Official runtime packages were extracted
under `~/neuravac-slam-runtime/root` because sudo requires a password. This
runtime uses the Pi's existing ROS Jazzy and Ubuntu libraries; it is not a
replacement for a full ROS installation. `deployment/install-runtime.sh`
reproduces the additional runtime downloads; `debs/packages.sha256` records them.

```bash
source /opt/ros/jazzy/setup.bash
source ~/Neuravac/src/neuravac_mapping/deployment/runtime-env.sh
cd ~/Neuravac
colcon build --packages-select neuravac_mapping lidar bringup --symlink-install
source install/setup.bash
ros2 launch bringup robot.launch.py use_vision:=false slam_backend:=toolbox
```

Do not start a second serial driver or mapper alongside an existing launch.
The current deployment keeps the independently running dashboard and launches
with `use_web:=false`, via `deployment/start-toolbox.sh`. It is not boot-enabled.
The launch defaults to Toolbox; `slam_backend:=legacy` selects the previous
backend. Stop the Toolbox launch and its child processes before rollback, then
launch legacy with the same runtime/overlay sourced. Do not run both backends.

## Verification

```bash
ROS_DOMAIN_ID=55 python3 -m unittest discover -s src/neuravac_mapping/tests
python3 src/neuravac_mapping/deployment/verify_live.py
ros2 lifecycle get /slam_toolbox
ros2 topic echo /mapping/scan_diagnostics --once
ros2 service call /slam/save std_srvs/srv/Trigger '{}'
```

No automatic drive commands are sent by verification. Physical acceptance:
start stopped, map slowly, turn in place, revisit a recognizable corner, and
close a loop. Confirm walls do not double and returning to the start aligns the
pose/map. Wheel slip, incorrect wheelbase, mounting offsets, and delayed sensor
measurements still require measured calibration; passing synthetic tests does
not prove physical mapping accuracy.

## Primary references

- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox/tree/jazzy)
- [Jazzy async parameters](https://github.com/SteveMacenski/slam_toolbox/blob/jazzy/config/mapper_params_online_async.yaml)
- [LaserScan timing contract](https://github.com/ros2/common_interfaces/blob/rolling/sensor_msgs/msg/LaserScan.msg)
- [Motion correction and loop closure](https://google-cartographer-ros.readthedocs.io/en/latest/algo_walkthrough.html)

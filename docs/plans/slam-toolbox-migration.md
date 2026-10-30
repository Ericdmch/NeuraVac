# SLAM Toolbox migration

Implement the user-authorized replacement of the custom grid mapper. Preserve
Pi changes, old map, and backend. No autonomous driving during verification.

1. Publish timestamped clockwise raw revolutions at the LiDAR driver; retain
   legacy point topic. Reconstruct per-ray times from measured revolution
   duration (device protocol lacks hardware time). Bound bad/gapped scans.
2. New neuravac_mapping package: interpolate timestamped wheel poses, deskew
   raw scans into a common frame, bin CCW LaserScan, publish odom/base TF and
   measured/configurable base/lidar TF. Reject scans without bracketing poses.
3. Run official async SLAM Toolbox with loop closure and pose-graph optimizer.
   Bridge /map + TF pose to existing /slam/map, /slam/pose, /slam/status; connect
   dashboard reset to Toolbox reset. Do not reuse the corrupt occupancy grid.
4. Add backend selection to Pi bringup and save runnable deployment/rollback
   scripts; install official runtime in user prefix if sudo is unavailable.
5. Add 180 degrees to current arrow offset (total 270 clockwise).
6. Verify scan/TF mathematical regressions, ROS build, lifecycle, live scan
   counts, TF, map/pose stream, package dependencies, and dashboard. Preserve
   backup rather than overwriting old map; physical loop-closing remains a
   manual validation step unless the operator performs it.

Review focus: yaw wrap interpolation, invalid/missing ranges, stale feedback,
scan seam/timing/order, stopped robot, duplicate TF ownership, reset semantics.

## Deployment verification

Implemented and deployed to neuravac@100.106.145.39. User confirmed sensor
centered between wheels and zero-angle aligned, so mount x/y/yaw defaults zero.
Official runtime loaded from user prefix; Ceres optimizer configured and
Toolbox lifecycle ACTIVE. No sudo/system package database changes required.

- New package: 10/10 tests passed in isolated Pi ROS domain 55.
- Live 12-second check: 104 raw scans, 99 corrected scans, 121 odometry
  messages, 11 maps, 103 poses; 720 bins with 385 finite returns at sample.
- All three TF links available, TRACKING, graph save/reset successful.
- Dashboard stream and SLAM pose matched exactly in final stopped check;
  telemetry online with 0.02-second age; served arrow is previous offset +180.
- Final review found no remaining important correctness issues after seam-phase,
  contact rejection, and status-freshness fixes.
- Old mapper/grid backups retained. New graph starts fresh. Physical room-loop
  closure and fast-turn mapping quality remain to be measured by operator.

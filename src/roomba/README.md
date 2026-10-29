# Roomba serial interface

The driver sends Query List `[149, 3, 0, 43, 44]` at a configurable 10 Hz.
Each complete reply is 30 bytes: group 0 telemetry (26), left encoder (2),
then right encoder (2), with multi-byte fields high byte first.

Position comes exclusively from signed modular encoder differences, wheel
circumference, and wheel track, using differential-drive arc integration.
The first sample sets a baseline. Both counter rollovers are handled;
implausible jumps or gaps over two seconds rebaseline without teleporting the
pose. `/odom` includes encoder-derived linear and angular velocity.

Geometry is editable in `config/roomba_params.yaml`: nominal diameter 72 mm,
508.8 counts/revolution, and track 235 mm, plus left/right calibration scales.
Track is the distance across the robot between wheel contact centers. Verify
geometry with measured straight travel and turns. The Create 2 is based on the
650 ([iRobot documentation](https://github.com/iRobotSTEM/CreateDocs)). Encoder
units and direction limitations are described in the
[iRobot OI specification](https://manuals.plus/m/9c9a46431d13383f099cc0b6743fceff8e55582c5fb593b84c16198a448c77a6.pdf).

The dashboard caches telemetry and refreshes its display every five seconds.
Use **Request now** in the dashboard or call the ROS service for an immediate
packet:

```bash
ros2 service call /request_telemetry roomba_interfaces/srv/RequestTelemetry "{}"
```

The service joins a pending encoder query or starts one and returns only the
26-byte group-0 portion. It never sends a separate query while another is in
flight. Partial replies accumulate until complete; timeout/invalid replies
cause input draining before retry. Raw sensor query/stream commands through
the serial console are rejected because the driver owns reply framing.

| Topic | Contents |
| --- | --- |
| `serial_rx` | Original raw serial chunks, including all query bytes. |
| `roomba/sensors` | Complete group-0 telemetry for the web app and SLAM bumper handling. |
| `roomba/encoder_counts` | `UInt16MultiArray` `[left, right]` raw 16-bit patterns. |
| `odom` | Encoder-derived `nav_msgs/Odometry`. |

`/cmd_vel` (`geometry_msgs/Twist`) is converted to Roomba drive-direct
(`serial_tx`, opcode 145). Linear and angular limits are applied from
`roomba_params.yaml`; a 0.5 second command watchdog publishes a stop command.
The watchdog is a software safety layer and does not replace an emergency stop.

Wake the robot with CLEAN if needed. Startup sends Start, waits two seconds,
enters Safe mode, and sends stop. Ctrl+C sends stop and closes the port.
Missing replies produce a rate-limited warning, not invented encoder motion.

Wheel slip still causes odometry error. Firmware infers encoder direction from
motor commands, so manually pushing the robot opposite its commanded direction
can also produce wrong signs. LiDAR agreement checks remain necessary.

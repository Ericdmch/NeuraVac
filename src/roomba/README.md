# Roomba serial interface

`roomba_node` owns the Roomba Open Interface serial connection. It starts in
safe mode, forwards `serial_tx` / `serial_rx`, and samples OI sensor packet 0
ten times per second by default (configurable with `sensor_query_hz`). Packet 0
is 26 bytes and contains signed incremental distance and angle readings; the
node integrates those into `/odom` for the LiDAR scan matcher.

The dashboard caches telemetry and refreshes its display every five seconds.
Use **Request now** in the dashboard or call the ROS service for an immediate
packet:

```bash
ros2 service call /request_telemetry roomba_interfaces/srv/RequestTelemetry "{}"
```

This service sends the OI Sensors command `[142, 0]` and returns the complete
26-byte packet. The background
requests remain enabled for odometry and use the same small command and
26-byte response. The [SCI manual](../../docs/Roomba/Roomba_SCI_manual.md)
documents packet sizes, signed values, drive commands, LEDs, and songs.

The `wheel_track_m` setting in `config/roomba_params.yaml` defaults to the
SCI's nominal 0.258 m spacing. Wheel track means the distance across the robot
between the centers of the left and right wheel contact patches. Measuring it
lets the node scale reported turn angle by `0.258 / wheel_track_m`; the default
leaves SCI angle unchanged. It does not compensate for wheel slip.

Wheel odometry can drift from wheel slip or uneven floors. SLAM uses it only to
predict the next pose; LiDAR scan matching corrects that prediction before it
adds a scan to the map.

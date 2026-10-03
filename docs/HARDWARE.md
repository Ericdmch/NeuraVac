# Hardware and bringup

Target Pi 4 Model B 8 GB, ARM64 Ubuntu 24.04, ROS Jazzy. Use active cooling and a stable 5 V supply. There is no onboard CUDA dependency. Onboard control/navigation work is prioritized over perception and dashboard updates.

## Donor selection

Identify the model before wiring. Verify that it supports iRobot Open Interface, Drive Direct and required sensor packets. OI Create 2/Roomba 600 is the codec reference, not a claim that every Roomba supports it. The supplied robot.hardware.example.yaml is an unvalidated OI example with normalized area-score thresholds; tune those thresholds with real floor images before copying into robot.yaml. Set serial port, baud, wheel dimensions, ticks/revolution and encoder support in robot.yaml. A donor lacking encoders cannot provide the required odometry by pretending commands equal motion; use measured odometry or an MCU backend.

[iRobot's OI specification](https://cdn-shop.adafruit.com/datasheets/create_2_Open_Interface_Spec.pdf) describes safe-mode behavior, packet IDs and physical connections. Confirm donor-specific pinout and voltage. Use a 5 V TTL-to-USB adapter or proper level shifting; never connect 5 V serial directly to Pi GPIO, or RS-232 voltages to OI. Provide separate regulated Pi power; OI accessory power is limited and unsuitable for the Pi.

## Bringup sequence

1. Lift wheels and keep physical power cutoff accessible. Do not work near stairs.
2. Confirm serial voltage, baud, donor packet capabilities and battery capacity.
3. Enable physical read-only test: `NEURAVAC_SERIAL_PORT=/dev/ttyUSB0 NEURAVAC_ALLOW_HARDWARE_TESTS=1 make test-hardware`; the movement test also needs `NEURAVAC_WHEELS_ELEVATED=1`.
4. Verify wheel direction, encoder signs, scale and watchdog stopping with the wheels elevated.
5. Trigger bumper/cliff sensors safely with wheels elevated, confirm zero wheel and cleaning-motor commands. Never test cliffs by driving toward stairs.
6. Configure base→laser and base→camera transforms, camera intrinsics and floor projection. Verify odometry/TF timestamps and LiDAR freshness.
7. Provide trained, validated FloorMess ONNX weights; establish cable recall before autonomous floor trials.
8. Build static dashboard assets, install Pi software, launch hardware services. The robot must remain IDLE until explicitly started.
9. Begin supervised low-speed floor trials within a bounded room. Validate a physical stop when the Pi, Wi-Fi, or serial link fails.

## MCU bridge wire contract

The implemented host adapter sends newline-delimited JSON `{version:1,seq,op,params}` and expects `{version:1,seq,ok,result}` within the bounded serial timeout. Operations: `hello` negotiates a watchdog ≤500 ms by default; `velocity` uses linear_mps/angular_rps; `motors` uses vacuum/main_brush/side_brush; `stop` zeroes all actuators; `sensors` returns validated battery/bumper/cliff/encoders. A reply exceeding 4096 bytes or with wrong version/sequence is rejected. Firmware must default outputs OFF, independently expire wheel and cleaning commands, and prevent hazards locally. The host protocol is tested with fake firmware; no flashed MCU firmware or board electrical design is claimed.

## System service

`systemd/neuravac.service` assumes a dedicated `neuravac` user, repository at `/opt/neuravac`, and appropriate serial/video device group permissions. Adjust User, WorkingDirectory and ExecStart to the actual installation. Protect `.env` with mode0600. Install the service explicitly with `sudo cp systemd/neuravac.service /etc/systemd/system/`, `sudo systemctl daemon-reload`, `sudo systemctl enable --now neuravac`. It launches services, self-tests and stays IDLE. It does not authorize a cleaning mission after reboot.

Hardware validation is outstanding on this development host.

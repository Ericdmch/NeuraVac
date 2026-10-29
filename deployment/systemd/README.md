# Pi user services

These units record the configuration used on the current robot. Copy them to `~/.config/systemd/user/`, then run `systemctl --user daemon-reload` and `systemctl --user enable --now neuravac-dashboard.service neuravac-roomba.service neuravac-lidar.service`. Run `sudo loginctl enable-linger neuravac` once to start user services without logging in. They expect the `neuravac` account, `~/Neuravac` ROS install, and `~/neuravac-web-venv`.

The identical CH340 adapters lack unique serial numbers. The Roomba and LiDAR units use the physical USB paths recorded on this Pi; check and update them if the adapters move. Do not use the shared `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` to distinguish them. Existing system-wide `/dev/neuravac_*` udev aliases may refer to older port assignments; these services bypass those aliases.

The dashboard service starts without vision, LiDAR launch, or SLAM. The separate LiDAR service publishes raw points; mapping and camera are not enabled by these units. Check `systemctl --user status` and `/telemetry` after startup. A connected ROS bridge alone does not prove the robot is online.

# COIN-D6 LiDAR development references

References and vendor tools for hardware integration, serial-protocol implementation, ROS integration, and bench testing.

## Hardware integration

- [Direct Raspberry Pi UART connection: wiring, power, serial setup, and Pi 4/5 differences](raspberry-pi-uart.md)
- [Instruction manual: wiring, power, dimensions, mounting, and coordinate system](COIN-D6%20Instruction%20Manual.md)
- [A1 hardware specification: original manufacturer specifications](1%20D6%20LiDAR%20Manual/COIN-D6%20Single-Line%20LiDAR%20Specification%20Sheet%20A1.md)
- [Laser-safety test report: emission measurements, fault tests, and labeling](1%20D6%20LiDAR%20Manual/COIN-D6%20D6A%20LiDAR%20%28CSPC-EN%29%20Laser%20Safety%20Test%2025.07.22.md)

## Protocol and software

- [English protocol specification: commands, packets, angles, intensity, and checksum](1%20D6%20LiDAR%20Manual/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29.md)
- [Chinese protocol specification: original equations and diagrams for cross-checking](1%20D6%20LiDAR%20Manual/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0.md)
- [Checksum verification example (calibration.py)](4%20Windows%20software/calibration.md)
- [ROS1/ROS2 setup guide](2%20ROS%20and%20ROS2%20feature%20pack%20information/Tucker%20Innovations%20%20Guoke%20Optoelectronics%20D6%20ROS%20Driver%20Package%20User%20Guide%20V1.0.md)
- [ROS1 driver source and build configuration](2%20ROS%20and%20ROS2%20feature%20pack%20information/cspc_lidar_sdk_ros1_0802.md)
- [ROS2 driver source and build configuration](2%20ROS%20and%20ROS2%20feature%20pack%20information/m1ct_d4_ros2_v16.md)

The ROS2 package retains D2/D4 names in places. It is kept as vendor-supplied implementation reference; the package name alone does not establish COIN-D6 compatibility.

## Bench tools and USB drivers

- [COIN-D6 Windows viewer: vendor archive and executable inventory](4%20Windows%20software/New%20Host%20Computer.md)
- [COIN-D6 Windows viewer: English guide, logging, mapping, and troubleshooting](4%20Windows%20software/New%20Host%20Computer.contents/Witmotion_LiDAR_Manual_EN.md)
- [CH340 Windows USB-to-serial driver](4%20Windows%20software/CH340%20driver/CH340_WINDOWS.md)
- [CH341 Linux USB-to-serial driver source](4%20Windows%20software/CH340%20driver/CH341SER_LINUX.md)

## Retained sources

PDF references retain extracted text and page images, including technical drawings and equations. Original PDFs, source archives, drivers, and the checksum script remain in `_originals/`. [manifest.json](manifest.json) records the retained source hashes.

## Curation

Removed the older CSPC V2.1.36 Windows viewer bundle, its sample scan and bundled runtime libraries, and both copies of its COIN-D4 operation guide. The newer viewer explicitly documents COIN-D6 support and covers point-cloud inspection and data logging.

Removed the expanded Chinese copy of the newer viewer manual because the retained English guide covers the same functions. The vendor viewer archive is kept intact for use, so it still contains the Chinese PDF. Both protocol specifications are retained because the original Chinese equations help interpret the English conversion. The laser-safety report is retained for hardware integration reference.

The original download folder is unchanged.

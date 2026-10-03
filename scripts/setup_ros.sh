#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f /opt/ros/jazzy/setup.bash ]] || { echo 'Install ROS 2 Jazzy on Ubuntu 24.04: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html' >&2; exit 1; }
source /opt/ros/jazzy/setup.bash
# Distro ABI plus isolated dependencies, with explicit colcon interpreter.
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -e '.[dev,hardware,vision]'
.venv/bin/python /usr/bin/colcon build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install
.venv/bin/python /usr/bin/colcon test --build-base ros2_ws/build --install-base ros2_ws/install --event-handlers console_direct+
.venv/bin/python /usr/bin/colcon test-result --test-result-base ros2_ws/build --verbose

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_ID:-}" == 24.04 && "$(uname -m)" == aarch64 ]] || { echo 'Target is ARM64 Ubuntu 24.04 on Raspberry Pi 4.' >&2; exit 1; }
sudo apt-get update
sudo apt-get install -y curl ca-certificates gnupg python3-venv python3-pip ffmpeg
if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  sudo mkdir -p /usr/share/keyrings
  curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo gpg --dearmor -o /usr/share/keyrings/ros2-archive-keyring.gpg
  printf 'deb [arch=arm64 signed-by=/usr/share/keyrings/ros2-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main\n' | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
  sudo apt-get update
fi
sudo apt-get install -y ros-jazzy-ros-base ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox ros-jazzy-usb-cam ros-jazzy-cv-bridge ros-jazzy-tf-transformations ros-jazzy-robot-state-publisher ros-jazzy-rosbag2 python3-colcon-common-extensions
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -e '.[hardware,vision]'
source /opt/ros/jazzy/setup.bash
.venv/bin/python /usr/bin/colcon build --base-paths ros2_ws/src --build-base ros2_ws/build --install-base ros2_ws/install --symlink-install
if [[ ! -f dashboard/frontend/dist/index.html ]]; then
  echo 'Copy dashboard/frontend/dist from a workstation after npm ci && npm run build. Node is not needed at runtime.'
fi
printf 'Installed. Set config/robot.yaml to your verified backend, calibrate sensors, then ./scripts/start_robot.sh. Boot remains IDLE.\n'

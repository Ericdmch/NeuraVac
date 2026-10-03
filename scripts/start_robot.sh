#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${NEURAVAC_MODE:-simulation}"
if [[ "$mode" == simulation ]]; then
  exec .venv/bin/python -m neuravac_core.cli dashboard "$@"
fi
[[ "$mode" == hardware || "$mode" == mapping || "$mode" == saved_map || "$mode" == demo ]] || { echo 'Invalid NEURAVAC_MODE' >&2; exit 2; }
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export PATH="$(pwd)/.venv/bin:$PATH"
export PYTHONPATH="$(pwd):$(.venv/bin/python -c 'import sysconfig; print(sysconfig.get_path("purelib"))'):${PYTHONPATH:-}"
launch_mode=hardware
mapping="${NEURAVAC_MAPPING:-true}"
if [[ "$mode" == demo ]]; then launch_mode=demo; mapping=false; fi
if [[ "$mode" == saved_map ]]; then mapping=false; fi
exec ros2 launch neuravac_bringup bringup.launch.py mode:="$launch_mode" mapping:="$mapping" robot_config:="$(pwd)/config/robot.yaml" perception_config:="$(pwd)/config/perception.yaml" navigation_config:="$(pwd)/config/navigation.yaml" static_dir:="$(pwd)/dashboard/frontend/dist" "$@"

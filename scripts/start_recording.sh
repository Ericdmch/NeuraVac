#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p recordings
if [[ "${NEURAVAC_RECORD_ROS:-0}" == 1 ]]; then
  command -v ros2 >/dev/null || { echo 'Source ROS Jazzy before recording ROS topics.' >&2; exit 1; }
  exec ros2 bag record -o "recordings/ros-$(date +%Y%m%d-%H%M%S)" /scan /camera/image_raw /base/bumper /base/cliff /base/battery /base/encoders /odom /map /semantic_map /world_model /mission_state /cleaning_status /safety_state /cmd_vel /nav/cmd_vel /base/vacuum_cmd /ai_decision
fi
exec .venv/bin/python -m neuravac_core.cli demo --record "recordings/demo-$(date +%Y%m%d-%H%M%S).jsonl" "$@"

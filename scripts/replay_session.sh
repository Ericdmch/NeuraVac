#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $# -eq 1 ]] || { echo 'Usage: replay_session.sh <session.jsonl or rosbag directory>' >&2; exit 2; }
if [[ -d "$1" ]]; then
  echo 'ROS replay does not launch the base driver. Use a separate ROS domain with base processes stopped.' >&2
  export ROS_DOMAIN_ID="${NEURAVAC_REPLAY_DOMAIN:-99}"
  exec ros2 bag play "$1" --clock
fi
exec .venv/bin/python -m neuravac_core.cli replay "$1"

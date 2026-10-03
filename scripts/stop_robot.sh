#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${NEURAVAC_MODE:-simulation}" == simulation ]]; then
  .venv/bin/python - <<'PY'
import os,httpx
headers={}
if os.getenv('NEURAVAC_API_TOKEN'): headers['Authorization']='Bearer '+os.environ['NEURAVAC_API_TOKEN']
response=httpx.post('http://127.0.0.1:8000/api/mission/estop',headers=headers,timeout=2)
response.raise_for_status()
print('Emergency stop latched. Explicit healthy reset required.')
PY
else
  source /opt/ros/jazzy/setup.bash
  source ros2_ws/install/setup.bash
  timeout 5 ros2 service call /emergency_stop std_srvs/srv/Trigger '{}'
fi

# Source after /opt/ros/jazzy/setup.bash and before the workspace overlay.
NEURAVAC_RUNTIME="$HOME/neuravac-slam-runtime/root"
if [ -d "$NEURAVAC_RUNTIME/opt/ros/jazzy" ]; then
  export AMENT_PREFIX_PATH="$NEURAVAC_RUNTIME/opt/ros/jazzy:${AMENT_PREFIX_PATH:-}"
  export LD_LIBRARY_PATH="$NEURAVAC_RUNTIME/opt/ros/jazzy/lib:$NEURAVAC_RUNTIME/usr/lib/aarch64-linux-gnu:${LD_LIBRARY_PATH:-}"
  export PYTHONPATH="$NEURAVAC_RUNTIME/opt/ros/jazzy/lib/python3.12/site-packages:${PYTHONPATH:-}"
fi

#!/usr/bin/env bash
set -e
source /opt/ros/jazzy/setup.bash
source "$HOME/Neuravac/src/neuravac_mapping/deployment/runtime-env.sh"
source "$HOME/Neuravac/install/setup.bash"
exec ros2 launch bringup robot.launch.py use_vision:=false use_web:=false slam_backend:=toolbox

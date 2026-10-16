"""Start the Roomba node with its parameters:

    ros2 launch neuravac_robot roomba.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    params = os.path.join(
        get_package_share_directory('neuravac_robot'), 'config', 'roomba.yaml')

    return LaunchDescription([
        Node(
            package='neuravac_robot',
            executable='roomba_node',   # the name registered in setup.py
            name='roomba',              # must match the top key in the YAML
            parameters=[params],
            output='screen',
        ),
    ])

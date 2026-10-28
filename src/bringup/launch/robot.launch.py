"""Start the whole NeuraVac robot: roomba, lidar, vision and the web dashboard.

    ros2 launch bringup robot.launch.py
    ros2 launch bringup robot.launch.py use_vision:=false      # no camera model
    ros2 launch bringup robot.launch.py use_lidar:=false use_roomba:=false

Each node reads its parameters from the config/ YAML of its own package. The
USB devices are referenced by the stable /dev/neuravac_* names that
`ros2 run bringup neuravac_udev_setup` creates, so they no longer depend on the
order the cables were plugged in.

Only one process can capture from the webcam. When vision runs it owns the
camera and the dashboard shows the frames vision publishes on
camera/image/compressed; with use_vision:=false the dashboard opens the webcam
itself.
"""

import os
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

TRUE_VALUES = ('1', 'true', 'yes', 'on')


def package_config(package, filename):
    return os.path.join(get_package_share_directory(package), 'config', filename)


def enabled(context, name):
    return LaunchConfiguration(name).perform(context).strip().lower() in TRUE_VALUES


def ros_python_environment():
    """Expose active venv packages to ROS nodes while keeping ROS's Python."""
    virtual_env = os.environ.get('VIRTUAL_ENV')
    if not virtual_env:
        return {}

    version = f'python{sys.version_info.major}.{sys.version_info.minor}'
    site_packages = os.path.join(virtual_env, 'lib', version, 'site-packages')
    if not os.path.isdir(site_packages):
        return {}

    inherited_pythonpath = os.environ.get('PYTHONPATH', '')
    pythonpath = os.pathsep.join(
        path for path in (site_packages, inherited_pythonpath) if path
    )
    return {'PYTHONPATH': pythonpath}


def launch_setup(context):
    nodes = []

    if enabled(context, 'use_roomba'):
        nodes.append(Node(
            package='roomba', executable='roomba_node', name='roomba_node',
            parameters=[package_config('roomba', 'roomba_params.yaml')],
            output='screen',
            # Exits when the serial port is missing; retry so plugging it in later works.
            respawn=True, respawn_delay=3.0,
        ))

    if enabled(context, 'use_lidar'):
        nodes.append(Node(
            package='lidar', executable='lidar_node', name='lidar_node',
            parameters=[package_config('lidar', 'lidar_params.yaml')],
            output='screen',
            respawn=True, respawn_delay=3.0,
        ))

    use_vision = enabled(context, 'use_vision')
    if use_vision:
        nodes.append(Node(
            package='vision', executable='vision_node', name='vision_node',
            parameters=[package_config('vision', 'vision_params.yaml')],
            output='screen',
            additional_env=ros_python_environment(),
        ))

    if enabled(context, 'use_web'):
        camera_env = {
            'NEURAVAC_CAMERA_SOURCE': 'ros' if use_vision else 'device',
            'NEURAVAC_CAMERA_DEVICE': LaunchConfiguration('camera_device').perform(context),
        }
        nodes.append(Node(
            package='web', executable='web_node', name='web_node',
            output='screen',
            additional_env=camera_env,
        ))

    return nodes


def generate_launch_description():
    arguments = [
        DeclareLaunchArgument('use_roomba', default_value='true',
                              description='Start the Roomba serial node'),
        DeclareLaunchArgument('use_lidar', default_value='true',
                              description='Start the LiDAR node'),
        DeclareLaunchArgument('use_vision', default_value='true',
                              description='Start the camera/detection node '
                                          '(it then owns the webcam)'),
        DeclareLaunchArgument('use_web', default_value='true',
                              description='Start the Flask dashboard on port 5000'),
        DeclareLaunchArgument('camera_device', default_value='/dev/neuravac_camera',
                              description='Webcam used by the dashboard when '
                                          'use_vision:=false'),
    ]
    return LaunchDescription(arguments + [OpaqueFunction(function=launch_setup)])

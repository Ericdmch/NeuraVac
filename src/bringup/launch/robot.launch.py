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
from datetime import datetime

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
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

    if enabled(context, 'use_diagnostics'):
        diagnostics_dir = os.path.abspath(os.path.expanduser(
            LaunchConfiguration('diagnostics_dir').perform(context)
        ))
        os.makedirs(diagnostics_dir, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        bag_path = os.path.join(diagnostics_dir, f'neuravac_{stamp}')
        nodes.append(ExecuteProcess(
            cmd=[
                'ros2', 'bag', 'record', '-o', bag_path,
                '/lidar_points', '/odom', '/slam/pose', '/serial_rx', '/serial_tx',
                '/roomba/sensors', '/roomba/encoder_counts', '/slam/status', '/slam/diagnostics',
            ],
            output='screen',
        ))

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

        if enabled(context, 'use_slam'):
            backend = LaunchConfiguration('slam_backend').perform(context)
            if backend == 'toolbox':
                nodes.append(IncludeLaunchDescription(PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory('neuravac_mapping'),
                                 'launch', 'mapping.launch.py'))))
            elif backend == 'legacy':
                nodes.append(Node(
                    package='neuravac_slam', executable='slam_node', name='neuravac_slam',
                    parameters=[package_config('neuravac_slam', 'slam_params.yaml')],
                    output='screen', respawn=True, respawn_delay=3.0))
            else:
                raise ValueError('slam_backend must be toolbox or legacy')

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

    if enabled(context, 'use_navigation'):
        nodes.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('bringup'), 'launch',
                'navigation.launch.py')),
            launch_arguments={
                'map': LaunchConfiguration('map').perform(context),
                'rviz': LaunchConfiguration('use_rviz').perform(context),
            }.items()))

    return nodes


def generate_launch_description():
    arguments = [
        DeclareLaunchArgument('slam_backend', default_value='toolbox'),
        DeclareLaunchArgument('use_roomba', default_value='true',
                              description='Start the Roomba serial node'),
        DeclareLaunchArgument('use_lidar', default_value='true',
                              description='Start the LiDAR node'),
        DeclareLaunchArgument('use_slam', default_value='true',
                              description='Build a 2D map from LiDAR scans'),
        DeclareLaunchArgument('use_vision', default_value='true',
                              description='Start the camera/detection node '
                                          '(it then owns the webcam)'),
        DeclareLaunchArgument('use_web', default_value='true',
                              description='Start the Flask dashboard on port 5000'),
        DeclareLaunchArgument('camera_device', default_value='/dev/neuravac_camera',
                              description='Webcam used by the dashboard when '
                                          'use_vision:=false'),
        DeclareLaunchArgument('use_diagnostics', default_value='false',
                              description='Record LiDAR, odometry, SLAM pose, '
                                          'and Roomba serial topics to a rosbag'),
        DeclareLaunchArgument('diagnostics_dir', default_value='~/Neuravac/logs',
                              description='Parent folder for diagnostic rosbag runs'),
        DeclareLaunchArgument('use_navigation', default_value='false',
                              description='Start Nav2 against SLAM Toolbox /map'),
        DeclareLaunchArgument('use_rviz', default_value='false',
                              description='Start RViz2 with the Nav2 display config'),
        DeclareLaunchArgument('map', default_value='',
                              description='Saved map YAML for localization; empty uses live SLAM'),
    ]
    return LaunchDescription(arguments + [OpaqueFunction(function=launch_setup)])

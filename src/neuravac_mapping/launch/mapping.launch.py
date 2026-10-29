from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.parameter_descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory('neuravac_mapping'))
    toolbox = Path(get_package_share_directory('slam_toolbox'))
    return LaunchDescription([
        DeclareLaunchArgument('lidar_x_m', default_value='0.0'),
        DeclareLaunchArgument('lidar_y_m', default_value='0.0'),
        DeclareLaunchArgument('lidar_yaw_rad', default_value='0.0'),
        Node(package='neuravac_mapping', executable='scan_bridge', output='screen',
             respawn=True, respawn_delay=2., parameters=[{
                 key: ParameterValue(LaunchConfiguration(key), value_type=float)
                 for key in ('lidar_x_m', 'lidar_y_m', 'lidar_yaw_rad')}]),
        Node(package='neuravac_mapping', executable='dashboard_bridge', output='screen', respawn=True, respawn_delay=2.),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(
            toolbox / 'launch/online_async_launch.py')),
            launch_arguments={'use_sim_time': 'false',
                              'slam_params_file': str(share / 'config/toolbox.yaml')}.items()),
    ])

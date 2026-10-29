"""Start Nav2 against the active SLAM Toolbox map (or a saved map)."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def setup(context):
    share = get_package_share_directory('bringup')
    params = os.path.join(share, 'config', 'nav2_params.yaml')
    map_yaml = LaunchConfiguration('map').perform(context).strip()
    nodes = []
    lifecycle = [
        'controller_server', 'planner_server', 'behavior_server',
        'bt_navigator', 'waypoint_follower', 'velocity_smoother',
    ]
    if map_yaml:
        nodes.append(Node(
            package='nav2_map_server', executable='map_server', name='map_server',
            parameters=[params, {'yaml_filename': map_yaml}], output='screen'))
        lifecycle.insert(0, 'map_server')
    for name in lifecycle:
        nodes.append(Node(
            package='nav2_' + ('waypoint_follower' if name == 'waypoint_follower' else name),
            executable=name, name=name, parameters=[params], output='screen'))
    nodes.append(Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        parameters=[{'autostart': True, 'node_names': lifecycle}],
        output='screen'))
    if LaunchConfiguration('rviz').perform(context).lower() in ('true', '1', 'yes'):
        nodes.append(Node(
            package='rviz2', executable='rviz2',
            arguments=['-d', os.path.join(share, 'rviz', 'nav2.rviz')],
            output='screen'))
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'map', default_value='',
            description='Saved map YAML. Leave empty when SLAM Toolbox publishes /map.'),
        DeclareLaunchArgument('rviz', default_value='false'),
        OpaqueFunction(function=setup),
    ])

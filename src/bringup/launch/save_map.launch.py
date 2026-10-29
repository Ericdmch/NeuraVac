"""Persist the current active SLAM Toolbox /map using Nav2's map saver."""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('output', default_value=os.path.expanduser(
            '~/Neuravac/maps/room')),
        DeclareLaunchArgument('map_topic', default_value='/map'),
        ExecuteProcess(
            cmd=['ros2', 'run', 'nav2_map_server', 'map_saver_cli',
                 '-f', LaunchConfiguration('output'),
                 '--ros-args', '-r',
                 ['map:=', LaunchConfiguration('map_topic')]],
            output='screen'),
    ])

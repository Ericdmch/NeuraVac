"""Experimental navigation nodes. Motion remains disabled by default."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = Path(get_package_share_directory('neuravac_mapping'))
    config = str(share / 'config' / 'autonomy_nav2.yaml')
    tree = str(share / 'behavior_trees' / 'explore_no_recovery.xml')
    return LaunchDescription([
        DeclareLaunchArgument('enable_motion', default_value='false'),
        DeclareLaunchArgument('enable_dashboard', default_value='true'),
        Node(package='nav2_controller', executable='controller_server', output='screen',
             parameters=[config], remappings=[('cmd_vel', 'autonomy/nav_cmd_vel')]),
        Node(package='nav2_planner', executable='planner_server', output='screen', parameters=[config]),
        Node(package='nav2_bt_navigator', executable='bt_navigator', output='screen',
             parameters=[config, {'default_nav_to_pose_bt_xml': tree}]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_autonomy', output='screen', parameters=[{
                 'autostart': True, 'node_names': ['controller_server', 'planner_server', 'bt_navigator']}]),
        Node(package='neuravac_mapping', executable='autonomy_node', output='screen', parameters=[{
            'enable_motion': ParameterValue(LaunchConfiguration('enable_motion'), value_type=bool),
            'behavior_tree': tree}]),
        Node(package='neuravac_mapping', executable='autonomy_dashboard', output='screen',
             condition=IfCondition(LaunchConfiguration('enable_dashboard'))),
    ])

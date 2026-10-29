from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="neuravac_ros",
            executable="roomba_bridge",
            name="roomba_serial_bridge",
            output="screen",
        ),
    ])

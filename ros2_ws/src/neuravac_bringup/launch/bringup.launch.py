"""Connected Jazzy launch. Hardware only starts via an explicit mode and backend."""

import os
import tempfile
from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter, SetRemap

from neuravac_core.config import load_config


def merged_parameters(defaults, overrides):
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(defaults.get(key), dict):
            merged_parameters(defaults[key], value)
        else:
            defaults[key] = value
    return defaults


def launch_nodes(context):
    def value(name):
        return LaunchConfiguration(name).perform(context)

    mode = value("mode")
    mapping = value("mapping") == "true"
    robot = value("robot_config")
    backend = value("backend")
    if mode not in ("simulation", "hardware", "demo"):
        raise ValueError("mode must be simulation, hardware or demo")
    config = load_config(robot)
    if mode == "hardware" and (backend or config.backend) not in ("roomba_oi", "mcu_bridge"):
        raise ValueError(
            "hardware mode requires an explicit serial backend in shared robot_config or backend argument"
        )
    simulated = mode in ("simulation", "demo")
    if simulated and mapping:
        raise ValueError(
            "labeled simulation publishes its known map; use mapping on physical sensor input"
        )
    nav_share = get_package_share_directory("nav2_bringup")
    params = yaml.safe_load((Path(nav_share) / "params/nav2_params.yaml").read_text())
    overrides = yaml.safe_load(Path(value("navigation_config")).read_text())
    params = merged_parameters(params, overrides)
    # The footprint and velocity limits derive from the same typed robot configuration.
    for key in ("local_costmap", "global_costmap"):
        params[key][key]["ros__parameters"]["robot_radius"] = config.robot_radius_m
    controller = params["controller_server"]["ros__parameters"]["FollowPath"]
    controller["max_vel_x"] = min(controller["max_vel_x"], config.safety.max_linear_mps)
    controller["max_speed_xy"] = controller["max_vel_x"]
    controller["max_vel_theta"] = min(controller["max_vel_theta"], config.safety.max_angular_rps)
    smoother = params["velocity_smoother"]["ros__parameters"]
    smoother["max_velocity"] = [controller["max_vel_x"], 0.0, controller["max_vel_theta"]]
    temp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", prefix="neuravac-nav-", delete=False
    )
    yaml.safe_dump(params, temp)
    temp.close()
    cleanup = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                OpaqueFunction(
                    function=lambda _: os.unlink(temp.name) if os.path.exists(temp.name) else []
                )
            ]
        )
    )
    common = {"robot_config": robot, "use_sim_time": False}
    nodes = [cleanup]

    def adapter(package, exe, extra=None):
        return Node(
            package="neuravac_" + package,
            executable=exe,
            parameters=[dict(common, **(extra or {}))],
            output="screen",
        )

    nodes.append(
        adapter("base", "simulation_node" if simulated else "base_node", {"backend": backend})
    )
    for package in ("safety", "semantic_map", "world_model", "cleaning"):
        nodes.append(adapter(package, package + "_node"))
    nodes.append(
        adapter(
            "perception",
            "perception_node",
            {
                "perception_config": value("perception_config"),
                "provider": "sim" if simulated else value("provider"),
                "replay_path": value("replay_path"),
            },
        )
    )
    cloud = value("cloud_enabled") == "true"
    nodes.append(adapter("cloud", "cloud_node", {"enabled": cloud}))
    nodes.append(adapter("planner", "planner_node", {"cloud_enabled": cloud}))
    if value("dashboard") == "true":
        nodes.append(
            adapter(
                "dashboard",
                "dashboard_node",
                {
                    "mode": "simulation" if simulated else "hardware",
                    "static_dir": value("static_dir"),
                },
            )
        )

    def static(parent, child, x, y, z, roll=0, pitch=0, yaw=0):
        return Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=[
                "--x",
                str(x),
                "--y",
                str(y),
                "--z",
                str(z),
                "--roll",
                str(roll),
                "--pitch",
                str(pitch),
                "--yaw",
                str(yaw),
                "--frame-id",
                parent,
                "--child-frame-id",
                child,
            ],
        )

    nodes += [
        static("base_link", "base_footprint", 0, 0, 0),
        static("base_link", "laser_frame", float(value("laser_x")), 0, float(value("laser_z"))),
    ]
    # Deployers must replace these frame offsets and optical calibration with measured values.
    nodes += [
        static("base_link", "camera_link", float(value("camera_x")), 0, float(value("camera_z"))),
        static("camera_link", "camera_optical_frame", 0, 0, 0, -1.57079632679, 0, -1.57079632679),
    ]
    if simulated:
        nodes.append(static("map", "odom", 0, 0, 0))
    elif mapping:
        nodes.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    str(
                        Path(get_package_share_directory("slam_toolbox"))
                        / "launch/online_async_launch.py"
                    )
                ),
                launch_arguments={"slam_params_file": temp.name, "use_sim_time": "false"}.items(),
            )
        )
    else:
        if not value("map"):
            raise ValueError(
                "saved-map hardware requires map:=/absolute/path/map.yaml and AMCL initial pose"
            )
        nodes.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    str(Path(nav_share) / "launch/localization_launch.py")
                ),
                launch_arguments={
                    "map": value("map"),
                    "params_file": temp.name,
                    "use_sim_time": "False",
                    "autostart": "True",
                    "use_composition": "False",
                }.items(),
            )
        )
    if not simulated and value("lidar_launch"):
        nodes.append(IncludeLaunchDescription(PythonLaunchDescriptionSource(value("lidar_launch"))))
    if not simulated and value("start_camera") == "true":
        nodes.append(
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                parameters=[
                    {
                        "video_device": value("camera_device"),
                        "image_width": 320,
                        "image_height": 320,
                        "framerate": 10.0,
                        "camera_frame_id": "camera_optical_frame",
                    }
                ],
                remappings=[("image_raw", "/camera/image_raw")],
            )
        )
    # Preserve Nav2's controller -> smoother -> collision monitor routing.
    # The final collision_monitor output topic is /nav/cmd_vel in navigation.yaml.
    nodes.append(
        GroupAction(
            [
                SetParameter(name="bond_timeout", value=30.0),
                SetRemap(src="docking_server:cmd_vel", dst="/nav/cmd_vel"),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        str(Path(nav_share) / "launch/navigation_launch.py")
                    ),
                    launch_arguments={
                        "params_file": temp.name,
                        "use_sim_time": "False",
                        "autostart": "True",
                        "use_composition": "False",
                    }.items(),
                ),
            ]
        )
    )
    nodes += [
        Node(
            package="nav2_map_server",
            executable="costmap_filter_info_server",
            name="semantic_filter_info",
            parameters=[temp.name],
        ),
        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="semantic_filter_lifecycle",
            parameters=[{"autostart": True, "node_names": ["semantic_filter_info"]}],
        ),
    ]
    return nodes


def generate_launch_description():
    share = Path(get_package_share_directory("neuravac_bringup"))
    defaults = {
        "mode": "simulation",
        "mapping": "false",
        "backend": "",
        "robot_config": str(share / "config/robot.yaml"),
        "perception_config": str(share / "config/perception.yaml"),
        "navigation_config": str(share / "config/navigation.yaml"),
        "provider": "onnx",
        "replay_path": "",
        "cloud_enabled": "false",
        "dashboard": "true",
        "static_dir": "",
        "map": "",
        "lidar_launch": "",
        "start_camera": "false",
        "camera_device": "/dev/video0",
        "laser_x": "0.0",
        "laser_z": "0.08",
        "camera_x": "0.08",
        "camera_z": "0.18",
    }
    return LaunchDescription(
        [DeclareLaunchArgument(name, default_value=value) for name, value in defaults.items()]
        + [OpaqueFunction(function=launch_nodes)]
    )

# ruff: noqa: E402
"""Actual rclpy transport tests; run only inside Jazzy via colcon test."""

import time
from pathlib import Path

import pytest

rclpy = pytest.importorskip("rclpy")
from geometry_msgs.msg import Twist
from neuravac_base.contracts import envelope
from neuravac_safety.node import SafetyNode
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import String
from std_srvs.srv import Trigger


def test_ros_arbiter_stops_on_dead_heartbeat_and_latches():
    from ament_index_python.packages import get_package_share_directory

    config = Path(get_package_share_directory("neuravac_bringup")) / "config/robot.yaml"
    rclpy.init(args=["--ros-args", "-p", f"robot_config:={config}"])
    safety = SafetyNode()
    probe = Node("safety_transport_probe")
    executor = SingleThreadedExecutor()
    executor.add_node(safety)
    executor.add_node(probe)
    outputs = []
    probe.create_subscription(Twist, "/cmd_vel", lambda m: outputs.append(m.linear.x), 10)
    pubs = {
        topic: probe.create_publisher(type_, topic, 10)
        for topic, type_ in [
            ("/base/status", String),
            ("/scan", LaserScan),
            ("/camera/image_raw", Image),
            ("/mission/heartbeat", String),
            ("/nav/cmd_vel", Twist),
        ]
    }

    def pump(duration, heartbeat=True):
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            stamp = probe.get_clock().now().to_msg()
            now = stamp.sec + stamp.nanosec / 1e9
            from neuravac_core.models import BatteryState, BumperState, CliffState

            pubs["/base/status"].publish(
                String(
                    data=envelope(
                        "base",
                        now,
                        {
                            "connected": True,
                            "odometry_supported": True,
                            "battery": BatteryState().model_dump(),
                            "bumper": BumperState().model_dump(),
                            "cliff": CliffState().model_dump(),
                        },
                    )
                )
            )
            scan = LaserScan()
            scan.header.stamp = stamp
            scan.angle_increment = 0.1
            scan.ranges = [2.0] * 10
            pubs["/scan"].publish(scan)
            image = Image()
            image.header.stamp = stamp
            image.width = 1
            image.height = 1
            image.data = b"\0\0\0"
            pubs["/camera/image_raw"].publish(image)
            if heartbeat:
                pubs["/mission/heartbeat"].publish(
                    String(data=envelope("heartbeat", now, {"state": "NAVIGATING"}))
                )
            velocity = Twist()
            velocity.linear.x = 0.1
            pubs["/nav/cmd_vel"].publish(velocity)
            executor.spin_once(timeout_sec=0.02)

    def service(name):
        client = probe.create_client(Trigger, name)
        assert client.wait_for_service(timeout_sec=2)
        future = client.call_async(Trigger.Request())
        executor.spin_until_future_complete(future, timeout_sec=2)
        assert future.done()
        return future.result()

    try:
        pump(1.5)
        assert any(v > 0.05 for v in outputs)
        pump(0.8, False)
        assert outputs[-1] == 0
        assert service("/emergency_stop").success
        pump(0.8)
        assert outputs[-1] == 0
        assert service("/safety/reset").success
        pump(0.3)
        assert outputs[-1] > 0.05
    finally:
        executor.shutdown()
        probe.destroy_node()
        safety.destroy_node()
        rclpy.shutdown()

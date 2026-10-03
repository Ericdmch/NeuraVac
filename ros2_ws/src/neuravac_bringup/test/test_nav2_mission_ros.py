# ruff: noqa: E402
"""Full labeled simulation chain with real Nav2. No hardware or cloud credentials."""

import os
import signal
import subprocess
import time

import pytest

rclpy = pytest.importorskip("rclpy")
from geometry_msgs.msg import Twist
from neuravac_base.contracts import decode
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from std_srvs.srv import Trigger


def test_nav2_cleaning_mission_completes(tmp_path):
    log = (tmp_path / "bringup.log").open("w")
    process = subprocess.Popen(
        [
            "ros2",
            "launch",
            "neuravac_bringup",
            "bringup.launch.py",
            "mode:=simulation",
            "dashboard:=false",
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    rclpy.init()
    node = Node("mission_integration_probe")
    states = []
    attempts = []
    velocities = []
    node.create_subscription(Twist, "/nav/cmd_vel", lambda msg: velocities.append(msg.linear.x), 10)

    def state(msg):
        states.append(
            decode(msg.data, "mission_state", node.get_clock().now().nanoseconds / 1e9, 2)[
                "payload"
            ]["state"]
        )

    def cleaning(msg):
        attempts.append(
            decode(msg.data, "cleaning_result", node.get_clock().now().nanoseconds / 1e9, 2)[
                "payload"
            ]
        )

    node.create_subscription(String, "/mission_state", state, 10)
    node.create_subscription(String, "/cleaning/result", cleaning, 10)

    def wait_for(predicate, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not predicate():
            if process.poll() is not None:
                break
            rclpy.spin_once(node, timeout_sec=0.1)
        if not predicate():
            log.flush()
            pytest.fail(f"\nStates ({len(states)}): {set(states)}\nAttempts ({len(attempts)}): {attempts}\n" + (tmp_path / "bringup.log").read_text()[-16000:])

    try:
        wait_for(lambda: "IDLE" in states, 60)
        assert "NAVIGATING" not in states  # Explicit start is mandatory.
        # The only actuator publisher is the arbiter. Nav2 retains its internal chain.
        wait_for(
            lambda: {info.node_name for info in node.get_publishers_info_by_topic("/cmd_vel")}
            == {"safety_arbiter"},
            30,
        )
        wait_for(
            lambda: {
                info.node_name for info in node.get_publishers_info_by_topic("/base/vacuum_cmd")
            }
            == {"safety_arbiter"},
            30,
        )
        wait_for(
            lambda: {info.node_name for info in node.get_publishers_info_by_topic("/cmd_vel_nav")}
            >= {
                "controller_server",
                "behavior_server",
            },
            30,
        )
        wait_for(
            lambda: {
                info.node_name for info in node.get_subscriptions_info_by_topic("/cmd_vel_nav")
            }
            >= {"velocity_smoother"},
            30,
        )
        wait_for(
            lambda: {
                info.node_name for info in node.get_publishers_info_by_topic("/cmd_vel_smoothed")
            }
            == {"velocity_smoother"},
            30,
        )
        wait_for(
            lambda: {
                info.node_name for info in node.get_subscriptions_info_by_topic("/cmd_vel_smoothed")
            }
            >= {"collision_monitor"},
            30,
        )
        nav2_active = node.create_client(Trigger, "/lifecycle_manager_navigation/is_active")
        assert nav2_active.wait_for_service(timeout_sec=15)

        def is_nav2_ready():
            fut = nav2_active.call_async(Trigger.Request())
            rclpy.spin_until_future_complete(node, fut, timeout_sec=0.5)
            return fut.done() and fut.result() is not None and fut.result().success

        wait_for(is_nav2_ready, 30)
        # Inject close obstacle scans before a stationary mission and prove the real
        # collision monitor suppresses a nonzero command from the smoothing stage.
        scan_pub = node.create_publisher(LaserScan, "/scan", 10)
        internal = node.create_publisher(Twist, "/cmd_vel_smoothed", 10)
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            scan = LaserScan()
            scan.header.stamp = node.get_clock().now().to_msg()
            scan.header.frame_id = "laser_frame"
            scan.angle_min = -0.2
            scan.angle_max = 0.2
            scan.angle_increment = 0.02
            scan.range_min = 0.01
            scan.range_max = 8.0
            scan.ranges = [0.08] * 21
            scan_pub.publish(scan)
            command = Twist()
            command.linear.x = 0.1
            internal.publish(command)
            rclpy.spin_once(node, timeout_sec=0.02)
        assert velocities and any(v == 0 for v in velocities)
        command = Twist()
        internal.publish(command)
        node.destroy_publisher(scan_pub)
        node.destroy_publisher(internal)
        cooldown = time.monotonic() + 0.8
        while time.monotonic() < cooldown:
            rclpy.spin_once(node, timeout_sec=0.05)
        start = node.create_client(Trigger, "/mission/start")
        assert start.wait_for_service(timeout_sec=3)
        future = start.call_async(Trigger.Request())
        wait_for(future.done, 5)
        assert future.result().success
        wait_for(lambda: "COMPLETE" in states, 180)
        assert "NAVIGATING" in states and "CLEANING" in states
        assert attempts and all(a["attempt"] is not None for a in attempts)
        assert sum(a["success"] for a in attempts) >= 2
        assert all(a["attempt"]["after_score"] < a["attempt"]["before_score"] for a in attempts)
        home = node.create_client(Trigger, "/mission/return_home")
        assert home.wait_for_service(timeout_sec=3)
        returned = home.call_async(Trigger.Request())
        wait_for(returned.done, 5)
        assert returned.result().success
        wait_for(lambda: "RETURNING_HOME" in states, 5)
        wait_for(lambda: states[-1] == "PAUSED", 120)
    finally:
        node.destroy_node()
        rclpy.shutdown()
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        log.close()

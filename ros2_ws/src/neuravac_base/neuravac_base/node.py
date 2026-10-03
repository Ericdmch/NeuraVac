"""The sole actuator consumer; serial IO and watchdog run outside ROS callbacks."""

import asyncio
import math
import threading
import time

from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.time import Time
from sensor_msgs.msg import BatteryState, JointState
from std_msgs.msg import Bool, String
from tf2_ros import TransformBroadcaster

from neuravac_base.contracts import decode
from neuravac_base.util import AsyncWorker, ConfigNode, spin
from neuravac_core.base.driver import BaseDriver
from neuravac_core.base.factory import create_base
from neuravac_core.safety import VelocityCommand


class BaseNode(ConfigNode):
    def __init__(self):
        super().__init__("base_driver")
        backend = self.declare_parameter("backend", "").value
        if backend:
            self.config.backend = backend
        if not self.config.encoder_supported:
            raise ValueError(
                "Nav2 deployment requires measured encoder odometry; configure an external odometry adapter"
            )
        if self.config.backend == "sim":
            raise ValueError(
                "use simulation_node so simulator sensors and motors share one environment"
            )
        self.initialize(create_base(self.config))

    def initialize(self, base):
        self.driver = BaseDriver(base, self.config)
        self.worker = AsyncWorker()
        self.lock = threading.Lock()
        self.command = None
        self.vacuum = (False, False, False)
        self.vacuum_stamp = 0.0
        self.snapshot = None
        self.sensor_stamp = 0.0
        self.pose = self.driver.pose.model_copy()
        self.encoder = None
        self.measured_velocity = (0.0, 0.0)
        self.previous_measurement = None
        self.fault = None
        self.status_pub = self.create_publisher(String, "/base/status", 10)
        self.battery_pub = self.create_publisher(BatteryState, "/battery_state", 10)
        self.base_battery_pub = self.create_publisher(BatteryState, "/base/battery", 10)
        self.encoder_pub = self.create_publisher(JointState, "/base/encoders", 10)
        self.bump_pub = self.create_publisher(Bool, "/base/bumper", 10)
        self.cliff_pub = self.create_publisher(Bool, "/base/cliff", 10)
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.tf = TransformBroadcaster(self)
        self.create_subscription(Twist, "/cmd_vel", self.velocity, 10)
        self.create_subscription(String, "/base/vacuum_cmd", self.cleaning, 10)
        self.io_future = self.worker.submit(self.run_io())
        self.watchdog_future = self.worker.submit(self.run_watchdog())
        self.create_timer(1 / self.config.control_hz, self.publish_sensors)

    def velocity(self, msg):
        try:
            command = VelocityCommand(
                source="navigation",
                linear_mps=msg.linear.x,
                angular_rps=msg.angular.z,
                timestamp=time.monotonic(),
            )
            if any(
                abs(value) > 1e-8
                for value in (msg.linear.y, msg.linear.z, msg.angular.x, msg.angular.y)
            ):
                raise ValueError("unsupported velocity axis")
            with self.lock:
                self.command = command
        except ValueError:
            with self.lock:
                self.command = None
            self.worker.submit(self.driver.stop())

    def cleaning(self, msg):
        try:
            payload = decode(msg.data, "vacuum", self.seconds(), self.config.safety.watchdog_s)[
                "payload"
            ]
            if set(payload) != {"vacuum", "main_brush", "side_brush"} or any(
                type(v) is not bool for v in payload.values()
            ):
                raise ValueError("invalid motor command")
            with self.lock:
                self.vacuum = tuple(payload[k] for k in ("vacuum", "main_brush", "side_brush"))
                self.vacuum_stamp = time.monotonic()
        except ValueError:
            with self.lock:
                self.vacuum = (False, False, False)

    async def run_watchdog(self):
        while True:
            try:
                await self.driver.watchdog(time.monotonic())
            except Exception:
                self.fault = "driver_watchdog_failure"
            await asyncio.sleep(0.05)

    async def run_io(self):
        try:
            await self.driver.connect()
            while True:
                now = time.monotonic()
                with self.lock:
                    command = self.command.model_copy() if self.command else None
                    motors = (
                        self.vacuum
                        if 0 <= now - self.vacuum_stamp <= self.config.safety.watchdog_s
                        else (False, False, False)
                    )
                if command:
                    command.vacuum, command.main_brush, command.side_brush = motors
                    await self.driver.apply(command, now)
                await self.step_simulation(1 / self.config.control_hz)
                snapshot = await self.driver.poll(time.monotonic())
                if not self.driver.previous_encoders.supported:
                    raise RuntimeError("backend has no measured encoders")
                with self.lock:
                    self.snapshot = snapshot
                    self.sensor_stamp = self.seconds()
                    current = self.driver.pose.model_copy()
                    if self.previous_measurement:
                        previous, previous_stamp = self.previous_measurement
                        dt = self.sensor_stamp - previous_stamp
                        if dt > 0:
                            yaw_delta = math.atan2(
                                math.sin(current.yaw - previous.yaw),
                                math.cos(current.yaw - previous.yaw),
                            )
                            linear = (
                                (current.x - previous.x) * math.cos(previous.yaw)
                                + (current.y - previous.y) * math.sin(previous.yaw)
                            ) / dt
                            self.measured_velocity = (linear, yaw_delta / dt)
                    self.previous_measurement = (current, self.sensor_stamp)
                    self.pose = current
                    self.encoder = self.driver.previous_encoders.model_copy()
                await asyncio.sleep(1 / self.config.control_hz)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self.fault = type(exc).__name__
        finally:
            await self.driver.close()

    async def step_simulation(self, dt):
        pass

    def publish_sensors(self):
        with self.lock:
            snapshot, stamp, pose, enc = self.snapshot, self.sensor_stamp, self.pose, self.encoder
            measured_velocity = self.measured_velocity
        if (
            not snapshot
            or self.fault
            or not 0 <= self.seconds() - stamp <= self.config.safety.sensor_timeout_s
        ):
            self.publish_json(
                self.status_pub, "base", {"connected": False, "fault": self.fault or "sensor_stale"}
            )
            return
        payload = {
            "connected": snapshot.connected,
            "battery": snapshot.battery.model_dump(),
            "bumper": snapshot.bumper.model_dump(),
            "cliff": snapshot.cliff.model_dump(),
            "odometry_supported": enc.supported,
            "linear_mps": measured_velocity[0],
            "angular_rps": measured_velocity[1],
        }
        self.publish_json(self.status_pub, "base", payload, stamp)
        now_msg = self.get_clock().now().to_msg()
        battery = BatteryState()
        battery.header.stamp = now_msg
        battery.percentage = float(snapshot.battery.percent) / 100.0
        battery.voltage = float(snapshot.battery.voltage)
        battery.current = float(snapshot.battery.current)
        battery.present = True
        self.battery_pub.publish(battery)
        self.base_battery_pub.publish(battery)
        self.bump_pub.publish(
            Bool(data=snapshot.bumper.left or snapshot.bumper.right or snapshot.bumper.wheel_drop)
        )
        self.cliff_pub.publish(Bool(data=snapshot.cliff.detected))
        joint = JointState()
        joint.header.stamp = now_msg
        joint.name = ["left_wheel", "right_wheel"]
        joint.position = [
            float(enc.left * 2 * math.pi / self.config.encoder_ticks_per_rev),
            float(enc.right * 2 * math.pi / self.config.encoder_ticks_per_rev),
        ]
        self.encoder_pub.publish(joint)
        odom = Odometry()
        odom.header.stamp = now_msg
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = float(pose.x)
        odom.pose.pose.position.y = float(pose.y)
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = float(math.sin(pose.yaw / 2))
        odom.pose.pose.orientation.w = float(math.cos(pose.yaw / 2))
        odom.twist.twist.linear.x = float(measured_velocity[0])
        odom.twist.twist.angular.z = float(measured_velocity[1])
        for index in (0, 7, 35):
            odom.pose.covariance[index] = 0.01
            odom.twist.covariance[index] = 0.02
        self.odom_pub.publish(odom)
        transform = TransformStamped()
        transform.header.stamp = now_msg
        transform.header.frame_id = "odom"
        transform.child_frame_id = "base_link"
        transform.transform.translation.x = float(pose.x)
        transform.transform.translation.y = float(pose.y)
        transform.transform.translation.z = 0.0
        transform.transform.rotation = odom.pose.pose.orientation
        self.tf.sendTransform(transform)

    def destroy_node(self):
        self.watchdog_future.cancel()
        self.io_future.cancel()
        try:
            self.worker.submit(self.driver.close()).result(timeout=2)
        except Exception:
            pass
        self.worker.close()
        return super().destroy_node()


def main():
    spin(BaseNode)

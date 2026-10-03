"""20 Hz fail-closed arbiter; every actuator topic has this single publisher."""

import math
import time

from geometry_msgs.msg import Twist
from neuravac_base.contracts import decode
from neuravac_base.util import ConfigNode, spin
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import String
from std_srvs.srv import Trigger

from neuravac_core.models import BatteryState, BumperState, CliffState
from neuravac_core.safety import CommandArbiter, SafetyMonitor, SensorSnapshot, VelocityCommand


class SafetyNode(ConfigNode):
    def __init__(self):
        super().__init__("safety_arbiter")
        self.monitor = SafetyMonitor(self.config.safety)
        self.arbiter = CommandArbiter(self.config.safety)
        self.sensors = SensorSnapshot(connected=False)
        self.cleaning = (False, 0.0)
        self.velocity_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.motor_pub = self.create_publisher(String, "/base/vacuum_cmd", 10)
        self.status_pub = self.create_publisher(String, "/safety/status", 10)
        self.create_subscription(
            Twist, "/nav/cmd_vel", lambda m: self.velocity(m, "navigation"), 10
        )
        self.create_subscription(Twist, "/manual/cmd_vel", lambda m: self.velocity(m, "manual"), 10)
        self.create_subscription(String, "/base/status", self.base, 10)
        self.create_subscription(LaserScan, "/scan", self.scan, qos_profile_sensor_data)
        self.create_subscription(Image, "/camera/image_raw", self.camera, qos_profile_sensor_data)
        self.create_subscription(String, "/mission/heartbeat", self.heartbeat, 10)
        self.create_subscription(String, "/mission/cleaning_cmd", self.clean, 10)
        self.create_service(Trigger, "/emergency_stop", self.emergency)
        self.create_service(Trigger, "/safety/reset", self.reset)
        self.create_timer(0.05, self.tick)

    def message_age(self, stamp, limit):
        age = self.seconds() - (stamp.sec + stamp.nanosec / 1e9)
        if not 0 <= age <= limit:
            raise ValueError("stale sensor stamp")
        return time.monotonic() - age

    def velocity(self, msg, source):
        try:
            if any(
                abs(v) > 1e-8 for v in (msg.linear.y, msg.linear.z, msg.angular.x, msg.angular.y)
            ):
                raise ValueError("unsupported axis")
            self.arbiter.submit(
                VelocityCommand(
                    source=source,
                    linear_mps=msg.linear.x,
                    angular_rps=msg.angular.z,
                    timestamp=time.monotonic(),
                )
            )
        except ValueError:
            self.arbiter.clear()
            self.cleaning = (False, 0.0)

    def base(self, msg):
        try:
            data = decode(msg.data, "base", self.seconds(), self.config.safety.sensor_timeout_s)
            p = data["payload"]
            if p.get("connected") is not True or p.get("odometry_supported") is not True:
                raise ValueError("driver unavailable")
            self.sensors.battery = BatteryState.model_validate(p["battery"])
            self.sensors.bumper = BumperState.model_validate(p["bumper"])
            self.sensors.cliff = CliffState.model_validate(p["cliff"])
            self.sensors.connected = True
            self.sensors.base_timestamp = time.monotonic() - (self.seconds() - data["stamp"])
        except (ValueError, KeyError, TypeError):
            self.sensors.connected = False

    def scan(self, msg):
        try:
            # +inf means no return; reject NaN, negatives, empty scans and invalid geometry.
            if (
                not msg.ranges
                or not math.isfinite(msg.angle_increment)
                or msg.angle_increment <= 0
                or any(math.isnan(x) or x < 0 for x in msg.ranges)
            ):
                raise ValueError("invalid scan")
            self.sensors.scan_timestamp = self.message_age(
                msg.header.stamp, self.config.safety.sensor_timeout_s
            )
        except ValueError:
            self.sensors.scan_timestamp = None

    def camera(self, msg):
        try:
            if msg.width <= 0 or msg.height <= 0 or not msg.data:
                raise ValueError("empty image")
            self.sensors.camera_timestamp = self.message_age(
                msg.header.stamp, self.config.safety.camera_timeout_s
            )
        except ValueError:
            self.sensors.camera_timestamp = None

    def heartbeat(self, msg):
        try:
            data = decode(msg.data, "heartbeat", self.seconds(), self.config.safety.watchdog_s)
            self.sensors.heartbeat_timestamp = time.monotonic() - (self.seconds() - data["stamp"])
        except ValueError:
            self.sensors.heartbeat_timestamp = None

    def clean(self, msg):
        try:
            data = decode(
                msg.data, "cleaning_command", self.seconds(), self.config.safety.watchdog_s
            )
            enabled = data["payload"]["enabled"]
            if type(enabled) is not bool:
                raise ValueError("expected boolean")
            self.cleaning = (enabled, time.monotonic() - (self.seconds() - data["stamp"]))
        except (ValueError, KeyError):
            self.cleaning = (False, 0.0)

    def emergency(self, request, response):
        self.monitor.emergency_stop()
        self.arbiter.clear()
        self.cleaning = (False, 0)
        self.tick()
        response.success = True
        response.message = "Emergency stop latched"
        return response

    def reset(self, request, response):
        response.success = self.monitor.reset(self.sensors, time.monotonic())
        self.arbiter.clear()
        self.cleaning = (False, 0)
        response.message = (
            "Reset healthy" if response.success else "Reset refused: sensors are unhealthy"
        )
        return response

    def tick(self):
        now = time.monotonic()
        status = self.monitor.evaluate(self.sensors, now)
        chosen = self.arbiter.select(now, status)
        output = Twist()
        output.linear.x = float(chosen.linear_mps)
        output.angular.z = float(chosen.angular_rps)
        enabled = (
            status.safe
            and chosen.source != "manual"
            and self.cleaning[0]
            and 0 <= now - self.cleaning[1] <= self.config.safety.watchdog_s
        )
        if enabled:
            output.linear.x = 0.0
            output.angular.z = 0.0
        self.velocity_pub.publish(output)
        self.publish_json(
            self.motor_pub, "vacuum", dict.fromkeys(("vacuum", "main_brush", "side_brush"), enabled)
        )
        self.publish_json(self.status_pub, "safety", status.model_dump())


def main():
    spin(SafetyNode)

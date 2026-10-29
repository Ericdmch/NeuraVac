"""Optional autonomous-drive extension for the Pi's serial-owning driver.

This module must be called from the serial owner, not run as a separate ROS
process. The owner retains its existing manual and telemetry safety checks.
"""
import math
import time

from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from std_srvs.srv import Trigger
from rclpy.qos import qos_profile_sensor_data

from .autonomy_drive import drive_command
from .motion_inputs import motion_fault, scan_clear
from .motor_watchdog import MotorWatchdog


class DriverWatchdog:
    def __init__(self, driver):
        self.driver = driver
        self.guard = MotorWatchdog(timeout=.3)
        self.stop_failed = False
        self.inputs = {}
        self.status = driver.create_publisher(String, 'autonomy/driver_status', 10)
        self.subscriptions = [
            driver.create_subscription(Twist, 'autonomy/cmd_vel', self.on_velocity, 10),
            driver.create_subscription(LaserScan, 'scan', self.on_scan, qos_profile_sensor_data),
            driver.create_subscription(PoseStamped, 'slam/pose', self.on_pose, 10),
            driver.create_subscription(Odometry, 'odom', self.on_odom, 10),
            driver.create_subscription(String, 'slam/status', self.on_status, 10),
        ]
        self.arm_service = driver.create_service(Trigger, 'autonomy/arm', self.arm)
        self.stop_service = driver.create_service(Trigger, 'autonomy/disarm', self.disarm)
        self.timer = driver.create_timer(.05, self.tick)

    def fault(self, now):
        with self.driver._sensor_condition:
            stamp = self.driver._latest_group_zero_at
            sensors = self.driver._latest_group_zero
        inputs = dict(self.inputs)
        if stamp is not None:
            inputs['sensors'] = (stamp, sensors)
        return motion_fault(inputs, now)

    def fresh_header(self, header):
        now = self.driver.get_clock().now().nanoseconds * 1e-9
        stamp = header.stamp.sec + header.stamp.nanosec * 1e-9
        return math.isfinite(now) and 0 <= now - stamp <= .5

    def on_scan(self, msg):
        coverage = abs(msg.angle_increment) * len(msg.ranges)
        valid = (self.fresh_header(msg.header) and math.isfinite(coverage) and 6.0 <= coverage <= 6.5 and
                 scan_clear(msg.ranges, msg.range_min, msg.range_max, .25))
        self.inputs['scan'] = (time.monotonic(), valid)

    def on_pose(self, msg):
        p, q = msg.pose.position, msg.pose.orientation
        valid = (self.fresh_header(msg.header) and msg.header.frame_id == 'map' and
                 all(math.isfinite(v) for v in (p.x, p.y, q.x, q.y, q.z, q.w)) and
                 abs(sum(v*v for v in (q.x, q.y, q.z, q.w)) - 1) < .05)
        self.inputs['pose'] = (time.monotonic(), valid)

    def on_odom(self, msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        valid = (self.fresh_header(msg.header) and msg.header.frame_id == 'odom' and msg.child_frame_id == 'base_link' and
                 all(math.isfinite(v) for v in (p.x, p.y, q.x, q.y, q.z, q.w)) and
                 abs(sum(v*v for v in (q.x, q.y, q.z, q.w)) - 1) < .05)
        self.inputs['odom'] = (time.monotonic(), valid)

    def on_status(self, msg):
        self.inputs['status'] = (time.monotonic(), msg.data)

    def arm(self, _request, response):
        now = time.monotonic()
        fault = self.fault(now)
        if self.guard.armed:
            response.success, response.message = False, 'Already armed'
        elif fault:
            response.success, response.message = False, fault
        else:
            with self.driver._serial_lock:
                fault = self.fault(time.monotonic())
                if fault:
                    response.success, response.message = False, fault
                    return response
                if not self.driver.serial.is_open:
                    response.success, response.message = False, 'Serial disconnected'
                    return response
                try:
                    self.driver.serial.write(bytes((131,)))
                    self.driver.serial.write(drive_command(0., 0.))
                except (OSError, IOError) as error:
                    response.success, response.message = False, 'Serial write failed: ' + str(error)
                    return response
                self.stop_failed = False
                self.guard.arm(time.monotonic())
                response.success, response.message = True, 'Armed; commands must arrive within 0.3 s'
        return response

    def stop(self, reason):
        was_armed = self.guard.armed
        if was_armed:
            self.guard.preempt(reason)
            with self.driver._serial_lock:
                try:
                    if not self.driver.serial.is_open:
                        raise OSError('serial disconnected')
                    self.driver.serial.write(drive_command(0., 0.))
                except (OSError, IOError):
                    self.stop_failed = True
                    self.guard.reason = reason + '; serial stop write failed'
        return not self.stop_failed

    def disarm(self, _request, response):
        stopped = self.stop('operator stop')
        response.success = stopped
        response.message = 'Autonomous drive stopped' if stopped else 'Serial stop write failed'
        return response

    def manual_preempt(self):
        self.stop('manual control')

    def on_velocity(self, msg):
        if not self.guard.armed:
            return
        now = time.monotonic()
        fault = self.fault(now)
        try:
            if any(v != 0. for v in (msg.linear.y, msg.linear.z, msg.angular.x, msg.angular.y)):
                raise ValueError('Unsupported velocity component')
            command = drive_command(msg.linear.x, msg.angular.z)
        except (TypeError, ValueError, OverflowError):
            fault = 'invalid or excessive velocity'
        if fault or now < self.guard.last or now - self.guard.last > self.guard.timeout:
            self.stop(fault or 'autonomous command timeout')
            return
        # Hold the serial lock across the last safety check and physical write.
        with self.driver._serial_lock:
            fault = self.fault(time.monotonic())
            if fault or not self.driver.serial.is_open:
                self.stop(fault or 'serial disconnected')
                return
            try:
                self.driver.serial.write(command)
            except (OSError, IOError):
                self.stop('serial drive write failed')
                return
            completed = time.monotonic()
            if completed < now or completed - now > self.guard.timeout:
                self.stop('autonomous command timeout')
            else:
                self.guard.last = completed

    def tick(self):
        if self.guard.armed:
            fault = self.fault(time.monotonic())
            # Do not let check() disarm before stop() has sent the zero command.
            expired = time.monotonic() - self.guard.last > self.guard.timeout
            if fault or expired:
                self.stop(fault or 'autonomous command timeout')
        self.status.publish(String(data=('ARMED' if self.guard.armed else self.guard.reason)))

"""ROS2 node that owns the Roomba's serial port.

  subscribes  /cmd_vel       (geometry_msgs/Twist)       drive commands
  publishes   /odom          (nav_msgs/Odometry)         dead-reckoned pose
              /battery_state (sensor_msgs/BatteryState)
              /tf            odom -> base_link           (what SLAM needs)

All the Roomba-specific work lives in roomba.py, sensors.py and odometry.py,
which know nothing about ROS. This file only connects them to topics.
"""
import math
import time

from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry as OdometryMsg
import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from tf2_ros import TransformBroadcaster

from neuravac_robot.odometry import Odometry, yaw_to_quaternion
from neuravac_robot.roomba import Roomba, twist_to_wheels

OI_MODE_NAMES = {2: 'safe', 3: 'full'}
CHARGING = ('charging', 'trickle_charging', 'charging_recovery')


class RoombaNode(Node):
    def __init__(self):
        super().__init__('roomba')

        # Settings come from config/roomba.yaml. Give decimals a decimal default
        # (20.0, not 20): the parameter's type is fixed by its first value.
        port = self.declare_parameter('port', '/dev/ttyUSB0').value
        baud = self.declare_parameter('baud', 115200).value
        self.rate_hz = self.declare_parameter('rate_hz', 20.0).value
        self.safe_mode = self.declare_parameter('safe_mode', True).value
        self.cmd_timeout = self.declare_parameter('cmd_timeout', 0.5).value
        self.wheel_base = self.declare_parameter('wheel_base', 0.235).value
        self.max_speed = self.declare_parameter('max_speed', 0.5).value
        self.odom_frame = self.declare_parameter('odom_frame', 'odom').value
        self.base_frame = self.declare_parameter('base_frame', 'base_link').value
        publish_tf = self.declare_parameter('publish_tf', True).value

        self.roomba = Roomba(port, baud)
        self.odometry = Odometry()
        self.next_connect = 0.0     # earliest time (monotonic) to retry the port
        self.last_request = None    # when the previous sensor request was sent
        self.last_cmd_time = None   # when /cmd_vel last arrived
        self.cmd_active = False     # True while the last command was non-zero

        # Two callback groups so a slow sensor read can never delay a stop
        # command: the executor runs one callback per group at a time, and the
        # two groups run in parallel on separate threads.
        sensor_group = MutuallyExclusiveCallbackGroup()
        command_group = MutuallyExclusiveCallbackGroup()

        self.odom_pub = self.create_publisher(OdometryMsg, 'odom', 10)
        self.battery_pub = self.create_publisher(BatteryState, 'battery_state', 10)
        self.tf_broadcaster = TransformBroadcaster(self) if publish_tf else None

        self.create_subscription(
            Twist, 'cmd_vel', self.on_cmd_vel, 10, callback_group=command_group)
        self.create_timer(1.0 / self.rate_hz, self.poll, callback_group=sensor_group)
        self.create_timer(0.1, self.watchdog, callback_group=command_group)

        self.get_logger().info(
            f'roomba node up: {port} @ {baud} baud, {self.rate_hz:.0f} Hz, '
            f'{"safe" if self.safe_mode else "FULL"} mode')

    # ---- commands ------------------------------------------------------

    def on_cmd_vel(self, msg):
        """Called when a /cmd_vel message arrives: forward it to the wheels."""
        right, left = twist_to_wheels(
            msg.linear.x, msg.angular.z, self.wheel_base, self.max_speed)
        self.last_cmd_time = time.monotonic()
        self.cmd_active = bool(right or left)
        self.send_wheels(right, left)

    def watchdog(self):
        """Stop the robot if /cmd_vel goes quiet. The Roomba has no timeout of its own."""
        if not self.cmd_active:
            return
        silence = time.monotonic() - self.last_cmd_time
        if silence > self.cmd_timeout:
            self.get_logger().warn(f'no /cmd_vel for {silence:.1f} s, stopping')
            self.cmd_active = False
            self.send_wheels(0, 0)

    def send_wheels(self, right, left):
        try:
            self.roomba.drive_direct(right, left)
        except OSError as error:
            self.get_logger().warn(
                f'cannot send drive command: {error}', throttle_duration_sec=2.0)

    # ---- sensors -------------------------------------------------------

    def poll(self):
        """Timer callback: (re)connect if needed, read sensors, publish."""
        now = time.monotonic()
        if not self.roomba.is_open:
            if now < self.next_connect:
                return
            self.next_connect = now + 3.0
            if not self.connect():
                return

        request_time = time.monotonic()
        previous_request = self.last_request
        self.last_request = request_time    # set even if this read fails (see below)
        try:
            sensors = self.roomba.read_sensors()
        except TimeoutError as error:       # one missed reply; the port is fine
            # The robot already reset its distance/angle counters when it saw
            # the request, so that interval's motion is lost from the pose.
            self.get_logger().warn(
                f'sensor reply timed out: {error}', throttle_duration_sec=2.0)
            return
        except OSError as error:            # cable pulled, adapter reset, ...
            self.get_logger().error(f'serial error, will reconnect: {error}')
            self.roomba.close()
            return

        stamp = self.get_clock().now().to_msg()
        # The first reply after connecting covers an unknown amount of time, so
        # it only sets the baseline. After that, distance/angle are the change
        # since the previous request, so dt is the gap between requests.
        if previous_request is not None:
            dt = request_time - previous_request
            if dt > 0.0:
                self.publish_odom(stamp, dt, sensors)
        self.publish_battery(stamp, sensors)
        self.check_mode(sensors)

    def connect(self):
        try:
            self.roomba.connect()
            self.roomba.start(self.safe_mode)
        except OSError as error:
            self.roomba.close()
            self.get_logger().warn(
                f'cannot open {self.roomba.port}: {error} (retrying)',
                throttle_duration_sec=15.0)
            return False
        self.last_request = None
        self.get_logger().info(f'connected to {self.roomba.port}')
        return True

    def publish_odom(self, stamp, dt, sensors):
        distance_mm = sensors['distance_mm']
        angle_deg = sensors['angle_degrees']
        pose = self.odometry.update(distance_mm, angle_deg)
        qx, qy, qz, qw = yaw_to_quaternion(pose.yaw)

        msg = OdometryMsg()
        msg.header.stamp = stamp
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = self.base_frame
        msg.pose.pose.position.x = pose.x
        msg.pose.pose.position.y = pose.y
        msg.pose.pose.orientation.x = qx
        msg.pose.pose.orientation.y = qy
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw
        msg.twist.twist.linear.x = distance_mm / 1000.0 / dt
        msg.twist.twist.angular.z = math.radians(angle_deg) / dt
        self.odom_pub.publish(msg)

        if self.tf_broadcaster is not None:
            tf = TransformStamped()
            tf.header.stamp = stamp
            tf.header.frame_id = self.odom_frame
            tf.child_frame_id = self.base_frame
            tf.transform.translation.x = pose.x
            tf.transform.translation.y = pose.y
            tf.transform.rotation.x = qx
            tf.transform.rotation.y = qy
            tf.transform.rotation.z = qz
            tf.transform.rotation.w = qw
            self.tf_broadcaster.sendTransform(tf)

    def publish_battery(self, stamp, sensors):
        msg = BatteryState()
        msg.header.stamp = stamp
        msg.header.frame_id = self.base_frame
        msg.voltage = sensors['battery_voltage_mv'] / 1000.0
        msg.current = sensors['battery_current_ma'] / 1000.0    # + while charging
        msg.temperature = float(sensors['battery_temperature_c'])
        msg.charge = sensors['battery_charge_mah'] / 1000.0
        msg.capacity = sensors['battery_capacity_mah'] / 1000.0
        msg.design_capacity = math.nan
        percent = sensors['battery_percent']
        msg.percentage = math.nan if percent is None else percent / 100.0
        state = sensors['charging_state_name']
        if state in CHARGING:
            msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
        elif state == 'not_charging':
            msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        elif state == 'waiting':
            msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_NOT_CHARGING
        else:
            msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_UNKNOWN
        msg.present = True
        self.battery_pub.publish(msg)

    def check_mode(self, sensors):
        """Warn if the robot dropped out of the mode we asked for."""
        wanted = 2 if self.safe_mode else 3
        if sensors['oi_mode'] != wanted:
            self.get_logger().warn(
                f'Roomba is in {sensors["oi_mode_name"]} mode, not '
                f'{OI_MODE_NAMES[wanted]}: drive commands are ignored '
                '(cliff, wheel drop, or the charger?)',
                throttle_duration_sec=5.0)

    def shutdown(self):
        """Stop the wheels and release the port."""
        self.roomba.stop()


def main(args=None):
    rclpy.init(args=args)
    node = RoombaNode()
    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

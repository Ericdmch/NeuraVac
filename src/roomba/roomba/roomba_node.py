#!/usr/bin/env python3
import math
import threading

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from nav_msgs.msg import Odometry
from roomba_interfaces.msg import SerialData
from roomba_interfaces.srv import RequestTelemetry
import serial
from serial import SerialException

DEBUG = False

class Roomba(Node):
    def __init__(self):
        super().__init__('roomba_node')

        # Serial connection
        self.declare_parameter('serial_port', '/dev/neuravac_roomba')
        self.declare_parameter('baudrate', 115200)

        serial_port = self.get_parameter('serial_port').value
        baudrate = self.get_parameter('baudrate').value
        self._serial_lock = threading.Lock()
        
        try:
            self.serial = serial.Serial(
                port=serial_port,
                baudrate=baudrate,
                timeout=0,
            )

            self.write_serial(SerialData(data=[128, 131, 139, 0, 0, 0])) # Wake up in safe mode and led off

        except SerialException as error:
            self.get_logger().error(
                f'Unable to open Roomba serial port {serial_port!r}: {error}'
            )
            raise

        self.get_logger().info(
            f'Roomba serial connection opened on {serial_port} at {baudrate} baud'
        )

        # ROS2 Serial topics
        self.serial_timer = self.create_timer(0.01, self.read_serial)
        self.serial_rx = self.create_publisher( # The pi is receiving data from the roomba
            SerialData,
            'serial_rx',
            10
        )
        self.serial_tx = self.create_subscription( # The pi is transmitting data to the roomba
            SerialData,
            'serial_tx',
            self.write_serial,
            10
        )
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self._sensor_query_timer = self.create_timer(0.5, self.request_group_zero)
        self._sensor_service = self.create_service(
            RequestTelemetry, 'request_telemetry', self.request_telemetry,
            callback_group=ReentrantCallbackGroup(),
        )
        self._sensor_buffer = bytearray()
        self._sensor_condition = threading.Condition()
        self._sensor_sequence = 0
        self._latest_group_zero = None
        self._odom_x = 0.0
        self._odom_y = 0.0
        self._odom_yaw = 0.0
        
        # Testing
        if DEBUG:
            self.test_timer = self.create_timer(0.1, self.test)
            self.test_count = 0

    def read_serial(self):
        waiting = self.serial.in_waiting
        if waiting == 0:
            return

        data = self.serial.read(waiting)
        msg = SerialData()
        msg.data = list(data)
        self.serial_rx.publish(msg)
        self._sensor_buffer.extend(data)
        while len(self._sensor_buffer) >= 26:
            packet = bytes(self._sensor_buffer[:26])
            if any(value not in (0, 1) for value in packet[1:7]) or packet[16] > 5:
                del self._sensor_buffer[0]
                continue
            del self._sensor_buffer[:26]
            with self._sensor_condition:
                self._latest_group_zero = packet
                self._sensor_sequence += 1
                self._sensor_condition.notify_all()
            self.publish_odometry(packet)
        # self.get_logger().info(f'Read {len(data)} bytes from serial: {data}')

    def write_serial(self, data : SerialData):
        if not self.serial.is_open:
            self.get_logger().error('Serial port is not open')
            return

        if not isinstance(data, SerialData):
            self.get_logger().error(
                f'Expected SerialData message, got {type(data).__name__}'
            )
            return

        try:
            payload = bytes(data.data)
            with self._serial_lock:
                self.serial.write(payload)
            self.get_logger().info(
                f'Wrote {len(payload)} bytes to serial: {payload}'
            )
        except SerialException as error:
            self.get_logger().error(f'Error writing to serial port: {error}')

    def request_group_zero(self):
        """Read group 0 for incremental odometry and latest sensor state."""
        self._write_bytes(bytes((142, 0)))

    def request_telemetry(self, _request, response):
        """Request group 0 and return the complete 26-byte sensor packet."""
        with self._sensor_condition:
            sequence = self._sensor_sequence
            try:
                self._write_bytes(bytes((142, 0)))
            except SerialException as error:
                response.accepted = False
                response.message = str(error)
                response.data = []
                return response
            received = self._sensor_condition.wait_for(
                lambda: self._sensor_sequence > sequence,
                timeout=1.0,
            )
            response.accepted = received
            response.message = (
                'Received OI sensor group 0.' if received
                else 'Timed out waiting for the 26-byte sensor packet.'
            )
            response.data = list(self._latest_group_zero) if received else []
        return response

    def _write_bytes(self, payload):
        if not self.serial.is_open:
            raise SerialException('Roomba serial port is not open')
        with self._serial_lock:
            self.serial.write(payload)

    def publish_odometry(self, packet):
        distance_m = int.from_bytes(packet[12:14], 'big', signed=True) / 1000.0
        delta_yaw = math.radians(int.from_bytes(packet[14:16], 'big', signed=True))
        mid_yaw = self._odom_yaw + delta_yaw / 2.0
        self._odom_x += distance_m * math.cos(mid_yaw)
        self._odom_y += distance_m * math.sin(mid_yaw)
        self._odom_yaw = math.atan2(
            math.sin(self._odom_yaw + delta_yaw),
            math.cos(self._odom_yaw + delta_yaw),
        )

        message = Odometry()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'odom'
        message.child_frame_id = 'base_link'
        message.pose.pose.position.x = self._odom_x
        message.pose.pose.position.y = self._odom_y
        message.pose.pose.orientation.z = math.sin(self._odom_yaw / 2.0)
        message.pose.pose.orientation.w = math.cos(self._odom_yaw / 2.0)
        message.pose.covariance[0] = 0.03
        message.pose.covariance[7] = 0.03
        message.pose.covariance[35] = 0.08
        self.odom_pub.publish(message)

    def destroy_node(self):
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
        super().destroy_node()

    

    def test(self):
        # Send a test message to the Roomba every second
        steps = [
            [128],                # START
            [131],                # SAFE
            [139, 0, 0, 255],     # power LED green
            [139, 0, 128, 255],   # orange
            [139, 0, 255, 255],   # red
            [139, 0, 0, 0],       # off
        ]


        msg = SerialData()
        msg.data = steps[self.test_count % len(steps)]

        self.write_serial(msg)

        self.test_count += 1
        

def main(args=None):
    rclpy.init(args=args)

    try:
        node = Roomba()
        



        from rclpy.executors import MultiThreadedExecutor

        executor = MultiThreadedExecutor(num_threads=2)
        executor.add_node(node)
        executor.spin()

    except (SerialException, KeyboardInterrupt):
        pass
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

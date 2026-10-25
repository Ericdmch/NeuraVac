#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from roomba_interfaces.msg import SerialData
import serial
from serial import SerialException

DEBUG = False

class Roomba(Node):
    def __init__(self):
        super().__init__('roomba_node')

        # Serial connection
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)

        serial_port = self.get_parameter('serial_port').value
        baudrate = self.get_parameter('baudrate').value
        
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
            self.serial.write(payload)
            self.get_logger().info(
                f'Wrote {len(payload)} bytes to serial: {payload}'
            )
        except SerialException as error:
            self.get_logger().error(f'Error writing to serial port: {error}')

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
            [139, 0, 0, 0],       # lights off
        ]


        msg = SerialData()
        msg.data = steps[self.test_count % len(steps)]

        self.write_serial(msg)

        self.test_count += 1
        

def main(args=None):
    rclpy.init(args=args)

    try:
        node = Roomba()
        
        rclpy.spin(node)

    except (SerialException, KeyboardInterrupt):
        pass
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

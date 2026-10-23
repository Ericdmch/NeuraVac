import rclpy
from rclpy.node import Node
import serial
from serial import SerialException
from roomba_interfaces.msg import SerialData

class Lidar(Node):
    def __init__(self):
        super().__init__('lidar_node')

        # Serial connection
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 230400)

        serial_port = self.get_parameter('serial_port').value
        baudrate = self.get_parameter('baudrate').value
        
        try:
            self.serial = serial.Serial(
                port=serial_port,
                baudrate=baudrate,
                timeout=0,
            )
        except serial.SerialException as error:
            self.get_logger().error(
                f'Unable to open Lidar serial port {serial_port!r}: {error}'
            )
            raise

        self.get_logger().info(
            f'Lidar serial connection opened on {serial_port} at {baudrate} baud'
        )

        # ROS2 Serial topics
        self.serial_timer = self.create_timer(0.01, self.read_serial)
        self.lidar_data = self.create_publisher(
            SerialData, 
            'lidar_data',
            10
        )

    def read_serial(self):
        waiting = self.serial.in_waiting
        if waiting == 0:
            return

        data = self.serial.read(waiting)
        # self.get_logger().info(f'Received {len(data)} bytes from Lidar: {data.hex()}')

def main(args=None):
    rclpy.init(args=args)

    try:
        node = Lidar()

        rclpy.spin(node)

    except (SerialException, KeyboardInterrupt):
        pass
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


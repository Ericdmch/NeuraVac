"""ROS 2 bridge that owns the Roomba serial connection."""

import rclpy
import time
from rclpy.node import Node
from std_msgs.msg import String

from src.roomba import Roomba


class RoombaBridge(Node):
    """Publish incoming serial monitor bytes and forward raw opcode commands."""

    def __init__(self):
        super().__init__("roomba_serial_bridge")
        self.roomba = Roomba()
        self.messages = self.create_publisher(String, "/roomba/serial_monitor/messages", 10)
        self.status = self.create_publisher(String, "/roomba/serial/status", 10)
        self.create_subscription(String, "/roomba/serial_monitor/commands", self.send_command, 10)
        self.timer = self.create_timer(0.05, self.poll_serial)
        self._last_connect_attempt = time.monotonic()
        self._connect()

    def _connect(self):
        self.roomba.connect_serial(attempts=0)
        connected = bool(self.roomba.ser and self.roomba.ser.is_open)
        status = String()
        status.data = "connected" if connected else "disconnected"
        self.status.publish(status)
        if connected:
            self.get_logger().info("Roomba serial port connected")
        else:
            self.get_logger().error("Unable to open the Roomba serial port")

    def send_command(self, message):
        try:
            code = [int(part, 16) for part in message.data.split()]
            if not code or any(byte < 0 or byte > 255 for byte in code):
                raise ValueError("expected one or more hexadecimal bytes")
            self.roomba._send_opcode(code=code)
        except ValueError as error:
            self.get_logger().warning(f"Ignoring invalid serial command: {error}")

    def poll_serial(self):
        connection = self.roomba.ser
        connected = bool(connection and connection.is_open)
        if not connected and time.monotonic() - self._last_connect_attempt >= 5:
            self._last_connect_attempt = time.monotonic()
            self._connect()
            connection = self.roomba.ser
            connected = bool(connection and connection.is_open)
        if connected:
            try:
                available = connection.in_waiting
                if available:
                    message = String()
                    message.data = f"received: {connection.read(available).hex(' ')}"
                    self.messages.publish(message)
            except Exception as error:
                self.get_logger().error(f"Serial read failed: {error}")
                connected = False
        status = String()
        status.data = "connected" if connected else "disconnected"
        self.status.publish(status)

    def close(self):
        if self.roomba.ser and self.roomba.ser.is_open:
            self.roomba.ser.close()


def main(args=None):
    rclpy.init(args=args)
    node = RoombaBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

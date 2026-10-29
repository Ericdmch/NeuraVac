"""Thread-safe ROS 2 client used by the Flask web application."""

from collections import deque
from threading import Lock, Thread
import time

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    ROS_IMPORT_ERROR = None
except ModuleNotFoundError as error:
    # Let Flask serve the dashboard on machines without ROS 2 installed.
    rclpy = None
    Node = object
    String = None
    ROS_IMPORT_ERROR = str(error)


class _GatewayNode(Node):
    def __init__(self, gateway):
        super().__init__("neuravac_web_gateway")
        self.gateway = gateway
        self.command_publisher = self.create_publisher(String, "/roomba/serial_monitor/commands", 10)
        self.create_subscription(String, "/roomba/serial_monitor/messages", gateway._on_message, 10)
        self.create_subscription(String, "/roomba/serial/status", gateway._on_status, 10)


class RosWebGateway:
    """Run a ROS executor in the Flask process and expose a small thread-safe API."""

    def __init__(self):
        self._messages = deque(maxlen=500)
        self._lock = Lock()
        self._connected = False
        self._node = None
        self._ready = False
        self._error = ROS_IMPORT_ERROR
        self._thread = Thread(target=self._spin, name="ros-web-gateway", daemon=True)
        if self._error is None:
            self._thread.start()
        deadline = time.monotonic() + 5
        while not self._ready and self._error is None and time.monotonic() < deadline:
            time.sleep(0.01)

    def _spin(self):
        try:
            if rclpy is None:
                return
            if not rclpy.ok():
                rclpy.init()
            self._node = _GatewayNode(self)
            self._ready = True
            rclpy.spin(self._node)
        except Exception as error:
            self._error = str(error)

    def _on_message(self, message):
        with self._lock:
            self._messages.append(message.data)

    def _on_status(self, message):
        with self._lock:
            self._connected = message.data == "connected"

    @property
    def connected(self):
        with self._lock:
            return self._connected

    @property
    def error(self):
        return self._error

    def drain_messages(self):
        with self._lock:
            messages = list(self._messages)
            self._messages.clear()
            return messages

    def send_command(self, code):
        if self._error:
            raise RuntimeError(f"ROS 2 gateway unavailable: {self._error}")
        if not self._ready or self._node is None:
            raise RuntimeError("ROS 2 gateway is not ready")
        message = String()
        message.data = " ".join(f"{byte:02x}" for byte in code)
        self._node.command_publisher.publish(message)

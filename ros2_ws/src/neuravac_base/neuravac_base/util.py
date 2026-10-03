import asyncio
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from neuravac_base.contracts import envelope
from neuravac_core.config import load_config


class AsyncWorker:
    """One persistent asyncio loop; blocking inference/HTTP never occupies ROS callbacks."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()

    def submit(self, coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=2)


class ConfigNode(Node):
    def __init__(self, name):
        super().__init__(name)
        path = self.declare_parameter("robot_config", "").value
        if not path:
            raise ValueError("robot_config must name the shared typed robot YAML")
        self.config = load_config(path)

    def seconds(self):
        return self.get_clock().now().nanoseconds / 1e9

    def publish_json(self, publisher, kind, payload, stamp=None):
        publisher.publish(
            String(data=envelope(kind, self.seconds() if stamp is None else stamp, payload))
        )


def spin(factory):
    rclpy.init()
    node = None
    try:
        node = factory()
        rclpy.spin(node)
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

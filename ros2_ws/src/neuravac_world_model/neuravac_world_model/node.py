"""Validates the authoritative semantic snapshot and attaches measured base health."""

from neuravac_base.contracts import decode, restore_world
from neuravac_base.util import ConfigNode, spin
from std_msgs.msg import String


class WorldModelNode(ConfigNode):
    def __init__(self):
        super().__init__("world_model")
        self.semantic = None
        self.base = None
        self.safety = None
        self.pub = self.create_publisher(String, "/world_model", 10)
        self.create_subscription(String, "/semantic_map", self.semantic_cb, 10)
        self.create_subscription(String, "/base/status", self.base_cb, 10)
        self.create_subscription(String, "/safety/status", self.safety_cb, 10)
        self.create_timer(0.1, self.publish)

    def semantic_cb(self, msg):
        try:
            value = decode(
                msg.data, "semantic_map", self.seconds(), self.config.safety.camera_timeout_s
            )
            restore_world(value["payload"]["world"], self.config)
            self.semantic = value
        except (ValueError, KeyError, TypeError):
            self.semantic = None

    def base_cb(self, msg):
        try:
            self.base = decode(
                msg.data, "base", self.seconds(), self.config.safety.sensor_timeout_s
            )
        except ValueError:
            self.base = None

    def safety_cb(self, msg):
        try:
            self.safety = decode(msg.data, "safety", self.seconds(), self.config.safety.watchdog_s)
        except ValueError:
            self.safety = None

    def publish(self):
        if self.semantic:
            data = dict(self.semantic["payload"])
            data["available"] = bool(
                data["available"]
                and 0 <= self.seconds() - data["observed_at"] <= self.config.safety.camera_timeout_s
            )
            data["base"] = (
                self.base["payload"]
                if self.base
                and 0 <= self.seconds() - self.base["stamp"] <= self.config.safety.sensor_timeout_s
                else {"connected": False}
            )
            data["safety"] = (
                self.safety["payload"]
                if self.safety
                and 0 <= self.seconds() - self.safety["stamp"] <= self.config.safety.watchdog_s
                else {"safe": False}
            )
            self.publish_json(self.pub, "world_model", data)


def main():
    spin(WorldModelNode)

"""Tracks map-frame observations and rasterizes expanded semantic keepouts."""

from nav_msgs.msg import OccupancyGrid
from neuravac_base.contracts import decode, keepout_cells
from neuravac_base.util import ConfigNode, spin
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import String

from neuravac_core.models import Detection
from neuravac_core.world import WorldModel


class SemanticMapNode(ConfigNode):
    def __init__(self):
        super().__init__("semantic_mapper")
        self.world = WorldModel(self.config)
        self.available = False
        self.observed_at = 0.0
        self.geometry = None
        self.pub = self.create_publisher(String, "/semantic_map", 10)
        self.regions = self.create_publisher(String, "/debris_regions", 10)
        self.hazards = self.create_publisher(String, "/hazards", 10)
        self.mask = self.create_publisher(
            OccupancyGrid,
            "/semantic_keepout",
            QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL),
        )
        self.create_subscription(String, "/perception/detections", self.observation, 10)
        self.create_subscription(String, "/cleaning/result", self.cleaned, 10)
        self.create_subscription(
            OccupancyGrid,
            "/map",
            self.map,
            QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL),
        )
        self.create_timer(0.1, self.publish)

    def map(self, msg):
        if (
            msg.header.frame_id == "map"
            and msg.info.width * msg.info.height <= 4_000_000
            and msg.info.resolution > 0
            and abs(msg.info.origin.orientation.z) < 1e-8
            and abs(msg.info.origin.orientation.x) < 1e-8
            and abs(msg.info.origin.orientation.y) < 1e-8
        ):
            self.geometry = msg.info

    def observation(self, msg):
        try:
            data = decode(
                msg.data, "detections", self.seconds(), self.config.safety.camera_timeout_s
            )
            p = data["payload"]
            if p.get("available") is not True:
                raise ValueError("observation unavailable")
            detections = [Detection.model_validate(item) for item in p["detections"]]
            if any(
                d.position is None or abs(d.timestamp - data["stamp"]) > 0.02 for d in detections
            ):
                raise ValueError("map position and matching stamp required")
            self.world.observe(detections, self.seconds())
            self.available = True
            self.observed_at = data["stamp"]
        except (ValueError, KeyError, TypeError):
            self.available = False

    def cleaned(self, msg):
        try:
            p = decode(
                msg.data, "cleaning_result", self.seconds(), self.config.safety.camera_timeout_s
            )["payload"]
            region = self.world.regions.get(p["region_id"])
            attempt = p.get("attempt")
            if (
                region
                and p.get("success") is True
                and attempt
                and attempt.get("success") is True
                and region.debris_score <= self.config.cleaning.success_threshold
                and abs(attempt["after_score"] - region.debris_score) < 1e-6
            ):
                region.cleaned = True
        except (ValueError, KeyError, TypeError):
            pass

    def publish(self):
        now = self.seconds()
        self.world.expire(now)
        available = (
            self.available and 0 <= now - self.observed_at <= self.config.safety.camera_timeout_s
        )
        self.publish_json(
            self.pub,
            "semantic_map",
            {
                "available": available,
                "observed_at": self.observed_at,
                "world": self.world.to_dict(),
            },
        )
        self.publish_json(
            self.regions,
            "debris_regions",
            {"regions": [r.model_dump(mode="json") for r in self.world.regions.values()]},
        )
        self.publish_json(
            self.hazards,
            "hazards",
            {"hazards": [h.model_dump(mode="json") for h in self.world.hazards]},
        )
        if self.geometry:
            origin = (self.geometry.origin.position.x, self.geometry.origin.position.y)
            data = keepout_cells(
                self.world, self.geometry.width, self.geometry.height, self.geometry.resolution, origin
            )
            if data != getattr(self, "last_mask_data", None):
                self.last_mask_data = data
                grid = OccupancyGrid()
                grid.header.frame_id = "map"
                grid.header.stamp = self.get_clock().now().to_msg()
                grid.info = self.geometry
                grid.data = data
                self.mask.publish(grid)


def main():
    spin(SemanticMapNode)

"""Newest-frame inference worker with explicit availability and calibrated map projection."""

import math
import os
from pathlib import Path

import numpy as np
import yaml
from neuravac_base.contracts import decode, project_observations
from neuravac_base.util import AsyncWorker, ConfigNode, spin
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import Image
from std_msgs.msg import String
from tf2_ros import Buffer, TransformListener

from neuravac_core.models import Detection, Pose
from neuravac_core.perception.interface import CameraFrame
from neuravac_core.perception.projection import FloorProjector
from neuravac_core.perception.providers import ONNXProvider, RemoteProvider, ReplayProvider


class PerceptionNode(ConfigNode):
    def __init__(self):
        super().__init__("floor_perception")
        self.pub = self.create_publisher(String, "/perception/detections", 10)
        path = self.declare_parameter("perception_config", "").value
        self.settings = yaml.safe_load(Path(path).read_text()) if path else {}
        provider = self.declare_parameter("provider", self.settings.get("provider", "onnx")).value
        self.worker = AsyncWorker()
        self.pending = None
        self.latest = None
        self.provider = None
        self.error = None
        self.projector = None
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self)
        projection = self.settings.get("projection", {})
        if projection.get("calibrated"):
            self.projector = FloorProjector(
                projection["intrinsics"],
                projection["camera_to_robot"],
                (self.settings["camera"]["width"], self.settings["camera"]["height"]),
                projection.get("max_distance_m", 5),
            )
        try:
            if provider == "sim":
                self.create_subscription(String, "/sim/labels", self.simulation, 10)
            elif provider == "replay":
                replay = self.declare_parameter("replay_path", "").value
                self.provider = ReplayProvider(replay)
            elif provider == "onnx":
                self.provider = ONNXProvider(
                    self.settings.get("model_path") or "",
                    confidence=self.settings.get("confidence", 0.5),
                    nms_iou=self.settings.get("nms_iou", 0.45),
                )
            elif provider == "remote":
                options = self.settings["remote"]
                self.provider = RemoteProvider(
                    options["endpoint"],
                    options["model"],
                    options["health_url"],
                    token=os.getenv(options.get("token_env", "NEURAVAC_VISION_TOKEN")),
                    timeout_s=options.get("timeout_s", 5),
                )
            else:
                raise ValueError("provider must be sim, replay, onnx or remote")
        except Exception as exc:
            self.error = type(exc).__name__
        self.create_subscription(Image, "/camera/image_raw", self.image, qos_profile_sensor_data)
        self.create_timer(0.05, self.tick)
        self.sim = provider == "sim"
        self.provider_kind = provider

    def simulation(self, msg):
        try:
            data = decode(
                msg.data, "detections", self.seconds(), self.config.safety.camera_timeout_s
            )
            detections = [Detection.model_validate(item) for item in data["payload"]["detections"]]
            if data["payload"].get("available") is not True or any(
                d.source != "simulated_camera" for d in detections
            ):
                raise ValueError("not labeled simulation")
            self.publish_json(
                self.pub,
                "detections",
                {"available": True, "detections": [d.model_dump(mode="json") for d in detections]},
                data["stamp"],
            )
        except (ValueError, KeyError):
            self.unavailable("invalid_simulation_labels")

    def image(self, msg):
        if self.sim:
            return
        # A single slot drops older frames while inference is pending.
        self.latest = msg

    def unavailable(self, reason):
        self.publish_json(
            self.pub, "detections", {"available": False, "detections": [], "reason": reason}
        )

    def tick(self):
        if self.sim:
            return
        if self.error:
            self.unavailable(self.error)
            return
        if self.pending:
            future, msg = self.pending
            if not future.done():
                return
            self.pending = None
            try:
                detections = future.result()
                stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
                if not 0 <= self.seconds() - stamp <= self.config.safety.camera_timeout_s:
                    raise ValueError("inference_stale")
                if self.provider_kind == "replay" and all(
                    d.position is not None and d.source == "replay" for d in detections
                ):
                    projected = detections
                else:
                    if not self.projector:
                        raise ValueError("camera calibration unavailable")
                    transform = self.tf.lookup_transform(
                        "map", "base_link", Time.from_msg(msg.header.stamp)
                    )
                    q = transform.transform.rotation
                    p = transform.transform.translation
                    pose = Pose(
                        x=p.x,
                        y=p.y,
                        yaw=math.atan2(
                            2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)
                        ),
                    )
                    projected = project_observations(detections, self.projector, pose)
                self.publish_json(
                    self.pub,
                    "detections",
                    {
                        "available": True,
                        "detections": [d.model_dump(mode="json") for d in projected],
                    },
                    stamp,
                )
            except Exception as exc:
                self.unavailable(type(exc).__name__)
        if self.latest is not None and self.provider is not None:
            msg, self.latest = self.latest, None
            try:
                if (
                    msg.encoding not in ("rgb8", "bgr8")
                    or msg.step < msg.width * 3
                    or len(msg.data) != msg.height * msg.step
                ):
                    raise ValueError("RGB/BGR8 image with valid row stride required")
                image = (
                    np.frombuffer(bytes(msg.data), dtype=np.uint8)
                    .reshape(msg.height, msg.step)[:, : msg.width * 3]
                    .reshape(msg.height, msg.width, 3)
                )
                if msg.encoding == "bgr8":
                    image = image[:, :, ::-1]
                stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
                self.pending = (
                    self.worker.submit(self.provider.detect(CameraFrame(image.copy(), stamp))),
                    msg,
                )
            except Exception as exc:
                self.unavailable(type(exc).__name__)

    def destroy_node(self):
        if self.pending:
            self.pending[0].cancel()
        if self.provider and hasattr(self.provider, "close"):
            try:
                self.worker.submit(self.provider.close()).result(timeout=2)
            except Exception:
                pass
        self.worker.close()
        return super().destroy_node()


def main():
    spin(PerceptionNode)

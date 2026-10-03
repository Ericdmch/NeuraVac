"""FastAPI bridge serves subscribed ROS telemetry and invokes real ROS services."""

import asyncio
import hmac
import io
import math
import os
import threading
import time
import uuid
from pathlib import Path

import numpy as np
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import Path as NavPath
from neuravac_base.contracts import decode
from neuravac_base.util import ConfigNode, spin
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformListener

from neuravac_core.storage import TABLES, MissionStore


class DashboardNode(ConfigNode):
    def __init__(self):
        super().__init__("dashboard_bridge")
        self.lock = threading.Lock()
        self.store = MissionStore(
            self.declare_parameter("database_path", "artifacts/ros-missions.db").value
        )
        self.mission_id = str(uuid.uuid4())
        self.recorded = {}
        self.data = {}
        self.attempts = []
        self.events = []
        self.image = None
        self.map_size = {}
        self.path = []
        self.mode = self.declare_parameter("mode", "hardware").value
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self)
        for topic, kind in [
            ("/world_model", "world_model"),
            ("/mission_state", "mission_state"),
            ("/safety/status", "safety"),
            ("/ai_decisions", "ai_decision"),
            ("/cleaning/result", "cleaning_result"),
        ]:
            self.create_subscription(String, topic, lambda msg, k=kind: self.telemetry(msg, k), 10)
        self.create_subscription(Image, "/camera/image_raw", self.camera, qos_profile_sensor_data)
        self.create_subscription(
            OccupancyGrid,
            "/map",
            self.map,
            QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL),
        )
        self.create_subscription(NavPath, "/plan", self.nav_path, 10)
        self.clients = {
            action: self.create_client(Trigger, service)
            for action, service in {
                "start": "/mission/start",
                "pause": "/mission/pause",
                "resume": "/mission/resume",
                "estop": "/emergency_stop",
                "reset": "/safety/reset",
                "move-chair": "/sim/move_chair",
                "return-home": "/mission/return_home",
            }.items()
        }
        host = self.declare_parameter("host", "127.0.0.1").value
        port = self.declare_parameter("port", 8000).value
        self.token = os.getenv("NEURAVAC_API_TOKEN", "")
        if host not in ("127.0.0.1", "localhost", "::1") and not self.token:
            raise ValueError("remote dashboard requires NEURAVAC_API_TOKEN")
        self.server = uvicorn.Server(
            uvicorn.Config(self.application(), host=host, port=port, log_level="warning")
        )
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()

    def telemetry(self, msg, kind):
        try:
            data = decode(msg.data, kind, self.seconds(), self.config.safety.camera_timeout_s)
            with self.lock:
                self.data[kind] = data
                payload = data["payload"]
                if kind == "mission_state" and payload.get("mission_id"):
                    self.mission_id = payload["mission_id"]
                table = {
                    "mission_state": "missions",
                    "cleaning_result": "cleaning_attempts",
                    "safety": "safety_events",
                    "ai_decision": "ai_decisions",
                    "world_model": "cleaning_regions",
                }.get(kind)
                stored = (
                    payload.get("attempt")
                    if kind == "cleaning_result"
                    else payload.get("world", {}).get("regions")
                    if kind == "world_model"
                    else payload
                )
                if table and stored is not None:
                    key = (self.mission_id, kind)
                    if stored != self.recorded.get(key):
                        self.store.record(
                            table,
                            self.mission_id,
                            data["stamp"],
                            {"regions": stored} if kind == "world_model" else stored,
                        )
                        self.recorded[key] = stored
                if kind == "cleaning_result" and data["payload"].get("attempt"):
                    self.attempts = (self.attempts + [data["payload"]["attempt"]])[-100:]
                if kind in ("ai_decision", "cleaning_result"):
                    self.events = (
                        self.events
                        + [{"event": kind, "timestamp": data["stamp"], "data": data["payload"]}]
                    )[-100:]
        except ValueError:
            pass

    def camera(self, msg):
        with self.lock:
            self.image = msg

    def map(self, msg):
        with self.lock:
            self.map_size = {
                "width": msg.info.width * msg.info.resolution,
                "height": msg.info.height * msg.info.resolution,
                "origin": {
                    "x": msg.info.origin.position.x,
                    "y": msg.info.origin.position.y,
                    "yaw": math.atan2(
                        2
                        * (
                            msg.info.origin.orientation.w * msg.info.origin.orientation.z
                            + msg.info.origin.orientation.x * msg.info.origin.orientation.y
                        ),
                        1
                        - 2 * (msg.info.origin.orientation.y**2 + msg.info.origin.orientation.z**2),
                    ),
                },
            }

    def nav_path(self, msg):
        with self.lock:
            self.path = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]

    def snapshot(self):
        with self.lock:
            data = dict(self.data)
            attempts = list(self.attempts)
            events = list(self.events)
            size = dict(self.map_size)
            path = list(self.path)
        now = self.seconds()
        world = data.get("world_model", {})
        payload = world.get("payload", {})
        mission = data.get("mission_state", {})
        safety = data.get("safety", {})
        fresh = 0 <= now - world.get("stamp", -100) <= self.config.safety.watchdog_s
        safe = (
            safety.get("payload", {})
            if 0 <= now - safety.get("stamp", -100) <= self.config.safety.watchdog_s
            else {"safe": False, "reasons": ["ros_telemetry_stale"]}
        )
        semantic = dict(payload.get("world", {}), **size)
        regions = semantic.get("regions", [])
        result = {
            "mode": self.mode,
            "mission_id": self.mission_id,
            "state": "FAULT"
            if safe.get("latched")
            else mission.get("payload", {}).get("state", "BOOTING"),
            "connected": fresh and payload.get("base", {}).get("connected") is True,
            "battery_percent": payload.get("base", {}).get("battery", {}).get("percent"),
            "world": semantic,
            "safety": safe,
            "cloud": data.get("ai_decision", {}).get("payload", {"status": "disabled"}),
            "path": path,
            "attempts": attempts,
            "events": events,
            "metrics": {
                "current_debris_score": sum(r["debris_score"] for r in regions),
                "regions_remaining": sum(
                    not r["cleaned"] and r["debris_score"] > self.config.cleaning.success_threshold
                    for r in regions
                ),
                "successful_passes": sum(a["success"] for a in attempts),
                "retried_passes": sum(a["pass_number"] > 1 for a in attempts),
            },
            "self_test": {
                "status": "passed"
                if mission.get("payload", {}).get("state") not in (None, "SELF_TEST")
                else "pending"
            },
        }
        try:
            transform = self.tf.lookup_transform("map", "base_link", Time())
            p = transform.transform.translation
            q = transform.transform.rotation
            result["pose"] = {
                "x": p.x,
                "y": p.y,
                "yaw": math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)),
            }
        except Exception:
            pass
        return result

    def application(self):
        app = FastAPI(title="NeuraVac ROS bridge")

        async def auth(authorization: str | None = Header(default=None)):
            if self.token and not hmac.compare_digest(authorization or "", f"Bearer {self.token}"):
                raise HTTPException(401, "Dashboard token required")

        guard = [Depends(auth)]

        @app.get("/api/health")
        async def health():
            return {
                "status": "ok",
                "mode": self.mode,
                "mission_id": self.mission_id,
                "transport": "ros2",
                "connected": self.snapshot()["connected"],
            }

        @app.get("/api/state", dependencies=guard)
        async def state():
            return self.snapshot()

        async def invoke(action):
            client = self.clients.get(action)
            if not client:
                raise HTTPException(404, "Unknown action")
            if not client.service_is_ready():
                raise HTTPException(503, "ROS control service unavailable")
            future = client.call_async(Trigger.Request())
            deadline = time.monotonic() + 3
            while not future.done() and time.monotonic() < deadline:
                await asyncio.sleep(0.02)
            if not future.done():
                raise HTTPException(504, "ROS control timed out")
            result = future.result()
            if not result.success:
                raise HTTPException(409, result.message)
            return self.snapshot()

        @app.post("/api/mission/{action}", dependencies=guard)
        async def control(action: str):
            return await invoke(action)

        @app.post("/api/demo/move-chair", dependencies=guard)
        async def move():
            return await invoke("move-chair")

        @app.get("/api/camera", dependencies=guard)
        async def camera():
            with self.lock:
                frame = self.image
            if (
                frame is None
                or not 0
                <= self.seconds() - (frame.header.stamp.sec + frame.header.stamp.nanosec / 1e9)
                <= self.config.safety.camera_timeout_s
            ):
                raise HTTPException(503, "Camera unavailable")
            try:
                from PIL import Image as PILImage

                if frame.encoding not in ("rgb8", "bgr8"):
                    raise ValueError("unsupported camera encoding")
                pixels = (
                    np.frombuffer(bytes(frame.data), np.uint8)
                    .reshape(frame.height, frame.step)[:, : frame.width * 3]
                    .reshape(frame.height, frame.width, 3)
                )
                if frame.encoding == "bgr8":
                    pixels = pixels[:, :, ::-1]
                stream = io.BytesIO()
                PILImage.fromarray(pixels).save(stream, format="PNG")
                return Response(
                    stream.getvalue(), media_type="image/png", headers={"Cache-Control": "no-store"}
                )
            except (ImportError, ValueError):
                raise HTTPException(
                    503, "Install Pillow and configure an RGB/BGR8 camera"
                ) from None

        @app.get("/api/history/{table}", dependencies=guard)
        async def history(table: str):
            if table not in TABLES:
                raise HTTPException(404, "Unknown mission history table")
            with self.lock:
                return self.store.export_table(table)

        @app.websocket("/ws")
        async def ws(socket: WebSocket):
            await socket.accept()
            if self.token:
                try:
                    message = await asyncio.wait_for(socket.receive_json(), 5)
                    if not hmac.compare_digest(str(message.get("token", "")), self.token):
                        await socket.close(code=1008)
                        return
                except Exception:
                    await socket.close(code=1008)
                    return
            try:
                while True:
                    await asyncio.wait_for(socket.send_json(self.snapshot()), 1)
                    await asyncio.sleep(0.25)
            except (WebSocketDisconnect, TimeoutError, RuntimeError):
                pass

        dist = self.declare_parameter("static_dir", "").value
        if dist and Path(dist).is_dir():
            app.mount("/", StaticFiles(directory=dist, html=True), name="dashboard")
        return app

    def destroy_node(self):
        self.server.should_exit = True
        self.thread.join(timeout=2)
        with self.lock:
            self.store.close()
        return super().destroy_node()


def main():
    spin(DashboardNode)

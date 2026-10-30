"""Standalone operator page for the staged autonomous mapping coordinator."""
import json
import math
import os
import threading
import time
import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid, Path
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from std_msgs.msg import String
from .autonomy_http import create_app


def _grid_payload(msg):
    info, q = msg.info, msg.info.origin.orientation
    if (msg.header.frame_id != 'map' or info.width <= 0 or info.height <= 0 or
            len(msg.data) != info.width * info.height or info.width * info.height > 4_000_000 or
            not math.isfinite(info.resolution) or info.resolution <= 0 or
            not all(math.isfinite(v) for v in (info.origin.position.x, info.origin.position.y, q.x, q.y, q.z, q.w)) or
            abs(sum(v*v for v in (q.x, q.y, q.z, q.w)) - 1) > .05):
        return None
    return {'width': info.width, 'height': info.height, 'resolution': info.resolution,
            'origin_x': info.origin.position.x, 'origin_y': info.origin.position.y,
            'origin_yaw': math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z)),
            'data': list(msg.data)}


class DashboardBridge(Node):
    def __init__(self):
        super().__init__('autonomous_mapping_dashboard')
        self.lock = threading.Lock()
        self.map = self.costmap = self.path = self.pose = self.state = None
        self.map_at = self.costmap_at = self.path_at = self.pose_at = self.state_at = None
        self.publisher = self.create_publisher(String, 'autonomy/request', 10)
        durable = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(OccupancyGrid, 'slam/map', self.on_map, durable)
        self.create_subscription(OccupancyGrid, '/global_costmap/costmap', self.on_costmap, durable)
        self.create_subscription(Path, '/plan', self.on_path, 10)
        self.create_subscription(PoseStamped, 'slam/pose', self.on_pose, 10)
        self.create_subscription(String, 'autonomy/state', self.on_state, 10)

    def on_map(self, msg):
        payload = _grid_payload(msg)
        if payload is not None:
            with self.lock:
                self.map, self.map_at = payload, time.monotonic()

    def on_costmap(self, msg):
        payload = _grid_payload(msg)
        if payload is not None:
            with self.lock:
                self.costmap, self.costmap_at = payload, time.monotonic()

    def on_path(self, msg):
        if msg.header.frame_id != 'map':
            return
        pts = [[p.pose.position.x, p.pose.position.y] for p in msg.poses
               if math.isfinite(p.pose.position.x) and math.isfinite(p.pose.position.y)]
        with self.lock:
            self.path, self.path_at = pts, time.monotonic()

    def on_pose(self, msg):
        x, y = msg.pose.position.x, msg.pose.position.y
        if msg.header.frame_id != 'map' or not math.isfinite(x) or not math.isfinite(y):
            return
        with self.lock:
            self.pose, self.pose_at = [x, y], time.monotonic()

    def on_state(self, msg):
        try:
            state = json.loads(msg.data)
            if not isinstance(state, dict):
                return
        except (TypeError, ValueError):
            return
        with self.lock:
            self.state, self.state_at = state, time.monotonic()

    def snapshot(self):
        now = time.monotonic()
        with self.lock:
            return {'map': self.map if self.map_at is not None and now-self.map_at <= 5 else None,
                    'costmap': self.costmap if self.costmap_at is not None and now-self.costmap_at <= 10 else None,
                    'path': self.path if self.path_at is not None and now-self.path_at <= 3 else None,
                    'pose': self.pose if self.pose_at is not None and now-self.pose_at <= 1 else None,
                    'state': self.state if self.state_at is not None and now-self.state_at <= 1 else None}

    def send(self, payload):
        self.publisher.publish(String(data=json.dumps(payload)))


def main():
    rclpy.init()
    bridge = DashboardBridge()
    executor = SingleThreadedExecutor()
    executor.add_node(bridge)
    thread = threading.Thread(target=executor.spin, daemon=True)
    thread.start()
    try:
        create_app(bridge).run(host=os.environ.get('NEURAVAC_AUTONOMY_HOST', '127.0.0.1'),
                               port=int(os.environ.get('NEURAVAC_AUTONOMY_PORT', '5050')),
                               debug=False, use_reloader=False, threaded=True)
    finally:
        executor.shutdown()
        thread.join(timeout=2)
        bridge.destroy_node()
        rclpy.try_shutdown()

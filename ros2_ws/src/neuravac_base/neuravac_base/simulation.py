"""Labeled 2D sensors and core simulated motors. All routes are executed by Nav2."""

import math

from nav_msgs.msg import OccupancyGrid
from rclpy.qos import DurabilityPolicy, QoSProfile
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import String
from std_srvs.srv import Trigger

from neuravac_base.node import BaseNode
from neuravac_base.util import ConfigNode, spin
from sim.sim2d.base import SimRobotBase
from sim.sim2d.environment import Environment


class SimulationNode(BaseNode):
    def __init__(self):
        ConfigNode.__init__(self, "simulation_base")
        self.config.backend = "sim"
        self.environment = Environment.demo()
        base = SimRobotBase(self.environment, self.config)
        self.initialize(base)
        # Encoder odometry shares the simulator's initial map pose.
        self.driver.pose = self.environment.start.model_copy()
        self.scan_pub = self.create_publisher(LaserScan, "/scan", 10)
        self.camera_pub = self.create_publisher(Image, "/camera/image_raw", 10)
        self.label_pub = self.create_publisher(String, "/sim/labels", 10)
        self.map_pub = self.create_publisher(
            OccupancyGrid, "/map", QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        )
        self.create_service(Trigger, "/sim/move_chair", self.move_chair)
        self.create_timer(0.1, self.sensors_sim)
        self.create_timer(1, self.map_sim)

    def move_chair(self, request, response):
        with self.lock:
            self.environment.move_obstacle("chair", 2.5, 1.0)
        response.success = True
        response.message = "Simulated chair moved"
        return response

    async def step_simulation(self, dt):
        with self.lock:
            self.driver.base.step(dt)

    def sensors_sim(self):
        stamp = self.get_clock().now().to_msg()
        now_sec = self.seconds()
        scan = LaserScan()
        scan.header.stamp = stamp
        scan.header.frame_id = "laser_frame"
        scan.angle_min = 0.0
        scan.angle_max = 2 * math.pi - 2 * math.pi / 72
        scan.angle_increment = 2 * math.pi / 72
        scan.range_min = 0.05
        scan.range_max = 8.0
        scan.scan_time = 0.1
        with self.lock:
            scan.ranges = self.environment.lidar(self.driver.base.pose)
            labels = self.environment.observe(now_sec)
        self.scan_pub.publish(scan)
        frame = Image()
        frame.header.stamp = stamp
        frame.header.frame_id = "camera_optical_frame"
        frame.height = 320
        frame.width = 320
        frame.encoding = "rgb8"
        frame.step = 960
        frame.data = bytes(320 * 320 * 3)
        self.camera_pub.publish(frame)
        self.publish_json(
            self.label_pub,
            "detections",
            {"available": True, "detections": [d.model_dump(mode="json") for d in labels]},
            now_sec,
        )

    def map_sim(self):
        grid = OccupancyGrid()
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.header.frame_id = "map"
        grid.info.resolution = 0.1
        grid.info.width = 60
        grid.info.height = 40
        grid.info.origin.orientation.w = 1.0
        grid.data = [
            0 if self.environment.free((col + 0.5) * 0.1, (row + 0.5) * 0.1, 0) else 100
            for row in range(40)
            for col in range(60)
        ]
        self.map_pub.publish(grid)


def main():
    spin(SimulationNode)

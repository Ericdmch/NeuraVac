"""Lightweight 2-D LiDAR scan-matching mapper for NeuraVac."""

import math

import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from roomba_interfaces.msg import LidarPoint


class LidarSlam(Node):
    """Accumulate scans into an occupancy grid using correlative matching."""

    def __init__(self):
        super().__init__('lidar_slam_node')
        self.declare_parameter('map_resolution', 0.05)
        self.declare_parameter('map_width', 400)
        self.declare_parameter('map_height', 400)
        self.declare_parameter('max_range_m', 8.0)
        self.resolution = float(self.get_parameter('map_resolution').value)
        self.width = int(self.get_parameter('map_width').value)
        self.height = int(self.get_parameter('map_height').value)
        self.max_range = float(self.get_parameter('max_range_m').value)
        self.grid = [-1] * (self.width * self.height)
        self.scan = []
        self.previous = []
        self.pose = [0.0, 0.0, 0.0]
        self.publisher = self.create_publisher(OccupancyGrid, 'slam/map', 1)
        self.subscription = self.create_subscription(
            LidarPoint, 'lidar_points', self.on_point, 100)
        self.get_logger().info('LiDAR SLAM mapper ready; publishing /slam/map')

    def on_point(self, message):
        angle = float(message.angle_deg)
        if self.scan and angle < self.scan[-1][0] - 180:
            self.process_scan()
            self.scan.clear()
        distance = float(message.distance_mm) / 1000.0
        if 0.08 < distance <= self.max_range:
            self.scan.append((angle, distance))

    def process_scan(self):
        points = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
                  for a, r in self.scan]
        if len(points) < 20:
            return
        if self.previous:
            self.match_scan(points)
        self.previous = points
        self.integrate(points)
        self.publish_map()

    def match_scan(self, points):
        """Search a small pose neighborhood against the preceding scan."""
        stride = max(1, len(points) // 90)
        reference = self.previous[::stride]
        sample = points[::stride]
        best = (float('inf'), 0.0, 0.0, 0.0)
        for da in (-0.06, -0.03, 0.0, 0.03, 0.06):
            c, s = math.cos(da), math.sin(da)
            for dx in (-0.10, -0.05, 0.0, 0.05, 0.10):
                for dy in (-0.10, -0.05, 0.0, 0.05, 0.10):
                    error = 0.0
                    for x, y in sample:
                        x, y = c * x - s * y + dx, s * x + c * y + dy
                        nearest = min((x - rx) ** 2 + (y - ry) ** 2
                                      for rx, ry in reference)
                        error += min(nearest, 0.25)
                    if error < best[0]:
                        best = (error, dx, dy, da)
        _, dx, dy, da = best
        heading = self.pose[2]
        self.pose[0] += math.cos(heading) * dx - math.sin(heading) * dy
        self.pose[1] += math.sin(heading) * dx + math.cos(heading) * dy
        self.pose[2] += da

    def integrate(self, points):
        origin_x = self.width // 2 + round(self.pose[0] / self.resolution)
        origin_y = self.height // 2 + round(self.pose[1] / self.resolution)
        c, s = math.cos(self.pose[2]), math.sin(self.pose[2])
        for px, py in points[::2]:
            ex = origin_x + round((c * px - s * py) / self.resolution)
            ey = origin_y + round((s * px + c * py) / self.resolution)
            steps = max(abs(ex - origin_x), abs(ey - origin_y), 1)
            for step in range(steps):
                x = origin_x + round((ex - origin_x) * step / steps)
                y = origin_y + round((ey - origin_y) * step / steps)
                if 0 <= x < self.width and 0 <= y < self.height:
                    index = y * self.width + x
                    if self.grid[index] == -1:
                        self.grid[index] = 0
            if 0 <= ex < self.width and 0 <= ey < self.height:
                self.grid[ey * self.width + ex] = 100

    def publish_map(self):
        message = OccupancyGrid()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'map'
        message.info.resolution = self.resolution
        message.info.width = self.width
        message.info.height = self.height
        message.info.origin.position.x = -self.width * self.resolution / 2
        message.info.origin.position.y = -self.height * self.resolution / 2
        message.data = self.grid
        self.publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = LidarSlam()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

"""Lightweight 2-D LiDAR scan-matching mapper for NeuraVac."""

import math

import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from roomba_interfaces.msg import LidarPoint, SerialData


class LidarSlam(Node):
    """Accumulate scans into an occupancy grid using correlative matching."""

    def __init__(self):
        super().__init__('lidar_slam_node')
        self.declare_parameter('map_resolution', 0.05)
        self.declare_parameter('map_width', 400)
        self.declare_parameter('map_height', 400)
        self.declare_parameter('max_range_m', 8.0)
        self.declare_parameter('lidar_correction_weight', 0.25)
        self.resolution = float(self.get_parameter('map_resolution').value)
        self.width = int(self.get_parameter('map_width').value)
        self.height = int(self.get_parameter('map_height').value)
        self.max_range = float(self.get_parameter('max_range_m').value)
        self.lidar_weight = float(self.get_parameter('lidar_correction_weight').value)
        self.grid = [-1] * (self.width * self.height)
        self.hits = [0] * (self.width * self.height)
        self.scan = []
        self.previous = []
        self.pose = [0.0, 0.0, 0.0]
        self.odom_pose = [0.0, 0.0, 0.0]
        self.odom_seen = False
        self.scan_odom_pose = [0.0, 0.0, 0.0]
        self.serial_buffer = bytearray()
        self.publisher = self.create_publisher(OccupancyGrid, 'slam/map', 1)
        self.subscription = self.create_subscription(
            LidarPoint, 'lidar_points', self.on_point, 100)
        self.odom_subscription = self.create_subscription(
            SerialData, 'serial_rx', self.on_serial, 20)
        self.get_logger().info('LiDAR and Roomba odometry mapper ready; publishing /slam/map')

    def on_serial(self, message):
        self.serial_buffer.extend(message.data)
        while len(self.serial_buffer) >= 26:
            if (all(value in (0, 1) for value in self.serial_buffer[1:7])
                    and self.serial_buffer[16] <= 5):
                packet = self.serial_buffer[:26]
                del self.serial_buffer[:26]
                distance = int.from_bytes(packet[12:14], 'big', signed=True) / 1000.0
                angle = math.radians(int.from_bytes(packet[14:16], 'big', signed=True))
                mid = self.odom_pose[2] + angle / 2
                self.odom_pose[0] += distance * math.cos(mid)
                self.odom_pose[1] += distance * math.sin(mid)
                self.odom_pose[2] += angle
                self.odom_seen = True
            else:
                del self.serial_buffer[0]
        if len(self.serial_buffer) > 128:
            del self.serial_buffer[:-25]

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
        odom_dx = self.odom_pose[0] - self.scan_odom_pose[0]
        odom_dy = self.odom_pose[1] - self.scan_odom_pose[1]
        odom_da = self.odom_pose[2] - self.scan_odom_pose[2]
        if self.previous:
            scan_delta = self.match_scan(points)
            if scan_delta is not None:
                weight = self.lidar_weight if self.odom_seen else 1.0
                odom_dx = (1 - weight) * odom_dx + weight * scan_delta[0]
                odom_dy = (1 - weight) * odom_dy + weight * scan_delta[1]
                odom_da = (1 - weight) * odom_da + weight * scan_delta[2]
        heading = self.pose[2]
        self.pose[0] += math.cos(heading) * odom_dx - math.sin(heading) * odom_dy
        self.pose[1] += math.sin(heading) * odom_dx + math.cos(heading) * odom_dy
        self.pose[2] += odom_da
        self.scan_odom_pose = list(self.odom_pose)
        self.previous = points
        self.integrate(points)
        self.publish_map()

    def match_scan(self, points):
        """Estimate robot motion between scans, in the previous scan frame."""
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
        # The local transform aligns current points to the previous scan; invert
        # it to obtain the LiDAR estimate of robot motion, then blend with wheel odometry.
        scan_da = -da
        scan_dx = -(math.cos(da) * dx + math.sin(da) * dy)
        scan_dy = -(-math.sin(da) * dx + math.cos(da) * dy)
        return scan_dx, scan_dy, scan_da

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
                index = ey * self.width + ex
                self.hits[index] = min(255, self.hits[index] + 1)
                # Values 50-79 are tentative returns; repeatedly observed walls
                # become stable occupied cells (80-100).
                self.grid[index] = min(100, 50 + self.hits[index] * 10)

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

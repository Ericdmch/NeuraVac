"""Small-room 2D SLAM using LiDAR scans with wheel odometry as a prior."""

import math
import threading

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import Odometry
from rclpy.node import Node
from roomba_interfaces.msg import LidarPoint
from std_srvs.srv import Trigger


def scan_to_cartesian(scan):
    """Convert COIN-D6 clockwise angles into ROS counter-clockwise points."""
    angles = -scan[:, 0]
    ranges = scan[:, 1]
    return np.column_stack((ranges * np.cos(angles), ranges * np.sin(angles)))


class LidarMapper(Node):
    """Accumulate full revolutions, align them against the map, and map rays."""

    def __init__(self):
        super().__init__('neuravac_slam')
        self.declare_parameter('resolution_m', 0.05)
        self.declare_parameter('map_size_m', 20.0)
        self.declare_parameter('min_range_m', 0.12)
        self.declare_parameter('max_range_m', 8.0)
        self.declare_parameter('scan_match_window_m', 0.20)
        self.declare_parameter('scan_match_window_deg', 12.0)
        self.declare_parameter('map_publish_hz', 2.0)
        value = lambda name: self.get_parameter(name).value
        self.resolution = float(value('resolution_m'))
        self.size = max(100, int(float(value('map_size_m')) / self.resolution))
        self.origin = -(self.size * self.resolution) / 2.0
        self.min_range = float(value('min_range_m'))
        self.max_range = float(value('max_range_m'))
        self.match_window = float(value('scan_match_window_m'))
        self.match_angle = math.radians(float(value('scan_match_window_deg')))
        self.grid = np.zeros((self.size, self.size), dtype=np.int8)
        self._scan = []
        self._last_angle = None
        self._last_scan = None
        self._pose = np.zeros(3, dtype=np.float64)
        self._odom_pose = None
        self._odom_at_last_scan = None
        self._lock = threading.Lock()
        self._map_version = 0
        self._published_version = -1
        self.create_subscription(LidarPoint, 'lidar_points', self.on_point, 50)
        self.create_subscription(Odometry, 'odom', self.on_odometry, 10)
        self.map_pub = self.create_publisher(OccupancyGrid, 'slam/map', 1)
        self.create_service(Trigger, 'slam/reset', self.reset_map)
        self.create_timer(1.0 / max(0.2, float(value('map_publish_hz'))), self.publish_map)
        self.get_logger().info(
            f'LiDAR-only SLAM ready: {self.size}x{self.size}, '
            f'{self.resolution:.2f} m/cell; wheel odometry is a scan-matching prior'
        )

    def reset_map(self, _request, response):
        """Clear accumulated state; subsequent scans build a fresh map."""
        with self._lock:
            self.grid.fill(0)
            self._scan.clear()
            self._last_angle = None
            self._last_scan = None
            self._pose.fill(0.0)
            self._odom_at_last_scan = (
                self._odom_pose.copy() if self._odom_pose is not None else None
            )
            self._map_version += 1
        response.success = True
        response.message = 'SLAM map and pose reset; mapping resumes with the next LiDAR scans.'
        self.get_logger().info(response.message)
        return response

    def on_odometry(self, message):
        q = message.pose.pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        self._odom_pose = np.array((
            message.pose.pose.position.x,
            message.pose.pose.position.y,
            yaw,
        ), dtype=np.float64)

    def _predict_from_odometry(self):
        if self._odom_pose is None:
            return
        current = self._odom_pose.copy()
        if self._odom_at_last_scan is None:
            self._odom_at_last_scan = current
            return
        previous = self._odom_at_last_scan
        delta_x, delta_y = current[0] - previous[0], current[1] - previous[1]
        c, s = math.cos(previous[2]), math.sin(previous[2])
        local_delta = np.array((c * delta_x + s * delta_y,
                                -s * delta_x + c * delta_y))
        c, s = math.cos(self._pose[2]), math.sin(self._pose[2])
        self._pose[:2] += np.array((c * local_delta[0] - s * local_delta[1],
                                    s * local_delta[0] + c * local_delta[1]))
        yaw_delta = math.atan2(
            math.sin(current[2] - previous[2]),
            math.cos(current[2] - previous[2]),
        )
        self._pose[2] = math.atan2(
            math.sin(self._pose[2] + yaw_delta),
            math.cos(self._pose[2] + yaw_delta),
        )
        self._odom_at_last_scan = current

    def on_point(self, message):
        angle = math.radians(float(message.angle_deg) % 360.0)
        if self._last_angle is not None:
            delta = angle - self._last_angle
            # LiDAR packet order normally advances monotonically. A large
            # discontinuity marks the seam between revolutions.
            if abs(delta) > math.pi:
                if len(self._scan) >= 40:
                    scan = np.asarray(self._scan, dtype=np.float64)
                    self._scan = []
                    self._process_scan(scan)
                else:
                    self._scan.clear()
        self._last_angle = angle
        distance = float(message.distance_mm) / 1000.0
        if self.min_range <= distance <= self.max_range:
            self._scan.append((angle, distance))

    def _local_points(self, scan):
        # Bound CPU while retaining evenly spaced angular coverage.
        if len(scan) > 360:
            take = np.linspace(0, len(scan) - 1, 360).astype(np.int32)
            scan = scan[take]
        return scan_to_cartesian(scan)

    def _match_scan(self, points):
        occupied = self.grid > 2
        if not occupied.any():
            return self._pose.copy()
        best_pose = self._pose.copy()
        best_score = -1.0
        step = max(self.resolution, self.match_window / 4.0)
        translations = np.arange(-self.match_window, self.match_window + step / 2, step)
        rotations = np.linspace(-self.match_angle, self.match_angle, 9)
        # Search around the last LiDAR-derived pose. Free cells are ignored;
        # this makes sparse and short-range returns less likely to pull the pose.
        for dyaw in rotations:
            theta = self._pose[2] + dyaw
            c, s = math.cos(theta), math.sin(theta)
            rotated_x = c * points[:, 0] - s * points[:, 1]
            rotated_y = s * points[:, 0] + c * points[:, 1]
            for dx in translations:
                for dy in translations:
                    ix = np.rint((rotated_x + self._pose[0] + dx - self.origin) / self.resolution).astype(np.int32)
                    iy = np.rint((rotated_y + self._pose[1] + dy - self.origin) / self.resolution).astype(np.int32)
                    valid = (ix >= 0) & (iy >= 0) & (ix < self.size) & (iy < self.size)
                    if not valid.any():
                        continue
                    score = float(np.count_nonzero(occupied[iy[valid], ix[valid]])) / len(points)
                    if score > best_score:
                        best_score = score
                        best_pose = np.array((self._pose[0] + dx,
                                              self._pose[1] + dy, theta))
        # If the scan has almost no overlap, do not invent a large correction.
        if best_score < 0.04:
            return self._pose.copy()
        return best_pose

    def _process_scan(self, scan):
        points = self._local_points(scan)
        if len(points) < 30:
            return
        with self._lock:
            if self._last_scan is not None:
                self._predict_from_odometry()
                self._pose = self._match_scan(points)
            elif self._odom_pose is not None:
                self._odom_at_last_scan = self._odom_pose.copy()
            theta = self._pose[2]
            c, s = math.cos(theta), math.sin(theta)
            rotation = np.array(((c, -s), (s, c)))
            world = points @ rotation.T + self._pose[:2]
            scanner = self._pose[:2]
            for endpoint in world:
                self._trace_ray(scanner, endpoint)
            self._last_scan = points
            self._map_version += 1

    def _trace_ray(self, start, end):
        start_cell = np.rint((start - self.origin) / self.resolution).astype(np.int32)
        end_cell = np.rint((end - self.origin) / self.resolution).astype(np.int32)
        steps = max(abs(int(end_cell[0] - start_cell[0])),
                    abs(int(end_cell[1] - start_cell[1])))
        if steps == 0:
            return
        xs = np.rint(np.linspace(start_cell[0], end_cell[0], steps + 1)).astype(np.int32)
        ys = np.rint(np.linspace(start_cell[1], end_cell[1], steps + 1)).astype(np.int32)
        inside = (xs >= 0) & (ys >= 0) & (xs < self.size) & (ys < self.size)
        xs, ys = xs[inside], ys[inside]
        if not len(xs):
            return
        # Slow accumulation and clamp keep walls persistent while allowing a
        # previously observed wall to clear when a new scan sees through it.
        self.grid[ys[:-1], xs[:-1]] = np.maximum(-8, self.grid[ys[:-1], xs[:-1]] - 1)
        x, y = int(end_cell[0]), int(end_cell[1])
        if 0 <= x < self.size and 0 <= y < self.size:
            self.grid[y, x] = min(16, int(self.grid[y, x]) + 3)

    def publish_map(self):
        with self._lock:
            if self._map_version == self._published_version:
                return
            message = OccupancyGrid()
            message.header.stamp = self.get_clock().now().to_msg()
            message.header.frame_id = 'map'
            message.info.resolution = self.resolution
            message.info.width = self.size
            message.info.height = self.size
            message.info.origin.position.x = self.origin
            message.info.origin.position.y = self.origin
            message.info.origin.orientation.w = 1.0
            values = np.full(self.grid.shape, -1, dtype=np.int8)
            seen = self.grid != 0
            values[seen] = 0
            occupied = self.grid > 0
            values[occupied] = np.clip(
                self.grid[occupied].astype(np.int16) * 8 + 40, 40, 100
            ).astype(np.int8)
            message.data = values.reshape(-1).tolist()
            self._published_version = self._map_version
        self.map_pub.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = LidarMapper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

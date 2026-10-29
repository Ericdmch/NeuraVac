"""Small-room 2D SLAM using LiDAR scans with wheel odometry as a prior."""

import math
import threading
import time
from pathlib import Path
import os

import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import Odometry
from rclpy.node import Node
from roomba_interfaces.msg import LidarPoint, SerialData
from std_srvs.srv import Trigger


def scan_to_cartesian(scan):
    """Convert COIN-D6 clockwise angles into ROS counter-clockwise points."""
    angles = -scan[:, 0]
    ranges = scan[:, 1]
    return np.column_stack((ranges * np.cos(angles), ranges * np.sin(angles)))


def rotation_search_angles(odom_fresh, odom_window, fallback_window, fallback_steps):
    """Broaden rotation matching when no recent wheel-odometry prior exists."""
    if odom_fresh:
        return np.linspace(-odom_window, odom_window, 9)
    return np.linspace(-fallback_window, fallback_window, fallback_steps)


def refine_icp(points, target, seed, max_distance=0.20, iterations=8):
    """Refine a pose with trimmed nearest-neighbor rigid alignment."""
    pose = np.asarray(seed, dtype=float).copy()
    if len(target) < 30 or len(points) < 30:
        return pose, 0.0, float('inf')

    def pairs(world):
        # Keep memory bounded even when the room map is large.
        nearest = []
        distances = []
        for start in range(0, len(world), 60):
            delta = world[start:start + 60, None, :] - target[None, :, :]
            squared = np.sum(delta * delta, axis=2)
            indices = np.argmin(squared, axis=1)
            nearest.extend(indices)
            distances.extend(np.sqrt(squared[np.arange(len(indices)), indices]))
        return np.asarray(nearest), np.asarray(distances)

    for _ in range(iterations):
        c, s = math.cos(pose[2]), math.sin(pose[2])
        world = points @ np.array(((c, -s), (s, c))).T + pose[:2]
        indices, distances = pairs(world)
        eligible = np.flatnonzero(distances < max_distance)
        if len(eligible) < 30:
            return pose, 0.0, float('inf')
        keep = eligible[np.argsort(distances[eligible])[:max(30, int(len(eligible) * 0.75))]]
        source = world[keep]
        destination = target[indices[keep]]
        center_source, center_target = source.mean(axis=0), destination.mean(axis=0)
        u, _, vt = np.linalg.svd((source - center_source).T @ (destination - center_target))
        rotation = vt.T @ u.T
        if np.linalg.det(rotation) < 0:
            vt[-1] *= -1
            rotation = vt.T @ u.T
        translation = center_target - rotation @ center_source
        pose[:2] = rotation @ pose[:2] + translation
        angle = math.atan2(rotation[1, 0], rotation[0, 0])
        pose[2] = math.atan2(math.sin(pose[2] + angle), math.cos(pose[2] + angle))
        if np.linalg.norm(translation) < 0.001 and abs(angle) < 0.0005:
            break
    c, s = math.cos(pose[2]), math.sin(pose[2])
    world = points @ np.array(((c, -s), (s, c))).T + pose[:2]
    _, distances = pairs(world)
    inliers = distances < max_distance
    ratio = float(np.mean(inliers))
    rmse = float(np.sqrt(np.mean(distances[inliers] ** 2))) if inliers.any() else float('inf')
    return pose, ratio, rmse


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
        self.declare_parameter('scan_match_fallback_window_deg', 45.0)
        self.declare_parameter('scan_match_fallback_steps', 19)
        self.declare_parameter('odom_stale_sec', 1.5)
        self.declare_parameter('map_publish_hz', 2.0)
        self.declare_parameter('min_scan_overlap', 0.15)
        self.declare_parameter('collision_pause_sec', 1.0)
        self.declare_parameter('map_file', '~/Neuravac/maps/room.npz')
        self.declare_parameter('icp_max_distance_m', 0.20)
        self.declare_parameter('icp_min_inlier_ratio', 0.40)
        self.declare_parameter('icp_max_rmse_m', 0.10)
        self.declare_parameter('recovery_scans', 3)
        value = lambda name: self.get_parameter(name).value
        self.resolution = float(value('resolution_m'))
        self.size = max(100, int(float(value('map_size_m')) / self.resolution))
        self.origin = -(self.size * self.resolution) / 2.0
        self.min_range = float(value('min_range_m'))
        self.max_range = float(value('max_range_m'))
        self.match_window = float(value('scan_match_window_m'))
        self.match_angle = math.radians(float(value('scan_match_window_deg')))
        self.fallback_match_angle = math.radians(
            float(value('scan_match_fallback_window_deg'))
        )
        self.fallback_match_steps = max(9, int(value('scan_match_fallback_steps')))
        self.odom_stale_sec = max(0.1, float(value('odom_stale_sec')))
        self.min_scan_overlap = float(value('min_scan_overlap'))
        self.collision_pause = float(value('collision_pause_sec'))
        self.map_file = Path(str(value('map_file'))).expanduser()
        self.icp_distance = float(value('icp_max_distance_m'))
        self.icp_ratio = float(value('icp_min_inlier_ratio'))
        self.icp_rmse = float(value('icp_max_rmse_m'))
        self.recovery_scans = max(2, int(value('recovery_scans')))
        self._recovering = False
        self._recovery_pose = None
        self._recovery_count = 0
        self._collision_until = 0.0
        self._serial_buffer = bytearray()
        self._match_score = 1.0
        self.grid = np.zeros((self.size, self.size), dtype=np.int8)
        self._scan = []
        self._last_angle = None
        self._last_scan = None
        self._pose = np.zeros(3, dtype=np.float64)
        self._odom_pose = None
        self._odom_received_at = None
        self._odom_at_last_scan = None
        self._lock = threading.Lock()
        self._map_version = 0
        self._published_version = -1
        self.create_subscription(LidarPoint, 'lidar_points', self.on_point, 50)
        self.create_subscription(Odometry, 'odom', self.on_odometry, 10)
        self.create_subscription(SerialData, 'serial_rx', self.on_serial, 10)
        self.map_pub = self.create_publisher(OccupancyGrid, 'slam/map', 1)
        self.pose_pub = self.create_publisher(PoseStamped, 'slam/pose', 10)
        self.create_service(Trigger, 'slam/reset', self.reset_map)
        self.create_service(Trigger, 'slam/save', self.save_map)
        self.create_service(Trigger, 'slam/load', self.load_map)
        self.create_timer(1.0 / max(0.2, float(value('map_publish_hz'))), self.publish_map)
        self._publish_pose()
        self.get_logger().info(
            f'LiDAR-only SLAM ready: {self.size}x{self.size}, '
            f'{self.resolution:.2f} m/cell; wheel odometry is a scan-matching prior'
        )

    def on_serial(self, message):
        """Pause map integration after reported bumps or wheel drops."""
        self._serial_buffer.extend(message.data)
        while len(self._serial_buffer) >= 26:
            packet = self._serial_buffer[:26]
            if any(v not in (0, 1) for v in packet[1:7]) or packet[16] > 5:
                del self._serial_buffer[0]
                continue
            del self._serial_buffer[:26]
            if packet[0] & 31:
                self._collision_until = time.monotonic() + self.collision_pause
                self._recovering = True
                self._recovery_pose = None
                self._recovery_count = 0

    def save_map(self, _request, response):
        """Atomically save map evidence and its associated robot pose."""
        try:
            self.map_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.map_file.with_suffix('.tmp')
            with self._lock:
                with temporary.open('wb') as output:
                    np.savez_compressed(output, grid=self.grid, pose=self._pose,
                                        resolution=self.resolution, origin=self.origin)
            os.replace(temporary, self.map_file)
            response.success = True
            response.message = f'Saved map to {self.map_file}'
        except (OSError, ValueError) as error:
            response.success = False
            response.message = str(error)
        return response

    def load_map(self, _request, response):
        """Restore a saved map when the robot is at its saved physical pose."""
        try:
            with np.load(self.map_file, allow_pickle=False) as saved:
                grid = saved['grid'].copy()
                pose = saved['pose'].copy()
                if (grid.shape != self.grid.shape or pose.shape != (3,)
                        or grid.dtype != np.int8
                        or np.any(grid < -8) or np.any(grid > 16)
                        or not np.isfinite(pose).all()
                        or not np.isclose(float(saved['resolution']), self.resolution)
                        or not np.isclose(float(saved['origin']), self.origin)):
                    raise ValueError('Saved map geometry is incompatible.')
            with self._lock:
                self.grid[:] = grid
                self._pose[:] = pose
                self._last_scan = np.empty((0, 2))
                self._recovering = True
                self._recovery_pose = None
                self._recovery_count = 0
                self._scan.clear()
                self._last_angle = None
                self._odom_at_last_scan = (
                    self._odom_pose.copy() if self._odom_pose is not None else None
                )
                self._map_version += 1
            self._publish_pose()
            response.success = True
            response.message = 'Loaded map. Robot must be at the saved position and heading.'
        except (OSError, ValueError, KeyError) as error:
            response.success = False
            response.message = str(error)
        return response

    def reset_map(self, _request, response):
        """Clear accumulated state; subsequent scans build a fresh map."""
        with self._lock:
            self.grid.fill(0)
            self._scan.clear()
            self._last_angle = None
            self._last_scan = None
            self._pose.fill(0.0)
            self._recovering = False
            self._recovery_pose = None
            self._recovery_count = 0
            self._odom_at_last_scan = (
                self._odom_pose.copy() if self._odom_pose is not None else None
            )
            self._map_version += 1
        self._publish_pose()
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
        self._odom_received_at = time.monotonic()

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
        self._match_score = 1.0
        if not occupied.any():
            return self._pose.copy()
        best_pose = self._pose.copy()
        best_score = -1.0
        best_cost = float('inf')
        step = max(self.resolution, self.match_window / 4.0)
        translations = np.arange(-self.match_window, self.match_window + step / 2, step)
        odom_fresh = (
            self._odom_received_at is not None
            and time.monotonic() - self._odom_received_at <= self.odom_stale_sec
        )
        rotations = rotation_search_angles(
            odom_fresh,
            self.match_angle,
            self.fallback_match_angle,
            self.fallback_match_steps,
        )
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
                    cost = dx * dx + dy * dy + dyaw * dyaw
                    if score > best_score + 1e-9 or (abs(score - best_score) < 1e-9 and cost < best_cost):
                        best_score = score
                        best_cost = cost
                        best_pose = np.array((self._pose[0] + dx,
                                              self._pose[1] + dy, theta))
        # If the scan has almost no overlap, do not invent a large correction.
        self._match_score = best_score
        if best_score < 0.04:
            return self._pose.copy()
        return best_pose

    def _process_scan(self, scan):
        points = self._local_points(scan)
        if len(points) < 30:
            return
        with self._lock:
            if time.monotonic() < self._collision_until:
                self._odom_at_last_scan = (
                    self._odom_pose.copy() if self._odom_pose is not None else None
                )
                return
            if self._last_scan is not None:
                previous_pose = self._pose.copy()
                if not self._recovering:
                    self._predict_from_odometry()
                else:
                    self._odom_at_last_scan = (
                        self._odom_pose.copy() if self._odom_pose is not None else None
                    )
                candidate = self._match_scan(points)
                if self._match_score < self.min_scan_overlap:
                    self._pose = previous_pose
                    self._recovering = True
                    self._recovery_count = 0
                    self.get_logger().warning('Rejected scan: insufficient overlap; map held.')
                    return
                ys, xs = np.nonzero(self.grid > 2)
                target = np.column_stack((xs, ys)) * self.resolution + self.origin
                if len(target) > 2500:
                    target = target[np.linspace(0, len(target) - 1, 2500).astype(int)]
                refined, ratio, error = refine_icp(points, target, candidate, self.icp_distance)
                correction_angle = abs(math.atan2(
                    math.sin(refined[2] - candidate[2]),
                    math.cos(refined[2] - candidate[2])))
                if (ratio < self.icp_ratio or error > self.icp_rmse
                        or np.linalg.norm(refined[:2] - candidate[:2]) > 0.25
                        or correction_angle > math.radians(15)):
                    self._pose = previous_pose
                    self._recovering = True
                    self._recovery_count = 0
                    return
                candidate = refined
                jump = abs(math.atan2(math.sin(candidate[2] - previous_pose[2]),
                                      math.cos(candidate[2] - previous_pose[2])))
                if (jump > math.radians(20)
                        or np.linalg.norm(candidate[:2] - previous_pose[:2]) > 0.35):
                    self._pose = previous_pose
                    self._recovering = True
                    self._recovery_count = 0
                    return
                if self._recovering:
                    consistent = self._recovery_pose is not None and (
                        np.linalg.norm(candidate[:2] - self._recovery_pose[:2]) < 0.08
                        and abs(math.atan2(math.sin(candidate[2] - self._recovery_pose[2]),
                                           math.cos(candidate[2] - self._recovery_pose[2]))) < math.radians(5))
                    self._recovery_count = self._recovery_count + 1 if consistent else 1
                    self._recovery_pose = candidate.copy()
                    self._pose = previous_pose
                    if self._recovery_count < self.recovery_scans:
                        return
                    self._recovering = False
                    self._recovery_count = 0
                self._pose = candidate
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
        self._publish_pose()

    def _publish_pose(self):
        with self._lock:
            pose = self._pose.copy()
        message = PoseStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'map'
        message.pose.position.x = float(pose[0])
        message.pose.position.y = float(pose[1])
        message.pose.orientation.z = math.sin(float(pose[2]) / 2.0)
        message.pose.orientation.w = math.cos(float(pose[2]) / 2.0)
        self.pose_pub.publish(message)

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
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.try_shutdown()

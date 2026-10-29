"""Small-room 2D SLAM using LiDAR scans with wheel odometry as a prior."""

import math
import queue
import threading
import time
from bisect import bisect_left
from collections import deque

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
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


def neighbor_support_mask(points, max_neighbor_gap):
    if len(points) < 3 or max_neighbor_gap <= 0.0:
        return np.ones(len(points), dtype=bool)
    previous = np.roll(points, 1, axis=0)
    following = np.roll(points, -1, axis=0)
    previous_gap = np.linalg.norm(points - previous, axis=1)
    following_gap = np.linalg.norm(points - following, axis=1)
    return (
        (previous_gap <= max_neighbor_gap)
        | (following_gap <= max_neighbor_gap)
    )


def rotation_search_angles(odom_fresh, odom_window, fallback_window, fallback_steps):
    """Broaden rotation matching when no recent wheel-odometry prior exists."""
    if odom_fresh:
        return np.linspace(-odom_window, odom_window, 9)
    return np.linspace(-fallback_window, fallback_window, fallback_steps)


def deskew_points_to_reference(points, timestamps, odom_samples, reference):
    """Transform timestamped LiDAR points into one reference robot pose."""
    if len(odom_samples) < 2:
        return points
    sample_times = [sample[0] for sample in odom_samples]
    reference_yaw = reference[2]
    c_ref, s_ref = math.cos(reference_yaw), math.sin(reference_yaw)
    deskewed = points.copy()
    for index, timestamp in enumerate(timestamps):
        right = bisect_left(sample_times, float(timestamp))
        if right <= 0:
            odom = odom_samples[0][1]
        elif right >= len(odom_samples):
            odom = odom_samples[-1][1]
        else:
            before_time, before = odom_samples[right - 1]
            after_time, after = odom_samples[right]
            fraction = (timestamp - before_time) / max(
                1e-9, after_time - before_time
            )
            yaw_delta = math.atan2(
                math.sin(after[2] - before[2]),
                math.cos(after[2] - before[2]),
            )
            odom = np.array((
                before[0] + fraction * (after[0] - before[0]),
                before[1] + fraction * (after[1] - before[1]),
                before[2] + fraction * yaw_delta,
            ))

        dx, dy = odom[0] - reference[0], odom[1] - reference[1]
        local_x = c_ref * dx + s_ref * dy
        local_y = -s_ref * dx + c_ref * dy
        yaw_delta = odom[2] - reference_yaw
        c, s = math.cos(yaw_delta), math.sin(yaw_delta)
        point = points[index]
        deskewed[index] = (
            local_x + c * point[0] - s * point[1],
            local_y + s * point[0] + c * point[1],
        )
    return deskewed


class LidarMapper(Node):
    """Accumulate full revolutions, align them against the map, and map rays."""

    def __init__(self):
        super().__init__('neuravac_slam')
        self.declare_parameter('resolution_m', 0.05)
        self.declare_parameter('map_size_m', 20.0)
        self.declare_parameter('min_range_m', 0.12)
        self.declare_parameter('max_range_m', 8.0)
        self.declare_parameter('max_neighbor_gap_m', 0.35)
        self.declare_parameter('hit_increment', 5)
        self.declare_parameter('miss_decrement', 4)
        self.declare_parameter('occupied_threshold', 6)
        self.declare_parameter('scan_match_window_m', 0.20)
        self.declare_parameter('scan_match_window_deg', 12.0)
        self.declare_parameter('scan_match_fallback_window_deg', 24.0)
        self.declare_parameter('scan_match_fallback_steps', 13)
        self.declare_parameter('scan_match_correction_weight', 0.35)
        self.declare_parameter('scan_match_max_translation_correction_m', 0.10)
        self.declare_parameter('scan_match_max_rotation_correction_deg', 10.0)
        self.declare_parameter('odom_stale_sec', 1.5)
        self.declare_parameter('odom_history_sec', 3.0)
        self.declare_parameter('active_return_sec', 2.0)
        self.declare_parameter('map_publish_hz', 2.0)
        value = lambda name: self.get_parameter(name).value
        self.resolution = float(value('resolution_m'))
        self.size = max(100, int(float(value('map_size_m')) / self.resolution))
        self.origin = -(self.size * self.resolution) / 2.0
        self.min_range = float(value('min_range_m'))
        self.max_range = float(value('max_range_m'))
        self.max_neighbor_gap = max(0.0, float(value('max_neighbor_gap_m')))
        self.hit_increment = max(1, int(value('hit_increment')))
        self.miss_decrement = max(1, int(value('miss_decrement')))
        self.occupied_threshold = max(1, int(value('occupied_threshold')))
        self.match_window = float(value('scan_match_window_m'))
        self.match_angle = math.radians(float(value('scan_match_window_deg')))
        self.fallback_match_angle = math.radians(
            float(value('scan_match_fallback_window_deg'))
        )
        self.fallback_match_steps = max(9, int(value('scan_match_fallback_steps')))
        self.match_correction_weight = min(
            1.0, max(0.0, float(value('scan_match_correction_weight')))
        )
        self.match_max_translation = max(
            0.0, float(value('scan_match_max_translation_correction_m'))
        )
        self.match_max_rotation = math.radians(
            max(0.0, float(value('scan_match_max_rotation_correction_deg')))
        )
        self.odom_stale_sec = max(0.1, float(value('odom_stale_sec')))
        self.odom_history_sec = max(0.5, float(value('odom_history_sec')))
        self.active_return_sec = max(0.1, float(value('active_return_sec')))
        self.grid = np.zeros((self.size, self.size), dtype=np.int8)
        self._last_hit = np.zeros((self.size, self.size), dtype=np.float64)
        self._scan = []
        self._last_angle = None
        self._last_scan = None
        self._pose = np.zeros(3, dtype=np.float64)
        self._odom_pose = None
        self._odom_received_at = None
        self._odom_at_last_scan = None
        self._odom_history = deque(maxlen=400)
        self._lock = threading.Lock()
        self._odom_lock = threading.Lock()
        self._scan_queue = queue.Queue(maxsize=1)
        self._stop_worker = threading.Event()
        self._reset_generation = 0
        self._scan_worker_thread = threading.Thread(
            target=self._scan_worker, name='slam-scan-worker', daemon=True
        )
        self._scan_worker_thread.start()
        self._map_version = 0
        self._published_version = -1
        self.create_subscription(LidarPoint, 'lidar_points', self.on_point, 1000)
        self.create_subscription(Odometry, 'odom', self.on_odometry, 10)
        self.map_pub = self.create_publisher(OccupancyGrid, 'slam/map', 1)
        self.pose_pub = self.create_publisher(PoseStamped, 'slam/pose', 10)
        self.create_service(Trigger, 'slam/reset', self.reset_map)
        self.create_timer(1.0 / max(0.2, float(value('map_publish_hz'))), self.publish_map)
        self._publish_pose()
        self.get_logger().info(
            f'LiDAR-only SLAM ready: {self.size}x{self.size}, '
            f'{self.resolution:.2f} m/cell; wheel odometry is a scan-matching prior'
        )

    def reset_map(self, _request, response):
        """Clear accumulated state; subsequent scans build a fresh map."""
        with self._lock:
            self._reset_generation += 1
            self.grid.fill(0)
            self._last_hit.fill(0.0)
            self._scan.clear()
            self._last_angle = None
            self._last_scan = None
            self._pose.fill(0.0)
            with self._odom_lock:
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
        pose = np.array((
            message.pose.pose.position.x,
            message.pose.pose.position.y,
            yaw,
        ), dtype=np.float64)
        received_at = time.monotonic()
        with self._odom_lock:
            self._odom_pose = pose
            self._odom_received_at = received_at
            self._odom_history.append((received_at, pose.copy()))
            oldest_allowed = received_at - self.odom_history_sec
            while len(self._odom_history) > 2 and self._odom_history[1][0] < oldest_allowed:
                self._odom_history.popleft()

    def _predict_from_odometry(self):
        with self._odom_lock:
            current = (
                self._odom_pose.copy() if self._odom_pose is not None else None
            )
        if current is None:
            return
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
                    self._enqueue_scan(scan)
                else:
                    self._scan.clear()
        self._last_angle = angle
        distance = float(message.distance_mm) / 1000.0
        if self.min_range <= distance <= self.max_range:
            self._scan.append((angle, distance, time.monotonic()))

    def _enqueue_scan(self, scan):
        generation = self._reset_generation
        try:
            self._scan_queue.put_nowait((generation, scan))
        except queue.Full:
            # Never let scan matching build a stale backlog. Keep the newest
            # complete revolution when processing takes longer than a sweep.
            try:
                self._scan_queue.get_nowait()
                self._scan_queue.task_done()
            except queue.Empty:
                pass
            try:
                self._scan_queue.put_nowait((generation, scan))
            except queue.Full:
                self.get_logger().warning('Dropping LiDAR scan; mapper is busy.')

    def _scan_worker(self):
        while not self._stop_worker.is_set():
            try:
                item = self._scan_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                if item is None:
                    return
                generation, scan = item
                self._process_scan(scan, generation)
            except Exception as error:  # Keep the scan consumer alive on bad input.
                self.get_logger().error(f'Unable to process LiDAR scan: {error}')
            finally:
                self._scan_queue.task_done()

    def _local_points(self, scan):
        # Bound CPU while retaining evenly spaced angular coverage.
        if len(scan) > 360:
            take = np.linspace(0, len(scan) - 1, 360).astype(np.int32)
            scan = scan[take]
        points = scan_to_cartesian(scan[:, :2])
        timestamps = scan[:, 2]
        supported = neighbor_support_mask(points, self.max_neighbor_gap)
        return points[supported], timestamps[supported]

    def _deskew_scan(self, points, timestamps):
        """Express each return at its capture pose in the scan reference frame."""
        with self._odom_lock:
            if self._odom_at_last_scan is None or self._odom_received_at is None:
                return points
            reference = self._odom_at_last_scan.copy()
            received_at = self._odom_received_at
            samples = list(self._odom_history)
        if time.monotonic() - received_at > self.odom_stale_sec or len(samples) < 2:
            return points
        return deskew_points_to_reference(points, timestamps, samples, reference)

    def _match_scan(self, points):
        occupied = self.grid >= self.occupied_threshold
        if not occupied.any():
            return self._pose.copy()
        best_pose = self._pose.copy()
        best_score = -1.0
        step = max(self.resolution, self.match_window / 4.0)
        translations = np.arange(-self.match_window, self.match_window + step / 2, step)
        with self._odom_lock:
            received_at = self._odom_received_at
        odom_fresh = (
            received_at is not None
            and time.monotonic() - received_at <= self.odom_stale_sec
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
                    if score > best_score:
                        best_score = score
                        best_pose = np.array((self._pose[0] + dx,
                                              self._pose[1] + dy, theta))
        # If the scan has almost no overlap, do not invent a large correction.
        if best_score < 0.04:
            return self._pose.copy()
        return best_pose

    def _process_scan(self, scan, generation):
        points, timestamps = self._local_points(scan)
        if len(points) < 30:
            return
        with self._lock:
            has_previous_scan = self._last_scan is not None
            if has_previous_scan:
                self._predict_from_odometry()
            else:
                with self._odom_lock:
                    if self._odom_pose is not None:
                        self._odom_at_last_scan = self._odom_pose.copy()
            if generation != self._reset_generation:
                return
            points = self._deskew_scan(points, timestamps)
            if has_previous_scan:
                prior = self._pose.copy()
                matched = self._match_scan(points)
                correction = matched[:2] - prior[:2]
                correction_length = float(np.linalg.norm(correction))
                if correction_length > self.match_max_translation > 0.0:
                    correction *= self.match_max_translation / correction_length
                elif self.match_max_translation == 0.0:
                    correction.fill(0.0)
                yaw_correction = math.atan2(
                    math.sin(matched[2] - prior[2]),
                    math.cos(matched[2] - prior[2]),
                )
                yaw_correction = min(
                    self.match_max_rotation,
                    max(-self.match_max_rotation, yaw_correction),
                )
                weight = self.match_correction_weight
                self._pose[:2] = prior[:2] + correction * weight
                self._pose[2] = math.atan2(
                    math.sin(prior[2] + yaw_correction * weight),
                    math.cos(prior[2] + yaw_correction * weight),
                )
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

    def destroy_node(self):
        self._stop_worker.set()
        try:
            self._scan_queue.put_nowait(None)
        except queue.Full:
            try:
                self._scan_queue.get_nowait()
                self._scan_queue.task_done()
            except queue.Empty:
                pass
            self._scan_queue.put_nowait(None)
        self._scan_worker_thread.join(timeout=2.0)
        super().destroy_node()

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
        # Accumulate repeated hits, but remove stale occupancy quickly when
        # a later ray passes through the old endpoint.
        self.grid[ys[:-1], xs[:-1]] = np.maximum(
            -12,
            self.grid[ys[:-1], xs[:-1]] - self.miss_decrement,
        )
        x, y = int(end_cell[0]), int(end_cell[1])
        if 0 <= x < self.size and 0 <= y < self.size:
            self.grid[y, x] = min(
                20, int(self.grid[y, x]) + self.hit_increment
            )
            self._last_hit[y, x] = time.monotonic()

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
            occupied = self.grid >= self.occupied_threshold
            values[occupied] = np.clip(
                self.grid[occupied].astype(np.int16) * 2 + 40, 50, 82
            ).astype(np.int8)
            active = occupied & (
                (time.monotonic() - self._last_hit) <= self.active_return_sec
            )
            values[active] = 100
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

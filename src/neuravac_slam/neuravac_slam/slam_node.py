"""LiDAR-only 2D mapping with conservative scan acceptance and recovery.

The D6 point message has no timestamp, and the Roomba integration publishes no
wheel odometry. The mapper therefore cannot predict or deskew motion; all pose
estimates come from bounded scan-to-map search and are treated as uncertain.
"""

import math
import queue
import threading

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from std_msgs.msg import String
from roomba_interfaces.msg import LidarPoint

from .slam_core import RecoveryGate, polar_to_points, transform_points, wrap_angle


class LidarMapper(Node):
    """Collect revolutions, validate a pose, then update the occupancy grid."""

    def __init__(self):
        super().__init__('neuravac_slam')
        self.declare_parameter('resolution_m', 0.05)
        self.declare_parameter('map_size_m', 20.0)
        self.declare_parameter('min_range_m', 0.12)
        self.declare_parameter('max_range_m', 8.0)
        self.declare_parameter('scan_match_window_m', 0.20)
        self.declare_parameter('scan_match_window_deg', 12.0)
        self.declare_parameter('map_publish_hz', 2.0)
        self.declare_parameter('min_scan_points', 40)
        self.declare_parameter('min_match_score', 0.15)
        self.declare_parameter('recovery_after_rejections', 3)
        self.declare_parameter('recovery_observations', 3)
        self.declare_parameter('recovery_max_scans', 30)
        # D6 angle values increase clockwise; ROS planar coordinates increase CCW.
        self.declare_parameter('lidar_angle_sign', -1.0)
        # Measure these fixed LiDAR-to-base offsets if the sensor is not centered.
        self.declare_parameter('lidar_x_offset_m', 0.0)
        self.declare_parameter('lidar_y_offset_m', 0.0)
        self.declare_parameter('lidar_yaw_offset_deg', 0.0)

        value = lambda name: self.get_parameter(name).value
        self.resolution = float(value('resolution_m'))
        self.size = max(100, int(float(value('map_size_m')) / self.resolution))
        self.origin = -(self.size * self.resolution) / 2.0
        self.min_range = float(value('min_range_m'))
        self.max_range = float(value('max_range_m'))
        self.match_window = float(value('scan_match_window_m'))
        self.match_angle = math.radians(float(value('scan_match_window_deg')))
        self.min_points = min(180, max(30, int(value('min_scan_points'))))
        self.min_match_score = float(value('min_match_score'))
        self.recovery_after = max(1, int(value('recovery_after_rejections')))
        self.recovery_limit = max(1, int(value('recovery_max_scans')))
        self.angle_sign = float(value('lidar_angle_sign'))
        self.lidar_offset = np.array((float(value('lidar_x_offset_m')),
                                      float(value('lidar_y_offset_m')),
                                      math.radians(float(value('lidar_yaw_offset_deg')))))
        self.recovery_gate = RecoveryGate(required=max(2, int(value('recovery_observations'))))

        self.grid = np.zeros((self.size, self.size), dtype=np.int8)
        self._scan = []
        self._last_angle = None
        self._pose = np.zeros(3, dtype=np.float64)  # Last committed pose only.
        self._state = 'TRACKING'
        self._rejections = 0
        self._recovery_scans = 0
        self._scan_id = 0
        self._last_warning_ns = 0
        self._dropped_scans = 0
        self._lock = threading.Lock()
        self._scan_queue = queue.Queue(maxsize=1)
        self._map_version = 0
        self._published_version = -1

        self.create_subscription(LidarPoint, 'lidar_points', self.on_point, 50)
        self.map_pub = self.create_publisher(OccupancyGrid, 'slam/map', 1)
        self.status_pub = self.create_publisher(String, 'slam/status', 10)
        self.create_timer(1.0 / max(0.2, float(value('map_publish_hz'))), self.publish_map)
        self._scan_worker = threading.Thread(target=self._scan_worker_loop, daemon=True)
        self._scan_worker.start()
        self.get_logger().info(
            f'LiDAR-only SLAM ready: {self.size}x{self.size}, '
            f'{self.resolution:.2f} m/cell; no odometry or point timestamps available'
        )

    def on_point(self, message):
        raw_angle = float(message.angle_deg)
        distance = float(message.distance_mm) / 1000.0
        if not math.isfinite(raw_angle) or not math.isfinite(distance):
            return
        angle = math.radians(raw_angle % 360.0)
        if self._last_angle is not None:
            delta = angle - self._last_angle
            # D6 packet point order advances through angle and wraps once per
            # revolution; the wire message has no revolution or time counter.
            if abs(delta) > math.pi:
                self._finish_revolution()
        self._last_angle = angle
        if self.min_range <= distance <= self.max_range:
            self._scan.append((angle, distance))
            # Missing seam packets must not create an unbounded callback buffer.
            if len(self._scan) > 1440:
                self._scan = self._scan[-720:]

    def _finish_revolution(self):
        scan, self._scan = self._scan, []
        if len(scan) >= self.min_points:
            # Keep callbacks short. A size-one queue bounds memory and replaces
            # stale work with the newest full revolution when the worker lags.
            try:
                self._scan_queue.put_nowait(np.asarray(scan, dtype=np.float64))
            except queue.Full:
                try:
                    self._scan_queue.get_nowait()
                    self._scan_queue.task_done()
                except queue.Empty:
                    pass
                self._dropped_scans += 1
                self._scan_queue.put_nowait(np.asarray(scan, dtype=np.float64))

    def _scan_worker_loop(self):
        while True:
            scan = self._scan_queue.get()
            try:
                if scan is None:
                    return
                self._process_scan(scan)
            except Exception as error:  # Keep the sensor callback and worker alive.
                self.get_logger().error(f'SLAM scan processing failed: {error}')
            finally:
                self._scan_queue.task_done()

    def _find_candidate(self, points, recovering):
        """Search a bounded pose neighborhood; report score and ambiguity."""
        occupied = self.grid > 2
        if not occupied.any():
            return self._pose.copy(), 1.0, 1.0

        if recovering:
            window = max(0.75, self.match_window * 3.0)
            angle_window = max(math.radians(45.0), self.match_angle * 3.0)
            # Coarse wide search followed by a small local refinement keeps
            # recovery bounded on the Pi (roughly 750 pose hypotheses).
            coarse_step = window / 3.0
            coarse_angle_step = angle_window / 6.0
            coarse_rotations = np.linspace(-angle_window, angle_window, 13)
            coarse_translations = np.linspace(-window, window, 7)
        else:
            window = self.match_window
            angle_window = self.match_angle
            step = max(self.resolution, window / 4.0)
            rotations = np.linspace(-angle_window, angle_window, 9)
        candidates = []

        def score_pose(theta, dx, dy):
            c, s = math.cos(theta), math.sin(theta)
            rotated_x = c * points[:, 0] - s * points[:, 1]
            rotated_y = s * points[:, 0] + c * points[:, 1]
            ix = np.rint((rotated_x + self._pose[0] + dx - self.origin)
                         / self.resolution).astype(np.int32)
            iy = np.rint((rotated_y + self._pose[1] + dy - self.origin)
                         / self.resolution).astype(np.int32)
            valid = (ix >= 0) & (iy >= 0) & (ix < self.size) & (iy < self.size)
            if np.count_nonzero(valid) < max(20, int(0.7 * len(points))):
                return
            matched = valid & occupied[np.clip(iy, 0, self.size - 1),
                                       np.clip(ix, 0, self.size - 1)]
            supported = np.flatnonzero(matched)
            # A high score concentrated on one short wall is weak evidence.
            # Require support in at least three of eight angular sectors.
            bearings = np.arctan2(points[supported, 1], points[supported, 0])
            sectors = np.unique(
                np.floor((bearings + math.pi) * (8.0 / (2.0 * math.pi))).astype(int) % 8
            )
            if len(sectors) < 3:
                return
            score = float(len(supported)) / len(points)
            pose = np.array((self._pose[0] + dx, self._pose[1] + dy, theta))
            candidates.append((score, pose))

        if recovering:
            for dyaw in coarse_rotations:
                theta = wrap_angle(self._pose[2] + dyaw)
                for dx in coarse_translations:
                    for dy in coarse_translations:
                        score_pose(theta, dx, dy)
            if candidates:
                coarse_pose = max(candidates, key=lambda item: item[0])[1]
                fine_step = max(self.resolution, coarse_step / 2.0)
                fine_angle_step = coarse_angle_step / 2.0
                for dyaw in np.linspace(-fine_angle_step, fine_angle_step, 5):
                    theta = wrap_angle(coarse_pose[2] + dyaw)
                    for dx in np.linspace(coarse_pose[0] - self._pose[0] - coarse_step / 2.0,
                                          coarse_pose[0] - self._pose[0] + coarse_step / 2.0, 5):
                        for dy in np.linspace(coarse_pose[1] - self._pose[1] - coarse_step / 2.0,
                                              coarse_pose[1] - self._pose[1] + coarse_step / 2.0, 5):
                            score_pose(theta, dx, dy)
        else:
            translations = np.arange(-window, window + step * 0.5, step)
            for dyaw in rotations:
                theta = wrap_angle(self._pose[2] + dyaw)
                for dx in translations:
                    for dy in translations:
                        score_pose(theta, dx, dy)
        if not candidates:
            return self._pose.copy(), 0.0, 0.0
        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_pose = candidates[0]
        # Only a spatially distinct alternative counts as ambiguity. Adjacent
        # grid samples represent the same local optimum, not a second solution.
        alternative = next((score for score, pose in candidates[1:]
                            if np.linalg.norm(pose[:2] - best_pose[:2]) > 0.10
                            or abs(wrap_angle(pose[2] - best_pose[2])) > math.radians(5)), 0.0)
        return best_pose, best_score, best_score - alternative

    def _process_scan(self, scan):
        lidar_points = polar_to_points(scan * np.array((self.angle_sign, 1.0)))
        # Convert the sensor cloud into base_link before pose search/map tracing.
        points = transform_points(lidar_points, self.lidar_offset)
        self._scan_id += 1
        if len(points) < self.min_points:
            self._reject('insufficient valid points', len(points), 0.0)
            return

        with self._lock:
            if self._state == 'FAILED':
                self._publish_status('recovery exhausted; mapping paused', len(points), 0.0, 0.0)
                return
            if not np.any(self.grid > 2):
                # The first scan establishes the arbitrary map origin.
                self._accept_scan(points, self._pose.copy())
                self._rejections = 0
                self._state = 'TRACKING'
                self._publish_status('first scan establishes map origin', len(points), 1.0, 1.0)
                return

            recovering = self._state in ('RECOVERING', 'FAILED')
            candidate, score, margin = self._find_candidate(points, recovering)
            required_score = max(self.min_match_score, 0.25 if recovering else 0.0)
            required_margin = 0.04 if recovering else 0.025
            correction = candidate - self._pose
            correction[2] = wrap_angle(correction[2])
            # Search bounds limit normal corrections. Recovery may consider a
            # larger pose, but must pass stronger fit and ambiguity tests.
            credible = score >= required_score and margin >= required_margin
            if not recovering and credible:
                self._accept_scan(points, candidate)
                self._rejections = 0
                self._publish_status('accepted', len(points), score, margin,
                                     candidate=candidate, correction=correction)
                return

            if not recovering:
                self._rejections += 1
                if self._rejections >= self.recovery_after:
                    self._state = 'RECOVERING'
                    self._recovery_scans = 0
                    self.recovery_gate.reset()
                self._publish_status('weak or ambiguous map match', len(points), score, margin,
                                     candidate=candidate, correction=correction)
                return

            self._recovery_scans += 1
            world_cloud = transform_points(points, candidate)
            confirmed = credible and self.recovery_gate.observe(candidate, world_cloud)
            if confirmed:
                self._accept_scan(points, candidate)
                self._state = 'TRACKING'
                self._rejections = 0
                self._recovery_scans = 0
                self.recovery_gate.reset()
                self._publish_status('recovered after independent scan agreement', len(points),
                                     score, margin, candidate=candidate, correction=correction)
                self.get_logger().info('SLAM tracking recovered; pose committed')
                return
            if not credible:
                self.recovery_gate.reset()
            if self._recovery_scans >= self.recovery_limit:
                self._state = 'FAILED'
                self.recovery_gate.reset()
            self._publish_status('recovery pose unconfirmed; map unchanged', len(points),
                                 score, margin, candidate=candidate, correction=correction)

    def _reject(self, reason, point_count, score):
        with self._lock:
            self._rejections += 1
            if self._rejections >= self.recovery_after and self._state == 'TRACKING':
                self._state = 'RECOVERING'
                self._recovery_scans = 0
                self.recovery_gate.reset()
            self._publish_status(reason, point_count, score, 0.0)

    def _accept_scan(self, points, pose):
        """Commit pose and integrate exactly this scan under the same lock."""
        self._pose = np.asarray(pose, dtype=np.float64).copy()
        world = transform_points(points, self._pose)
        scanner = transform_points(self.lidar_offset[None, :2], self._pose)[0]
        for endpoint in world:
            self._trace_ray(scanner, endpoint)
        self._map_version += 1

    def _trace_ray(self, start, end):
        if not np.isfinite(start).all() or not np.isfinite(end).all():
            return
        start_cell = np.rint((start - self.origin) / self.resolution).astype(np.int32)
        end_cell = np.rint((end - self.origin) / self.resolution).astype(np.int32)
        steps = max(abs(int(end_cell[0] - start_cell[0])),
                    abs(int(end_cell[1] - start_cell[1])))
        if steps == 0:
            return
        xs = np.rint(np.linspace(start_cell[0], end_cell[0], steps + 1)).astype(np.int32)
        ys = np.rint(np.linspace(start_cell[1], end_cell[1], steps + 1)).astype(np.int32)
        # Preserve ray order so the last in-map cell is not incorrectly cleared
        # when a return lies beyond the map boundary.
        inside = (xs >= 0) & (ys >= 0) & (xs < self.size) & (ys < self.size)
        indices = np.flatnonzero(inside)
        if not len(indices):
            return
        endpoint_inside = 0 <= end_cell[0] < self.size and 0 <= end_cell[1] < self.size
        free_stop = len(indices) - (1 if endpoint_inside else 0)
        free_indices = indices[:max(0, free_stop)]
        if len(free_indices):
            self.grid[ys[free_indices], xs[free_indices]] = np.maximum(
                -8, self.grid[ys[free_indices], xs[free_indices]] - 1)
        if endpoint_inside:
            self.grid[end_cell[1], end_cell[0]] = min(
                16, int(self.grid[end_cell[1], end_cell[0]]) + 3)

    def _publish_status(self, reason, point_count, score, margin,
                        candidate=None, correction=None):
        candidate = self._pose if candidate is None else candidate
        correction = np.zeros(3) if correction is None else correction
        msg = String()
        msg.data = (
            f'state={self._state}; odometry_fresh=false; points={point_count}; '
            f'match_score={score:.3f}; ambiguity_margin={margin:.3f}; '
            f'predicted_pose=unavailable; candidate=({candidate[0]:.3f},'
            f'{candidate[1]:.3f},{candidate[2]:.3f}); '
            f'accepted=({self._pose[0]:.3f},{self._pose[1]:.3f},{self._pose[2]:.3f}); '
            f'correction=({correction[0]:.3f},{correction[1]:.3f},'
            f'{math.degrees(correction[2]):.1f}deg); '
            f'recovery_observations={self.recovery_gate.count}; '
            f'dropped_scans={self._dropped_scans}; motion_compensation=false; '
            f'reason={reason}'
        )
        self.status_pub.publish(msg)
        now_ns = self.get_clock().now().nanoseconds
        if reason != 'accepted' and now_ns - self._last_warning_ns >= 2_000_000_000:
            self._last_warning_ns = now_ns
            self.get_logger().warning(f'SLAM scan {self._scan_id}: {msg.data}')

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

    def destroy_node(self):
        try:
            self._scan_queue.put_nowait(None)
        except queue.Full:
            try:
                self._scan_queue.get_nowait()
                self._scan_queue.task_done()
            except queue.Empty:
                pass
            self._scan_queue.put_nowait(None)
        self._scan_worker.join(timeout=2.0)
        return super().destroy_node()


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

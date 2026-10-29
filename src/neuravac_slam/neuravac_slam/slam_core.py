"""ROS-independent geometry and recovery checks for the LiDAR mapper."""

import math

import numpy as np


def wrap_angle(angle):
    """Return an angle in [-pi, pi), including across the +/-pi seam."""
    return (float(angle) + math.pi) % (2.0 * math.pi) - math.pi


def polar_to_points(scan, max_points=180):
    """Convert finite (angle_rad, range_m) rows to a bounded local cloud."""
    scan = np.asarray(scan, dtype=np.float64)
    if scan.ndim != 2 or scan.shape[1] != 2:
        return np.empty((0, 2), dtype=np.float64)
    valid = np.isfinite(scan).all(axis=1) & (scan[:, 1] > 0.0)
    scan = scan[valid]
    if len(scan) > max_points:
        indexes = np.linspace(0, len(scan) - 1, max_points).astype(np.int32)
        scan = scan[indexes]
    return np.column_stack((scan[:, 1] * np.cos(scan[:, 0]),
                            scan[:, 1] * np.sin(scan[:, 0])))


def transform_points(points, pose):
    """Apply the local-to-map planar rigid transform to an Nx2 point array."""
    points = np.asarray(points, dtype=np.float64)
    pose = np.asarray(pose, dtype=np.float64)
    c, s = math.cos(pose[2]), math.sin(pose[2])
    rotation = np.array(((c, -s), (s, c)))
    return points @ rotation.T + pose[:2]


def cloud_overlap(first, second, tolerance=0.15):
    """Fraction of first-cloud endpoints supported by a second cloud."""
    if len(first) < 12 or len(second) < 12:
        return 0.0
    # Bound the recovery-only pairwise check to 100x100 distances.
    a = first[np.linspace(0, len(first) - 1, min(100, len(first))).astype(int)]
    b = second[np.linspace(0, len(second) - 1, min(100, len(second))).astype(int)]
    delta = a[:, None, :] - b[None, :, :]
    nearest_sq = np.min(np.einsum('ijk,ijk->ij', delta, delta), axis=1)
    return float(np.count_nonzero(nearest_sq <= tolerance * tolerance)) / len(a)


class RecoveryGate:
    """Require repeatable map poses and independent scan-to-scan support."""

    def __init__(self, required=3, position_tolerance=0.12,
                 angle_tolerance=math.radians(6.0), min_overlap=0.18):
        self.required = required
        self.position_tolerance = position_tolerance
        self.angle_tolerance = angle_tolerance
        self.min_overlap = min_overlap
        self.reset()

    def reset(self):
        self.count = 0
        self._pose = None
        self._cloud = None

    def observe(self, pose, world_cloud):
        pose = np.asarray(pose, dtype=np.float64).copy()
        cloud = np.asarray(world_cloud, dtype=np.float64).copy()
        if self._pose is not None:
            position_delta = float(np.linalg.norm(pose[:2] - self._pose[:2]))
            angle_delta = abs(wrap_angle(pose[2] - self._pose[2]))
            overlap = cloud_overlap(cloud, self._cloud)
            if (position_delta > self.position_tolerance
                    or angle_delta > self.angle_tolerance
                    or overlap < self.min_overlap):
                self.count = 0
                self._pose = None
                self._cloud = None
        self.count += 1
        self._pose = pose
        self._cloud = cloud
        return self.count >= self.required

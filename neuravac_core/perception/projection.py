"""Intersect calibrated optical rays with robot z=0, then transform to map."""

import math

import numpy as np

from neuravac_core.models import Detection, Pose


class FloorProjector:
    def __init__(
        self, intrinsics, camera_to_robot, image_size: tuple[int, int], max_distance_m: float = 5
    ):
        k = np.asarray(intrinsics, dtype=float)
        transform = np.asarray(camera_to_robot, dtype=float)
        if (
            k.shape != (3, 3)
            or transform.shape != (4, 4)
            or not np.isfinite(k).all()
            or not np.isfinite(transform).all()
        ):
            raise ValueError("Finite 3x3 intrinsics and 4x4 extrinsics required")
        if k[0, 0] <= 0 or k[1, 1] <= 0 or not np.allclose(k[2], [0, 0, 1]):
            raise ValueError("Invalid camera intrinsics")
        rotation = transform[:3, :3]
        if (
            not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6)
            or not np.isclose(np.linalg.det(rotation), 1)
            or not np.allclose(transform[3], [0, 0, 0, 1])
        ):
            raise ValueError("Extrinsics must be a rigid camera-to-robot transform")
        if (
            transform[2, 3] <= 0
            or len(image_size) != 2
            or min(image_size) <= 0
            or not math.isfinite(max_distance_m)
            or max_distance_m <= 0
        ):
            raise ValueError("Positive camera height, image dimensions and range required")
        self.inverse_k, self.transform = np.linalg.inv(k), transform
        self.image_size, self.max_distance_m = image_size, max_distance_m

    def project_pixel(
        self, u: float, v: float, robot_pose: Pose | None = None
    ) -> tuple[float, float] | None:
        width, height = self.image_size
        if (
            not math.isfinite(u)
            or not math.isfinite(v)
            or not 0 <= u < width
            or not 0 <= v < height
        ):
            return None
        direction = self.transform[:3, :3] @ self.inverse_k @ np.array([u, v, 1])
        origin = self.transform[:3, 3]
        if direction[2] >= -1e-8:
            return None
        point = origin + (-origin[2] / direction[2]) * direction
        if point[0] <= 0 or np.linalg.norm(point[:2]) > self.max_distance_m:
            return None
        pose = robot_pose or Pose()
        c, s = math.cos(pose.yaw), math.sin(pose.yaw)
        return (pose.x + c * point[0] - s * point[1], pose.y + s * point[0] + c * point[1])

    def project_detection(
        self, detection: Detection, robot_pose: Pose | None = None
    ) -> Detection | None:
        if detection.bbox is None:
            return None
        x1, _, x2, y2 = detection.bbox
        point = self.project_pixel((x1 + x2) / 2, y2, robot_pose)
        if point is None:
            return None
        return detection.model_copy(update={"position": point}, deep=True)

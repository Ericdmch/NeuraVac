"""Dependency-light ROS transport contracts. All envelope stamps are ROS seconds."""

import json
import math

from neuravac_core.models import CleaningRegion, SemanticObject
from neuravac_core.world import WorldModel


def envelope(kind, stamp, payload):
    if type(stamp) not in (float, int) or not math.isfinite(stamp) or stamp < 0:
        raise ValueError("invalid ROS stamp")
    return json.dumps(
        {"schema_version": 1, "kind": kind, "stamp": stamp, "frame_id": "map", "payload": payload},
        allow_nan=False,
        separators=(",", ":"),
    )


def decode(raw, kind, now, max_age):
    def unique(pairs):
        output = {}
        for key, value in pairs:
            if key in output:
                raise ValueError("duplicate JSON key")
            output[key] = value
        return output

    if len(raw) > 2_000_000:
        raise ValueError("envelope exceeds limit")
    data = json.loads(
        raw,
        object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
    )
    json.dumps(data, allow_nan=False)
    if (
        not isinstance(data, dict)
        or set(data) != {"schema_version", "kind", "stamp", "frame_id", "payload"}
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
        or data["kind"] != kind
        or data["frame_id"] != "map"
        or type(data["stamp"]) not in (float, int)
        or not math.isfinite(data["stamp"])
        or not 0 <= now - data["stamp"] <= max_age
        or not isinstance(data["payload"], dict)
    ):
        raise ValueError("invalid/stale envelope")
    return data


def restore_world(payload, config):
    if (
        set(payload) != {"schema_version", "revision", "objects", "regions", "recent_changes"}
        or payload["schema_version"] != 1
    ):
        raise ValueError("invalid world snapshot")
    if type(payload["revision"]) is not int or payload["revision"] < 0:
        raise ValueError("invalid revision")
    world = WorldModel(config)
    world.objects = {
        o.id: o for item in payload["objects"] if (o := SemanticObject.model_validate(item))
    }
    world.regions = {
        r.id: r for item in payload["regions"] if (r := CleaningRegion.model_validate(item))
    }
    if len(world.objects) != len(payload["objects"]) or len(world.regions) != len(
        payload["regions"]
    ):
        raise ValueError("duplicate IDs")
    if any(
        oid not in world.objects and r.reachable
        for r in world.regions.values()
        for oid in r.object_ids
    ):
        raise ValueError("dangling region object")
    world.revision = int(payload["revision"])
    world.recent_changes = payload["recent_changes"][-100:]
    return world


def keepout_cells(world, width, height, resolution, origin):
    if not (0 < width * height <= 4_000_000 and resolution > 0):
        raise ValueError("invalid occupancy geometry")
    cells = [0] * (width * height)
    margin = world.config.robot_radius_m + world.config.semantic.hazard_expansion_m
    for hazard in world.hazards:
        radius = margin + max((math.dist(hazard.position, p) for p in hazard.polygon), default=0)
        x, y = hazard.position
        for row in range(
            max(0, int((y - radius - origin[1]) / resolution)),
            min(height, math.ceil((y + radius - origin[1]) / resolution) + 1),
        ):
            for col in range(
                max(0, int((x - radius - origin[0]) / resolution)),
                min(width, math.ceil((x + radius - origin[0]) / resolution) + 1),
            ):
                if math.dist(
                    (origin[0] + (col + 0.5) * resolution, origin[1] + (row + 0.5) * resolution),
                    (x, y),
                ) <= radius + resolution / math.sqrt(2):
                    cells[row * width + col] = 100
    return cells


def project_observations(detections, projector, pose):
    """Even an empty inference result requires calibrated image-time map localization."""
    if projector is None or pose is None:
        raise ValueError("calibration and image-time map TF required")
    width, height = projector.image_size
    projected = []
    for detection in detections:
        if detection.bbox is None:
            raise ValueError("detector bbox required")
        x1, y1, x2, y2 = detection.bbox

        def pixel(u, v):
            return projector.project_pixel(min(u, width - 1), min(v, height - 1), pose)

        point = pixel((x1 + x2) / 2, y2)
        if point is None:
            raise ValueError("floor projection failed")
        update = {"position": point}
        if detection.class_name == "clean_floor":
            polygon = [pixel(u, v) for u, v in ((x1, y1), (x2, y1), (x2, y2), (x1, y2))]
            if any(p is None for p in polygon):
                raise ValueError("clean-floor polygon crosses projection horizon")
            update["polygon"] = polygon
        projected.append(detection.model_copy(update=update))
    return projected

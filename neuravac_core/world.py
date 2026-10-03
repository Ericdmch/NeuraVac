"""Authoritative semantic tracking, debris clustering and decision validation."""

import math
from collections.abc import Callable

from neuravac_core.config import RobotConfig
from neuravac_core.models import CleaningRegion, Decision, Detection, Pose, SemanticObject


class WorldModel:
    def __init__(self, config: RobotConfig) -> None:
        self.config = config
        self.objects: dict[str, SemanticObject] = {}
        self.regions: dict[str, CleaningRegion] = {}
        self.revision = 0
        self.recent_changes: list[dict] = []
        self._next_id = 1
        self._observed_at: dict[str, float] = {}

    def observe(self, detections: list[Detection], now: float) -> None:
        assigned = set()
        for detection in detections:
            if (
                detection.position is None
                or not 0 <= now - detection.timestamp <= self.config.safety.camera_timeout_s
            ):
                continue
            position = detection.position
            candidates = [
                o
                for o in self.objects.values()
                if o.class_name == detection.class_name
                and o.id not in assigned
                and math.dist(o.position, detection.position)
                <= self.config.semantic.association_radius_m
            ]
            obj = (
                min(candidates, key=lambda o: math.dist(o.position, position))
                if candidates
                else None
            )
            vacuumable = (
                detection.class_name == "debris"
                and detection.confidence >= self.config.semantic.min_confidence
            )
            traversable = (
                detection.class_name in ("debris", "clean_floor")
                and detection.confidence >= self.config.semantic.min_confidence
            )
            if obj:
                old = obj.position
                obj.position = detection.position
                obj.confidence = max(obj.confidence, detection.confidence)
                obj.last_seen = detection.timestamp
                obj.debris_score = detection.debris_score
                obj.polygon = detection.polygon
                obj.vacuumable = vacuumable
                obj.traversable = traversable
                obj.hazard_score = 0 if traversable else 1
                if math.dist(old, obj.position) > 0.05:
                    self._change("moved", obj.id, now)
            else:
                object_id = f"o{self._next_id}"
                self._next_id += 1
                obj = SemanticObject(
                    id=object_id,
                    class_name=detection.class_name,
                    confidence=detection.confidence,
                    position=detection.position,
                    polygon=detection.polygon,
                    first_seen=detection.timestamp,
                    last_seen=detection.timestamp,
                    source=detection.source,
                    traversable=traversable,
                    vacuumable=vacuumable,
                    hazard_score=0 if traversable else 1,
                    debris_score=detection.debris_score,
                )
                self.objects[obj.id] = obj
                self._change("appeared", obj.id, now)
            assigned.add(obj.id)
        clear_floor = [
            d
            for d in detections
            if d.class_name == "clean_floor"
            and d.confidence >= self.config.semantic.min_confidence
            and len(d.polygon) >= 3
            and 0 <= now - d.timestamp <= self.config.safety.camera_timeout_s
        ]
        for obj in self.objects.values():
            if (
                obj.class_name != "debris"
                or obj.id in assigned
                or not self.safe_point(obj.position)
            ):
                continue
            for floor in clear_floor:
                points = obj.polygon or [obj.position]
                if all(point_in_polygon(point, floor.polygon) for point in points):
                    obj.debris_score = 0
                    obj.last_seen = floor.timestamp
                    obj.source = floor.source + ":explicit_clear_floor"
                    self._change("verified_clear_floor", obj.id, now)
                    break
        self.expire(now)
        self._cluster()

    def _change(self, change: str, object_id: str, now: float) -> None:
        self.revision += 1
        self.recent_changes.append({"change": change, "id": object_id, "timestamp": now})
        self.recent_changes = self.recent_changes[-100:]

    def expire(self, now: float) -> None:
        for object_id, obj in list(self.objects.items()):
            if now - obj.last_seen > self.config.semantic.stale_after_s:
                del self.objects[object_id]
                self._change("expired", object_id, now)
        self._cluster()

    @property
    def hazards(self) -> list[SemanticObject]:
        return [o for o in self.objects.values() if not o.traversable]

    def safe_point(self, point: tuple[float, float]) -> bool:
        margin = self.config.robot_radius_m + self.config.semantic.hazard_expansion_m
        for hazard in self.hazards:
            extent = max((math.dist(hazard.position, p) for p in hazard.polygon), default=0)
            if math.dist(point, hazard.position) <= margin + extent:
                return False
        return True

    def _cluster(self) -> None:
        remaining = {o.id: o for o in self.objects.values() if o.vacuumable}
        active = {}
        while remaining:
            object_id = min(remaining)
            group = [remaining.pop(object_id)]
            changed = True
            while changed:
                changed = False
                for candidate, obj in list(remaining.items()):
                    if any(
                        math.dist(obj.position, member.position)
                        <= self.config.cleaning.cluster_radius_m
                        for member in group
                    ):
                        group.append(remaining.pop(candidate))
                        changed = True
            ids = sorted(o.id for o in group)
            region_id = "d-" + ids[0]
            center = (
                sum(o.position[0] for o in group) / len(group),
                sum(o.position[1] for o in group) / len(group),
            )
            score = sum(o.debris_score for o in group)
            previous = self.regions.get(region_id)
            if previous is None:
                historical = [
                    r
                    for r in self.regions.values()
                    if r.id not in active
                    and math.dist(r.position, center) <= self.config.cleaning.cluster_radius_m
                ]
                if historical:
                    previous = min(historical, key=lambda r: math.dist(r.position, center))
                    region_id = previous.id
            radius = self.config.cleaning.vacuum_radius_m
            active[region_id] = CleaningRegion(
                id=region_id,
                position=center,
                object_ids=ids,
                debris_score=score,
                polygon=[
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius),
                    (center[0] - radius, center[1] + radius),
                ],
                confidence=min(o.confidence for o in group),
                density=score / (math.pi * radius**2),
                reachable=self.safe_point(center),
                cleaned=previous.cleaned if previous else False,
                failures=previous.failures if previous else 0,
            )
            if score > self.config.cleaning.success_threshold:
                active[region_id].cleaned = False
        for region_id, previous in self.regions.items():
            if region_id not in active:
                # Object TTL is a tracking concern, not evidence that dirt disappeared.
                previous.reachable = False
                active[region_id] = previous
        self.regions = active

    def score(self, region_id: str, observation_time: float) -> float:
        region = self.regions.get(region_id)
        if region is None:
            raise ValueError("target disappeared; inspection required")
        if any(
            oid not in self.objects or self.objects[oid].last_seen < observation_time - 0.02
            for oid in region.object_ids
        ):
            raise ValueError(
                "cleaning verification requires fresh observations of every target object"
            )
        return region.debris_score

    def choose(
        self,
        pose: Pose,
        reachable: Callable[[tuple[float, float]], bool] | None = None,
        battery_percent: float = 100,
    ) -> CleaningRegion | None:
        candidates = []
        for region in self.regions.values():
            if region.cleaned or region.debris_score <= self.config.cleaning.success_threshold:
                continue
            region.reachable = (
                all(oid in self.objects for oid in region.object_ids)
                and self.safe_point(region.position)
                and (reachable(region.position) if reachable else True)
            )
            if not region.reachable:
                continue
            weights = self.config.planning
            distance = math.dist((pose.x, pose.y), region.position)
            battery_cost = distance * (100 - battery_percent) / max(1, battery_percent)
            region.priority = (
                weights.amount_weight
                * region.debris_score
                * region.confidence**weights.confidence_weight
                / (
                    1
                    + weights.distance_weight * distance
                    + weights.failure_weight * region.failures
                    + weights.battery_cost_weight * battery_cost
                )
            )
            candidates.append(region)
        return max(candidates, key=lambda r: r.priority) if candidates else None

    def validate_decision(self, decision: Decision, now: float) -> Decision:
        if decision.action in ("clean_region", "inspect_region"):
            region = self.regions.get(decision.target_id or "")
            if (
                region is None
                or region.cleaned
                or not region.reachable
                or not self.safe_point(region.position)
            ):
                raise ValueError("AI selected missing, cleaned, unreachable or prohibited target")
            if any(
                oid not in self.objects
                or now - self.objects[oid].last_seen > self.config.safety.camera_timeout_s
                for oid in region.object_ids
            ):
                raise ValueError("AI selected stale target")
        if decision.action == "finish" and any(
            not r.cleaned and r.debris_score > self.config.cleaning.success_threshold
            for r in self.regions.values()
        ):
            raise ValueError("cannot finish while unresolved debris remains")
        return decision

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "revision": self.revision,
            "objects": [o.model_dump(mode="json") for o in self.objects.values()],
            "regions": [r.model_dump(mode="json") for r in self.regions.values()],
            "recent_changes": self.recent_changes,
        }

    def reasoning_state(self, battery_percent: float) -> dict:
        return {
            "mission": "clean the room without disturbing belongings",
            "battery_percent": battery_percent,
            "dirty_regions": [
                r.model_dump(mode="json")
                for r in self.regions.values()
                if not r.cleaned and r.debris_score > self.config.cleaning.success_threshold
            ],
            "hazards": [
                {
                    "id": h.id,
                    "type": h.class_name,
                    "position": list(h.position),
                    "confidence": h.confidence,
                }
                for h in self.hazards
            ],
            "recent_changes": self.recent_changes[-10:],
        }


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    inside = False
    x, y = point
    for index, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[(index + 1) % len(polygon)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside

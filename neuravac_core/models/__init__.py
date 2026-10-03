"""Versioned, finite, strict application data contracts (map coordinates in metres)."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_assignment=True)


class Pose(StrictModel):
    x: float = 0.0
    y: float = 0.0
    yaw: float = 0.0


class BatteryState(StrictModel):
    percent: float = Field(default=100.0, ge=0, le=100)
    voltage: float = Field(default=14.4, ge=0)
    current: float = 0.0
    charging: bool = False


class BumperState(StrictModel):
    left: bool = False
    right: bool = False
    wheel_drop: bool = False


class CliffState(StrictModel):
    left: bool = False
    front_left: bool = False
    front_right: bool = False
    right: bool = False

    @property
    def detected(self) -> bool:
        return any((self.left, self.front_left, self.front_right, self.right))


class EncoderState(StrictModel):
    left: int = 0
    right: int = 0
    supported: bool = True


FloorClass = Literal[
    "clean_floor",
    "debris",
    "cable",
    "clothing",
    "paper",
    "liquid",
    "shoe",
    "large_object",
    "unknown",
]


class Detection(StrictModel):
    class_name: FloorClass
    confidence: float = Field(ge=0, le=1)
    timestamp: float = Field(ge=0)
    source: str
    bbox: tuple[float, float, float, float] | None = None
    position: tuple[float, float] | None = None
    polygon: list[tuple[float, float]] = Field(default_factory=list)
    debris_score: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def valid_bbox(self) -> "Detection":
        if self.bbox and (self.bbox[2] <= self.bbox[0] or self.bbox[3] <= self.bbox[1]):
            raise ValueError("bbox must have positive width and height")
        return self


class SemanticObject(StrictModel):
    id: str
    class_name: FloorClass
    confidence: float = Field(ge=0, le=1)
    position: tuple[float, float]
    polygon: list[tuple[float, float]] = Field(default_factory=list)
    first_seen: float
    last_seen: float
    source: str
    traversable: bool
    vacuumable: bool
    hazard_score: float = Field(ge=0, le=1)
    debris_score: float = Field(default=0, ge=0)


class CleaningRegion(StrictModel):
    id: str
    position: tuple[float, float]
    polygon: list[tuple[float, float]] = Field(default_factory=list)
    object_ids: list[str] = Field(default_factory=list)
    debris_score: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    density: float = Field(default=0, ge=0)
    priority: float = 0
    reachable: bool = True
    cleaned: bool = False
    failures: int = Field(default=0, ge=0)


Action = Literal[
    "clean_region",
    "inspect_region",
    "rescan_area",
    "return_home",
    "pause",
    "request_human_help",
    "finish",
]


class Decision(StrictModel):
    action: Action
    target_id: str | None = None
    priority: float = Field(default=0, ge=0, le=1)
    reason: str = Field(min_length=1, max_length=500)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def require_target(self) -> "Decision":
        if self.action in ("clean_region", "inspect_region") and not self.target_id:
            raise ValueError("region action requires target_id")
        return self


class MissionState(StrEnum):
    BOOTING = "BOOTING"
    SELF_TEST = "SELF_TEST"
    IDLE = "IDLE"
    MAPPING = "MAPPING"
    SCANNING = "SCANNING"
    PLANNING = "PLANNING"
    NAVIGATING = "NAVIGATING"
    CLEANING = "CLEANING"
    VERIFYING = "VERIFYING"
    RETRYING = "RETRYING"
    REPLANNING = "REPLANNING"
    RETURNING_HOME = "RETURNING_HOME"
    PAUSED = "PAUSED"
    FAULT = "FAULT"
    COMPLETE = "COMPLETE"

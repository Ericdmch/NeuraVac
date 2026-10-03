"""Seeded CI environment: circles, conservative footprints, and observable debris."""

import math
import random
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import Field

from neuravac_core.models import Detection, FloorClass, Pose, StrictModel


@dataclass
class Obstacle:
    id: str
    x: float
    y: float
    radius: float
    class_name: FloorClass = "large_object"


@dataclass
class Dirt:
    id: str
    x: float
    y: float
    score: float = 1
    removal_rate: float = 0.72


@dataclass
class Environment:
    width: float = 6
    height: float = 4
    start: Pose = field(default_factory=lambda: Pose(x=0.6, y=0.6))
    obstacles: list[Obstacle] = field(default_factory=list)
    dirt: list[Dirt] = field(default_factory=list)
    revision: int = 0

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Environment":
        scenario = Scenario.model_validate(yaml.safe_load(Path(path).read_text()))
        env = cls(
            width=scenario.room.width,
            height=scenario.room.height,
            start=scenario.robot_start,
            obstacles=scenario.obstacles,
            dirt=scenario.debris,
        )
        if not env.free(env.start.x, env.start.y, 0.17):
            raise ValueError("robot start overlaps a wall or obstacle")
        if any(
            not 0 <= d.x <= env.width
            or not 0 <= d.y <= env.height
            or d.score < 0
            or d.removal_rate < 0
            for d in env.dirt
        ):
            raise ValueError("invalid debris geometry/score")
        if any(
            o.radius <= 0 or not 0 <= o.x <= env.width or not 0 <= o.y <= env.height
            for o in env.obstacles
        ):
            raise ValueError("invalid obstacle geometry")
        return env

    @classmethod
    def demo(cls) -> "Environment":
        return cls(
            obstacles=[Obstacle("cable", 3, 1.6, 0.3, "cable"), Obstacle("chair", 4.1, 1.4, 0.3)],
            dirt=[Dirt("A", 1.6, 1), Dirt("B", 4.7, 2.8)],
        )

    def free(self, x: float, y: float, radius: float) -> bool:
        return (
            radius <= x <= self.width - radius
            and radius <= y <= self.height - radius
            and all(math.hypot(x - o.x, y - o.y) > radius + o.radius + 0.05 for o in self.obstacles)
        )

    def move_obstacle(self, object_id: str, x: float, y: float) -> None:
        obstacle = next(o for o in self.obstacles if o.id == object_id)
        obstacle.x, obstacle.y = x, y
        self.revision += 1

    def observe(self, now: float) -> list[Detection]:
        # Labeled sensor emulator, not an inference model. Includes zero-score observations.
        result = [
            Detection(
                class_name="debris",
                confidence=0.95,
                timestamp=now,
                source="simulated_camera",
                position=(d.x, d.y),
                debris_score=d.score,
            )
            for d in self.dirt
        ]
        result += [
            Detection(
                class_name=o.class_name,
                confidence=0.98,
                timestamp=now,
                source="simulated_camera",
                position=(o.x, o.y),
                polygon=[
                    (o.x - o.radius, o.y - o.radius),
                    (o.x + o.radius, o.y - o.radius),
                    (o.x + o.radius, o.y + o.radius),
                    (o.x - o.radius, o.y + o.radius),
                ],
            )
            for o in self.obstacles
        ]
        return result

    def clean(self, pose: Pose, radius: float, dt: float) -> None:
        for dirt in self.dirt:
            if math.hypot(pose.x - dirt.x, pose.y - dirt.y) <= radius:
                dirt.score = max(0, dirt.score - dirt.removal_rate * dt)

    def lidar(
        self, pose: Pose, seed: int = 0, beams: int = 72, noise_std: float = 0.005
    ) -> list[float]:
        randomizer = random.Random(seed)
        readings = []
        for i in range(beams):
            angle = pose.yaw + i * 2 * math.pi / beams
            distance = 0.05
            while distance < 8:
                if not self.free(
                    pose.x + distance * math.cos(angle), pose.y + distance * math.sin(angle), 0
                ):
                    break
                distance += 0.05
            readings.append(max(0.05, distance + randomizer.gauss(0, noise_std)))
        return readings


class Room(StrictModel):
    width: float = Field(gt=0, le=100)
    height: float = Field(gt=0, le=100)


class Scenario(StrictModel):
    seed: int = 42
    room: Room
    robot_start: Pose
    obstacles: list[Obstacle] = Field(default_factory=list)
    debris: list[Dirt] = Field(default_factory=list)
    move_chair_after_first_target: bool = True

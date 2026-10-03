"""Redacted versioned JSONL; replay never constructs an actuator backend."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import Field

from neuravac_core.config import RobotConfig
from neuravac_core.models import Detection, StrictModel
from neuravac_core.utils.logging import redact
from neuravac_core.world import WorldModel


class RecordedEvent(StrictModel):
    version: int = 1
    event: str
    timestamp: float = Field(ge=0)
    data: dict


def _json(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


class SessionRecorder:
    def __init__(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.stream = Path(path).open("w")
        self.last_timestamp = -1.0

    def write(self, event: str, timestamp: float, data: dict) -> None:
        if timestamp < self.last_timestamp:
            raise ValueError("recording timestamps must be monotonic")
        self.last_timestamp = timestamp
        envelope = {"version": 1, "event": event, "timestamp": timestamp, "data": redact(data)}
        self.stream.write(json.dumps(envelope, default=_json, allow_nan=False) + "\n")
        self.stream.flush()

    def close(self) -> None:
        self.stream.close()


def replay_events(path: str | Path) -> Iterator[dict]:
    previous = -1.0
    with Path(path).open() as stream:
        for line_number, line in enumerate(stream, 1):
            if len(line) > 8_000_000:
                raise ValueError("record line too large")
            try:
                event = RecordedEvent.model_validate_json(line)
            except ValueError as error:
                raise ValueError(f"invalid replay event at line {line_number}") from error
            if event.version != 1 or event.timestamp < previous:
                raise ValueError("unsupported version or unordered replay")
            previous = event.timestamp
            yield event.model_dump()


def replay_world(path: str | Path, config: RobotConfig) -> WorldModel:
    world = WorldModel(config)
    for event in replay_events(path):
        if event["event"] == "detections":
            world.observe(
                [Detection.model_validate(d) for d in event["data"]["detections"]],
                event["timestamp"],
            )
    return world

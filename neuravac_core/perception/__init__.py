"""Perception providers; trained weights and calibration are explicit inputs."""

from neuravac_core.perception.camera import CameraCapture, LatestFrameBuffer
from neuravac_core.perception.interface import CameraFrame, PerceptionProvider
from neuravac_core.perception.projection import FloorProjector
from neuravac_core.perception.providers import (
    CLASSES,
    MockProvider,
    ONNXProvider,
    RemoteProvider,
    ReplayProvider,
)

__all__ = [
    "CLASSES",
    "CameraCapture",
    "CameraFrame",
    "FloorProjector",
    "LatestFrameBuffer",
    "MockProvider",
    "ONNXProvider",
    "PerceptionProvider",
    "RemoteProvider",
    "ReplayProvider",
]

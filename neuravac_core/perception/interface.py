"""RGB camera frames and the asynchronous detector boundary."""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from neuravac_core.models import Detection


@dataclass(frozen=True)
class CameraFrame:
    image: np.ndarray
    timestamp: float

    def __post_init__(self):
        if (
            not isinstance(self.image, np.ndarray)
            or self.image.ndim != 3
            or self.image.shape[2] != 3
            or self.image.dtype != np.uint8
            or min(self.image.shape[:2]) <= 0
        ):
            raise ValueError("image must be a nonempty RGB uint8 HWC array")
        if not math.isfinite(self.timestamp) or self.timestamp < 0:
            raise ValueError("timestamp must be finite and nonnegative")


class PerceptionProvider(ABC):
    @abstractmethod
    async def detect(self, frame: CameraFrame) -> list[Detection]:
        """Return observed detections; errors must not become empty observations."""

"""Explicit simulation, exact-timestamp replay, CPU ONNX and remote providers."""

import asyncio
import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import numpy as np

from neuravac_core.models import Detection
from neuravac_core.perception.interface import CameraFrame, PerceptionProvider

CLASSES = (
    "clean_floor",
    "debris",
    "cable",
    "clothing",
    "paper",
    "liquid",
    "shoe",
    "large_object",
    "unknown",
)


class MockProvider(PerceptionProvider):
    def __init__(self, labels: dict[float, list[Detection]] | None = None):
        self.labels = labels or {}

    async def detect(self, frame: CameraFrame) -> list[Detection]:
        return [item.model_copy(deep=True) for item in self.labels.get(frame.timestamp, [])]


class ReplayProvider(MockProvider):
    def __init__(self, path: str | Path):
        labels = {}
        for line_number, line in enumerate(Path(path).read_text().splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if set(record) == {"version", "event", "timestamp", "data"}:
                if record["version"] != 1:
                    raise ValueError(f"line {line_number}: unsupported recording version")
                if record["event"] != "detections":
                    continue
                if not isinstance(record["data"], dict) or set(record["data"]) != {"detections"}:
                    raise ValueError(f"line {line_number}: invalid detections event data")
                record = {
                    "timestamp": record["timestamp"],
                    "detections": record["data"]["detections"],
                }
            if set(record) != {"timestamp", "detections"}:
                raise ValueError(f"line {line_number}: expected timestamp and detections")
            timestamp = float(record["timestamp"])
            if not np.isfinite(timestamp) or timestamp < 0 or timestamp in labels:
                raise ValueError(f"line {line_number}: invalid or duplicate timestamp")
            items = [Detection.model_validate(item) for item in record["detections"]]
            if any(item.timestamp != timestamp for item in items):
                raise ValueError(f"line {line_number}: detection timestamp mismatch")
            labels[timestamp] = items
        super().__init__(labels)


def box_iou(a, b) -> float:
    intersection = max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(
        0.0, min(a[3], b[3]) - max(a[1], b[1])
    )
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union if union > 0 else 0.0


def debris_area_proxy(class_name: str, confidence: float, bbox, image_shape) -> float:
    """Confidence-weighted image fraction; not physical debris count or floor area."""
    if class_name != "debris" or bbox is None:
        return 0.0
    height, width = image_shape[:2]
    x1, y1, x2, y2 = bbox
    area = max(0, min(width, x2) - max(0, x1)) * max(0, min(height, y2) - max(0, y1))
    return float(area / (height * width) * confidence)


class ONNXProvider(PerceptionProvider):
    """NCHW float RGB input; [1,N,6] xyxy pixels/confidence/class output.

    Input uses direct resize to 320x320. Ultralytics raw outputs do NOT meet
    this contract; use ml/export_onnx.py to wrap them before deployment.
    """

    def __init__(
        self,
        model_path: str | Path,
        classes=CLASSES,
        confidence: float = 0.5,
        nms_iou: float = 0.45,
        session=None,
    ):
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"ONNX weights unavailable: {self.model_path}; train/export a real floor detector first"
            )
        if (
            not classes
            or len(set(classes)) != len(classes)
            or any(item not in CLASSES for item in classes)
        ):
            raise ValueError("classes must be unique known floor classes in training order")
        if not 0 <= confidence <= 1 or not 0 <= nms_iou <= 1:
            raise ValueError("confidence and nms_iou must be in [0,1]")
        if session is None:
            try:
                import onnxruntime as ort
            except ImportError as exc:
                raise RuntimeError("Install neuravac[vision] for CPU ONNX inference") from exc
            session = ort.InferenceSession(str(self.model_path), providers=["CPUExecutionProvider"])
        inputs = session.get_inputs()
        if (
            len(inputs) != 1
            or inputs[0].shape != [1, 3, 320, 320]
            or inputs[0].type != "tensor(float)"
        ):
            raise ValueError("Expected one float32 input [1,3,320,320]")
        self.session, self.input_name = session, inputs[0].name
        self.classes, self.confidence, self.nms_iou = classes, confidence, nms_iou

    def _detect(self, frame: CameraFrame) -> list[Detection]:
        height, width = frame.image.shape[:2]
        # Nearest sampling avoids a heavyweight resize dependency in the core.
        ys = np.minimum((np.arange(320) * height / 320).astype(int), height - 1)
        xs = np.minimum((np.arange(320) * width / 320).astype(int), width - 1)
        tensor = (
            np.ascontiguousarray(
                frame.image[ys[:, None], xs].transpose(2, 0, 1)[None], dtype=np.float32
            )
            / 255
        )
        outputs = self.session.run(None, {self.input_name: tensor})
        if not outputs:
            raise ValueError("Detector returned no tensors")
        rows = np.asarray(outputs[0])
        if (
            rows.ndim != 3
            or rows.shape[0] != 1
            or rows.shape[2] != 6
            or not np.isfinite(rows).all()
        ):
            raise ValueError(
                "Expected finite [1,N,6] xyxy/confidence/class tensor; raw YOLO outputs require conversion"
            )
        detections: list[Detection] = []
        for x1, y1, x2, y2, score, class_id in sorted(rows[0], key=lambda row: -row[4]):
            if (
                score < 0
                or score > 1
                or class_id != int(class_id)
                or not 0 <= class_id < len(self.classes)
            ):
                raise ValueError("Invalid detector confidence or class ID")
            if score < self.confidence:
                continue
            coords = (
                np.clip([x1, y1, x2, y2], 0, 320) * np.array([width, height, width, height]) / 320
            )
            if coords[2] <= coords[0] or coords[3] <= coords[1]:
                continue
            class_name = self.classes[int(class_id)]
            bbox = (float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3]))
            if any(
                item.class_name == class_name and box_iou(item.bbox, bbox) > self.nms_iou
                for item in detections
            ):
                continue
            detections.append(
                Detection(
                    class_name=class_name,
                    confidence=float(score),
                    timestamp=frame.timestamp,
                    source="onnx_cpu",
                    bbox=bbox,
                    debris_score=debris_area_proxy(
                        class_name, float(score), bbox, frame.image.shape
                    ),
                )
            )
        return detections

    async def detect(self, frame: CameraFrame) -> list[Detection]:
        return await asyncio.to_thread(self._detect, frame)


class RemoteProvider(PerceptionProvider):
    """Explicit HTTP vision endpoint; /health must verify the deployed model first.

    Endpoint API: GET health_url -> {ready:true,model:configured_model};
    POST endpoint -> {detections:[Detection,...]} with RGB shape/pixels/timestamp.
    """

    def __init__(
        self,
        endpoint: str,
        model: str,
        health_url: str,
        token: str | None = None,
        timeout_s: float = 5,
        client: httpx.AsyncClient | None = None,
    ):
        for url in (endpoint, health_url):
            parsed = urlsplit(url)
            if (
                parsed.scheme not in ("https", "http")
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("Use an explicit HTTP(S) URL without credentials/query/fragment")
            if parsed.scheme != "https" and parsed.hostname not in (
                "localhost",
                "127.0.0.1",
                "::1",
            ):
                raise ValueError("Nonlocal endpoints require HTTPS")
        if (urlsplit(endpoint).scheme, urlsplit(endpoint).netloc) != (
            urlsplit(health_url).scheme,
            urlsplit(health_url).netloc,
        ):
            raise ValueError("Health verification must use the inference endpoint origin")
        if not model or not 0 < timeout_s <= 60:
            raise ValueError("Explicit model and bounded timeout required")
        self.endpoint, self.model, self.health_url = endpoint, model, health_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.client = client or httpx.AsyncClient(timeout=timeout_s, follow_redirects=False)
        self.timeout_s = timeout_s
        self.verified = False

    async def _request_json(self, method: str, url: str, payload: dict | None = None) -> dict:
        async def collect() -> dict:
            async with self.client.stream(
                method, url, headers=self.headers, timeout=self.timeout_s, json=payload
            ) as response:
                response.raise_for_status()
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > 2_000_000:
                        raise ValueError("remote response exceeds size limit")
                parsed = json.loads(data)
                if not isinstance(parsed, dict):
                    raise ValueError("remote response must be an object")
                return parsed

        return await asyncio.wait_for(collect(), timeout=self.timeout_s)

    async def verify(self):
        payload = await self._request_json("GET", self.health_url)
        if payload.get("ready") is not True or payload.get("model") != self.model:
            raise RuntimeError("Remote endpoint did not verify the configured model")
        self.verified = True

    async def detect(self, frame: CameraFrame) -> list[Detection]:
        if not self.verified:
            await self.verify()
        if frame.image.size > 320 * 320 * 3:
            raise ValueError("Remote frames must be at most 320x320 pixels")
        payload = await self._request_json(
            "POST",
            self.endpoint,
            {
                "model": self.model,
                "timestamp": frame.timestamp,
                "shape": list(frame.image.shape),
                "rgb": frame.image.reshape(-1).tolist(),
            },
        )
        if set(payload) != {"detections"}:
            raise ValueError("Remote response must contain only detections")
        result = [Detection.model_validate(item) for item in payload["detections"]]
        for item in result:
            if "debris_score" not in item.model_fields_set:
                item.debris_score = debris_area_proxy(
                    item.class_name, item.confidence, item.bbox, frame.image.shape
                )
        if any(item.timestamp != frame.timestamp for item in result):
            raise ValueError("Remote detection timestamps must match input frame")
        return result

    async def close(self):
        await self.client.aclose()

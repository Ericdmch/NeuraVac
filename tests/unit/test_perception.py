import json

import numpy as np
import pytest

from neuravac_core.models import Detection, Pose
from neuravac_core.perception import CameraFrame, MockProvider, ONNXProvider, ReplayProvider
from neuravac_core.perception.camera import LatestFrameBuffer
from neuravac_core.perception.projection import FloorProjector


@pytest.mark.asyncio
async def test_mock_requires_explicit_timestamp_labels():
    frame = CameraFrame(np.zeros((8, 8, 3), dtype=np.uint8), 1.0)
    assert await MockProvider().detect(frame) == []
    label = Detection(class_name="cable", confidence=0.9, timestamp=1, source="sim")
    provider = MockProvider({1.0: [label]})
    assert (await provider.detect(frame))[0].class_name == "cable"
    assert await provider.detect(CameraFrame(frame.image, 2)) == []


@pytest.mark.asyncio
async def test_replay_does_not_use_nearest_future_detection(tmp_path):
    path = tmp_path / "detections.jsonl"
    path.write_text(
        json.dumps(
            {
                "timestamp": 1.0,
                "detections": [
                    {
                        "class_name": "debris",
                        "confidence": 0.8,
                        "timestamp": 1,
                        "source": "recorded",
                    }
                ],
            }
        )
        + "\n"
    )
    provider = ReplayProvider(path)
    assert len(await provider.detect(CameraFrame(np.zeros((8, 8, 3), dtype=np.uint8), 1))) == 1
    assert await provider.detect(CameraFrame(np.zeros((8, 8, 3), dtype=np.uint8), 1.1)) == []


def test_missing_onnx_weights_fail_explicitly(tmp_path):
    with pytest.raises(FileNotFoundError):
        ONNXProvider(tmp_path / "missing.onnx")


@pytest.mark.asyncio
async def test_onnx_contract_scales_boxes_and_suppresses_overlap(tmp_path):
    class Input:
        name = "images"
        shape = [1, 3, 320, 320]
        type = "tensor(float)"

    class Session:
        def get_inputs(self):
            return [Input()]

        def run(self, output_names, inputs):
            assert inputs["images"].shape == (1, 3, 320, 320)
            assert inputs["images"].dtype == np.float32
            # contract is [1,N,6]: x1,y1,x2,y2,confidence,class_id.
            return [np.array([[[32, 32, 160, 160, 0.9, 2], [33, 33, 160, 160, 0.8, 2]]])]

    path = tmp_path / "explicit.onnx"
    path.write_bytes(b"test-session")
    provider = ONNXProvider(path, session=Session())
    result = await provider.detect(CameraFrame(np.zeros((160, 640, 3), dtype=np.uint8), 7))
    assert len(result) == 1
    assert result[0].bbox == pytest.approx((64, 16, 320, 80))
    assert result[0].class_name == "cable"
    assert result[0].timestamp == 7


def test_projector_rejects_horizon_and_transforms_to_map():
    # optical x right, y down, z forward -> robot x forward, y left, z up.
    transform = np.array([[0, 0, 1, 0], [-1, 0, 0, 0], [0, -1, 0, 1], [0, 0, 0, 1]], dtype=float)
    projector = FloorProjector(
        np.array([[100, 0, 50], [0, 100, 50], [0, 0, 1]]), transform, image_size=(100, 100)
    )
    assert projector.project_pixel(50, 50) is None
    assert projector.project_pixel(50, 20) is None
    assert projector.project_pixel(101, 90) is None
    assert projector.project_pixel(50, 100) is None
    assert projector.project_pixel(50, 90, Pose(x=1, y=2)) == pytest.approx((3.5, 2))


def test_latest_frame_buffer_drops_old_frames():
    buffer = LatestFrameBuffer()
    buffer.publish(CameraFrame(np.zeros((2, 2, 3), dtype=np.uint8), 1))
    buffer.publish(CameraFrame(np.zeros((2, 2, 3), dtype=np.uint8), 2))
    assert buffer.latest().timestamp == 2


@pytest.mark.parametrize(
    "image,timestamp", [(np.zeros((2, 2)), 1), (np.zeros((2, 2, 3), dtype=np.uint8), float("nan"))]
)
def test_invalid_frames_are_rejected(image, timestamp):
    with pytest.raises(ValueError):
        CameraFrame(image, timestamp)


@pytest.mark.asyncio
async def test_remote_requires_health_model_verification():
    import httpx

    from neuravac_core.perception import RemoteProvider

    def respond(request):
        return httpx.Response(200, json={"ready": True, "model": "wrong-model"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    provider = RemoteProvider(
        "https://vision.example/infer", "floor-v1", "https://vision.example/health", client=client
    )
    with pytest.raises(RuntimeError, match="verify"):
        await provider.detect(CameraFrame(np.zeros((8, 8, 3), dtype=np.uint8), 1))
    await provider.close()


@pytest.mark.asyncio
async def test_onnx_rejects_raw_yolo_output(tmp_path):
    class Input:
        name, shape, type = "images", [1, 3, 320, 320], "tensor(float)"

    class Session:
        def get_inputs(self):
            return [Input()]

        def run(self, *_):
            return [np.zeros((1, 13, 2100))]

    path = tmp_path / "raw.onnx"
    path.write_bytes(b"fake")
    provider = ONNXProvider(path, session=Session())
    with pytest.raises(ValueError, match="raw YOLO"):
        await provider.detect(CameraFrame(np.zeros((8, 8, 3), dtype=np.uint8), 1))


@pytest.mark.asyncio
async def test_replay_reads_session_recorder_detections_envelope(tmp_path):
    path = tmp_path / "session.jsonl"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "event": "detections",
                "timestamp": 3.0,
                "data": {
                    "detections": [
                        {
                            "class_name": "cable",
                            "confidence": 0.9,
                            "timestamp": 3.0,
                            "source": "camera",
                        }
                    ]
                },
            }
        )
        + "\n"
    )
    result = await ReplayProvider(path).detect(CameraFrame(np.zeros((4, 4, 3), dtype=np.uint8), 3))
    assert result[0].class_name == "cable"


@pytest.mark.asyncio
async def test_onnx_debris_score_is_normalized_visible_area(tmp_path):
    class Input:
        name, shape, type = "images", [1, 3, 320, 320], "tensor(float)"

    class Session:
        def get_inputs(self):
            return [Input()]

        def run(self, *_):
            return [np.array([[[0, 0, 160, 160, 0.8, 1], [160, 0, 320, 160, 0.9, 2]]])]

    path = tmp_path / "test.onnx"
    path.write_bytes(b"synthetic-contract")
    observations = await ONNXProvider(path, session=Session()).detect(
        CameraFrame(np.zeros((100, 200, 3), dtype=np.uint8), 1)
    )
    by_class = {item.class_name: item for item in observations}
    assert by_class["debris"].debris_score == pytest.approx(0.2)
    assert by_class["cable"].debris_score == 0


@pytest.mark.asyncio
async def test_remote_debris_score_fills_missing_but_preserves_explicit_measurement():
    import httpx

    from neuravac_core.perception import RemoteProvider

    def respond(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"ready": True, "model": "floor"})
        return httpx.Response(
            200,
            json={
                "detections": [
                    {
                        "class_name": "debris",
                        "confidence": 0.8,
                        "timestamp": 1,
                        "source": "remote",
                        "bbox": [0, 0, 10, 10],
                    },
                    {
                        "class_name": "debris",
                        "confidence": 0.9,
                        "timestamp": 1,
                        "source": "remote",
                        "bbox": [10, 10, 20, 20],
                        "debris_score": 0.7,
                    },
                ]
            },
        )

    provider = RemoteProvider(
        "https://vision.example/infer",
        "floor",
        "https://vision.example/health",
        client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
    )
    result = await provider.detect(CameraFrame(np.zeros((20, 20, 3), dtype=np.uint8), 1))
    assert result[0].debris_score == pytest.approx(0.2)
    assert result[1].debris_score == 0.7
    await provider.close()


async def test_remote_vision_absolute_deadline_and_bounded_body():
    import asyncio

    import httpx

    from neuravac_core.perception import RemoteProvider

    class SlowBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(20):
                await asyncio.sleep(0.01)
                yield b" "

    def slow(request):
        return httpx.Response(200, stream=SlowBody())

    provider = RemoteProvider(
        "https://vision.test/infer",
        "floor",
        "https://vision.test/health",
        timeout_s=0.025,
        client=httpx.AsyncClient(transport=httpx.MockTransport(slow)),
    )
    with pytest.raises(TimeoutError):
        await provider.verify()
    await provider.close()

    def large(request):
        return httpx.Response(200, content=b" " * 2_100_000)

    provider = RemoteProvider(
        "https://vision.test/infer",
        "floor",
        "https://vision.test/health",
        client=httpx.AsyncClient(transport=httpx.MockTransport(large)),
    )
    with pytest.raises(ValueError, match="size"):
        await provider.verify()
    await provider.close()

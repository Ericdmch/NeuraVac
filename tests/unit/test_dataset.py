import numpy as np
import pytest

from datasets.floormess import deduplicate, grouped_split, validate_yolo_labels
from ml.evaluate import evaluate_detections


@pytest.mark.parametrize(
    "line",
    [
        "9 .5 .5 .1 .1",
        "1 nan .5 .1 .1",
        "1 .9 .5 .4 .1",
        "1.5 .5 .5 .1 .1",
        "1 .5 .5 0 .1",
        "1 .5 .5 .1",
    ],
)
def test_invalid_yolo_boxes_rejected(line):
    with pytest.raises(ValueError):
        validate_yolo_labels(line)


def test_yolo_labels_allow_empty_negative_and_valid_box():
    assert validate_yolo_labels("") == []
    assert validate_yolo_labels("2 .5 .5 .2 .4") == [(2, 0.5, 0.5, 0.2, 0.4)]


def test_split_keeps_sessions_together_and_is_deterministic():
    rows = [
        {"id": f"{group}-{i}", "group": group}
        for group in ("a", "b", "c", "d", "e")
        for i in range(3)
    ]
    first = grouped_split(rows, seed=42)
    assert first == grouped_split(list(reversed(rows)), seed=42)
    group_sets = [{row["group"] for row in values} for values in first.values()]
    assert not (
        group_sets[0] & group_sets[1]
        or group_sets[1] & group_sets[2]
        or group_sets[0] & group_sets[2]
    )
    assert sum(map(len, first.values())) == 15


def test_dedup_uses_pixels_and_preserves_first_frame():
    images = [
        np.zeros((4, 4, 3), dtype=np.uint8),
        np.zeros((4, 4, 3), dtype=np.uint8),
        np.full((4, 4, 3), 255, dtype=np.uint8),
    ]
    assert deduplicate(images) == [0, 2]


def test_evaluation_counts_cable_false_negative_and_iou():
    truth = [
        {"image_id": "a", "class_name": "cable", "bbox": [0, 0, 10, 10]},
        {"image_id": "a", "class_name": "debris", "bbox": [20, 20, 30, 30]},
    ]
    predictions = [
        {"image_id": "a", "class_name": "debris", "confidence": 0.9, "bbox": [20, 20, 30, 30]}
    ]
    report = evaluate_detections(truth, predictions)
    assert report["precision"] == 1
    assert report["recall"] == 0.5
    assert report["mean_matched_iou"] == 1
    assert report["per_class"]["cable"]["false_negatives"] == 1


def test_export_deduplicates_before_splitting_and_validates_conflicting_labels(tmp_path):
    import json

    from PIL import Image

    from datasets.floormess import export_dataset

    rows = []
    for index in range(4):
        Image.fromarray(np.full((8, 8, 3), index * 40, dtype=np.uint8)).save(
            tmp_path / f"{index}.png"
        )
        (tmp_path / f"{index}.txt").write_text("2 .5 .5 .2 .2\n")
        rows.append(
            {
                "id": str(index),
                "group": str(index),
                "image": f"{index}.png",
                "label": f"{index}.txt",
            }
        )
    rows.append(
        {"id": "duplicate", "group": "duplicate-session", "image": "0.png", "label": "0.txt"}
    )
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("\n".join(json.dumps(row) for row in rows))
    counts = export_dataset(manifest, tmp_path / "export")
    assert sum(counts.values()) == 4
    assert all(count > 0 for count in counts.values())
    assert (tmp_path / "export/data.yaml").is_file()


def test_extract_video_creates_unlabeled_manifest(tmp_path):
    import json

    import cv2

    from tools.floormess import extract_frames

    video = tmp_path / "clip.avi"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 5, (16, 16))
    if not writer.isOpened():
        pytest.skip("video encoder unavailable")
    for value in (0, 50, 100, 150, 200):
        writer.write(np.full((16, 16, 3), value, dtype=np.uint8))
    writer.release()
    manifest = extract_frames(video, tmp_path / "frames", "session-one", every_s=0.4)
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    assert len(rows) == 3
    assert {row["group"] for row in rows} == {"session-one"}
    assert not (tmp_path / "frames" / rows[0]["label"]).exists()


def test_training_refuses_unavailable_weights_without_download(tmp_path):
    from ml.train import train

    with pytest.raises(FileNotFoundError):
        train(tmp_path / "missing.pt", tmp_path / "data.yaml", tmp_path / "runs")


@pytest.mark.asyncio
async def test_benchmark_reports_measured_latency_and_prediction(tmp_path):
    from neuravac_core.models import Detection
    from neuravac_core.perception import CameraFrame, MockProvider
    from tools.benchmark_models import benchmark_provider

    provider = MockProvider(
        {
            1: [
                Detection(
                    class_name="cable",
                    confidence=0.9,
                    timestamp=1,
                    source="simulation",
                    bbox=(0, 0, 10, 10),
                )
            ]
        }
    )
    result, predictions = await benchmark_provider(
        provider, [("test-image", CameraFrame(np.zeros((16, 16, 3), dtype=np.uint8), 1))], warmup=0
    )
    assert result["frames"] == 1
    assert result["latency_ms"]["mean"] >= 0
    assert result["peak_python_bytes"] >= 0
    assert predictions[0]["image_id"] == "test-image"
    assert predictions[0]["class_name"] == "cable"


def test_near_duplicate_signature_keeps_a_changed_thin_cable():
    base = np.full((64, 64, 3), 180, dtype=np.uint8)
    base[20:50, 20] = 0
    noisy = np.clip(base.astype(int) + 2, 0, 255).astype(np.uint8)
    shifted_cable = np.full((64, 64, 3), 180, dtype=np.uint8)
    shifted_cable[20:50, 40] = 0
    assert deduplicate([base, noisy, shifted_cable], distance_threshold=0.02) == [0, 2]
    assert deduplicate([base, noisy], distance_threshold=0) == [0, 1]


def test_export_preserves_near_duplicate_cable_labels_and_links_sessions(tmp_path):
    import json

    from PIL import Image

    from datasets.floormess import export_dataset

    rows = []
    for index, value in enumerate((180, 182, 30, 60, 90)):
        image = np.full((64, 64, 3), value, dtype=np.uint8)
        if index < 2:
            image[20:50, 20] = index * 2
        Image.fromarray(image).save(tmp_path / f"{index}.png")
        (tmp_path / f"{index}.txt").write_text("2 .32 .55 .05 .5\n")
        rows.append(
            {
                "id": str(index),
                "group": f"session-{index}",
                "image": f"{index}.png",
                "label": f"{index}.txt",
            }
        )
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("\n".join(json.dumps(row) for row in rows))
    counts = export_dataset(manifest, tmp_path / "export", distance_threshold=0.02)
    assert sum(counts.values()) == 5  # Cable examples need review rather than automated removal.
    split = json.loads((tmp_path / "export/split.json").read_text())
    assignments = {row["id"]: name for name, entries in split.items() for row in entries}
    assert assignments["0"] == assignments["1"]

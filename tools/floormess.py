#!/usr/bin/env python3
"""FloorMess video and annotation CLI. Run python -m tools.floormess --help."""

import argparse
import json
import math
import time
from pathlib import Path

from datasets.floormess import (
    export_dataset,
    grouped_split,
    load_manifest,
    prepare_manifest,
    validate_yolo_labels,
)
from neuravac_core.perception.providers import CLASSES


def record_video(output: Path, device: int, seconds: float, fps: float, width: int, height: int):
    import cv2

    if (
        seconds <= 0
        or fps <= 0
        or width <= 0
        or height <= 0
        or not math.isfinite(seconds)
        or not math.isfinite(fps)
    ):
        raise ValueError("Positive finite capture settings required")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(device)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    writer = None
    count = 0
    try:
        if not capture.isOpened():
            raise RuntimeError("Unable to open camera")
        start, next_frame = time.monotonic(), time.monotonic()
        while time.monotonic() - start < seconds:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError("Camera read failed")
            if writer is None:
                height, width = frame.shape[:2]
                writer = cv2.VideoWriter(
                    str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
                )
                if not writer.isOpened():
                    raise RuntimeError("Video encoder unavailable")
            writer.write(frame)
            count += 1
            next_frame += 1 / fps
            time.sleep(max(0, next_frame - time.monotonic()))
    finally:
        capture.release()
        if writer is not None:
            writer.release()
    if count == 0:
        raise RuntimeError("No frames recorded")
    output.with_suffix(output.suffix + ".json").write_text(
        json.dumps(
            {
                "source": "physical_camera",
                "device": device,
                "frames": count,
                "requested_fps": fps,
                "duration_s": seconds,
            },
            indent=2,
        )
        + "\n"
    )


def extract_frames(video: Path, output: Path, group: str, every_s: float = 1) -> Path:
    import cv2

    if not group or not math.isfinite(every_s) or every_s <= 0:
        raise ValueError("Explicit session group and positive finite extraction interval required")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Extraction directory must be empty")
    capture = cv2.VideoCapture(str(video))
    rows = []
    try:
        if not capture.isOpened():
            raise RuntimeError(f"Cannot open video {video}")
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            raise RuntimeError("Video has no valid FPS for timestamp extraction")
        output.mkdir(parents=True, exist_ok=True)
        (output / "images").mkdir()
        (output / "labels").mkdir()
        index, next_time = 0, 0.0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp = index / fps
            if timestamp + 1e-9 >= next_time:
                stem = f"{index:08d}"
                image = f"images/{stem}.png"
                if not cv2.imwrite(str(output / image), frame):
                    raise RuntimeError("Failed to write extracted image")
                rows.append(
                    {
                        "id": stem,
                        "group": group,
                        "image": image,
                        "label": f"labels/{stem}.txt",
                        "timestamp": timestamp,
                    }
                )
                next_time += every_s
            index += 1
    finally:
        capture.release()
    if not rows:
        raise RuntimeError("Video contained no decodable frames")
    manifest = output / "manifest.jsonl"
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows))
    # Label files are deliberately absent until annotation. Empty labels explicitly mean a verified negative.
    return manifest


def dedup_manifest(manifest: Path, output: Path, distance_threshold: float = 0.02):
    if output.resolve().parent != manifest.resolve().parent:
        raise ValueError(
            "Dedup output must share the manifest directory to preserve relative paths"
        )
    unique, review = prepare_manifest(manifest, distance_threshold, require_labels=False)
    output.write_text("".join(json.dumps(row) + "\n" for row in unique))
    output.with_suffix(".review.json").write_text(json.dumps(review, indent=2) + "\n")
    return {
        "kept": len(unique),
        "dropped": len(review["dropped"]),
        "distance_threshold": distance_threshold,
        "review": str(output.with_suffix(".review.json")),
    }


def visualize(image_path: Path, label_path: Path, output: Path):
    from PIL import Image, ImageDraw

    labels = validate_yolo_labels(label_path.read_text())
    with Image.open(image_path) as original:
        image = original.convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    for class_id, x, y, w, h in labels:
        box = ((x - w / 2) * width, (y - h / 2) * height, (x + w / 2) * width, (y + h / 2) * height)
        draw.rectangle(box, outline="red", width=2)
        draw.text((box[0], max(0, box[1] - 12)), CLASSES[class_id], fill="red")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record")
    record.add_argument("output", type=Path)
    record.add_argument("--device", type=int, default=0)
    record.add_argument("--seconds", type=float, default=60)
    record.add_argument("--fps", type=float, default=10)
    record.add_argument("--width", type=int, default=640)
    record.add_argument("--height", type=int, default=480)
    extract = sub.add_parser("extract")
    extract.add_argument("video", type=Path)
    extract.add_argument("output", type=Path)
    extract.add_argument("--group", required=True)
    extract.add_argument("--every-s", type=float, default=1)
    dedup = sub.add_parser("dedup")
    dedup.add_argument("manifest", type=Path)
    dedup.add_argument("output", type=Path)
    dedup.add_argument("--distance-threshold", type=float, default=0.02)
    split = sub.add_parser("split")
    split.add_argument("manifest", type=Path)
    split.add_argument("output", type=Path)
    split.add_argument("--seed", type=int, default=42)
    split.add_argument("--distance-threshold", type=float, default=0.02)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    view = sub.add_parser("visualize")
    view.add_argument("image", type=Path)
    view.add_argument("label", type=Path)
    view.add_argument("output", type=Path)
    export = sub.add_parser("export")
    export.add_argument("manifest", type=Path)
    export.add_argument("output", type=Path)
    export.add_argument("--seed", type=int, default=42)
    export.add_argument("--distance-threshold", type=float, default=0.02)
    args = parser.parse_args(argv)
    if args.command == "record":
        record_video(args.output, args.device, args.seconds, args.fps, args.width, args.height)
    elif args.command == "extract":
        print(extract_frames(args.video, args.output, args.group, args.every_s))
    elif args.command == "dedup":
        print(json.dumps(dedup_manifest(args.manifest, args.output, args.distance_threshold)))
    elif args.command == "split":
        rows, review = prepare_manifest(
            args.manifest, args.distance_threshold, require_labels=False
        )
        result = grouped_split(rows, args.seed)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        args.output.with_suffix(".review.json").write_text(json.dumps(review, indent=2) + "\n")
    elif args.command == "validate":
        rows = load_manifest(args.manifest)
        grouped_split(rows)
        for row in rows:
            if not (args.manifest.parent / row["image"]).is_file():
                raise FileNotFoundError(row["image"])
            validate_yolo_labels((args.manifest.parent / row["label"]).read_text())
        print(json.dumps({"validated": len(rows)}))
    elif args.command == "visualize":
        visualize(args.image, args.label, args.output)
    elif args.command == "export":
        print(
            json.dumps(
                export_dataset(args.manifest, args.output, args.seed, args.distance_threshold)
            )
        )


if __name__ == "__main__":
    main()

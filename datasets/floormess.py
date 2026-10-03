"""Strict labels, pixel deduplication and session-level deterministic splits."""

import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np

from neuravac_core.perception.providers import CLASSES


def validate_yolo_labels(
    text: str, class_count: int = len(CLASSES)
) -> list[tuple[int, float, float, float, float]]:
    labels = []
    if class_count <= 0:
        raise ValueError("Positive class_count required")
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            raise ValueError(f"line {line_number}: expected class x_center y_center width height")
        try:
            class_id = int(parts[0])
            x, y, width, height = map(float, parts[1:])
        except ValueError as exc:
            raise ValueError(f"line {line_number}: invalid number") from exc
        if not 0 <= class_id < class_count or not all(
            math.isfinite(v) for v in (x, y, width, height)
        ):
            raise ValueError(f"line {line_number}: invalid class or nonfinite coordinate")
        if (
            not 0 < width <= 1
            or not 0 < height <= 1
            or x - width / 2 < -1e-9
            or y - height / 2 < -1e-9
            or x + width / 2 > 1 + 1e-9
            or y + height / 2 > 1 + 1e-9
        ):
            raise ValueError(
                f"line {line_number}: box extends beyond normalized image or has no area"
            )
        labels.append((class_id, x, y, width, height))
    return labels


def pixel_digest(image: np.ndarray) -> str:
    return hashlib.sha256(
        str((image.shape, image.dtype.str)).encode() + np.ascontiguousarray(image).tobytes()
    ).hexdigest()


def visual_signature(image: np.ndarray, cells: int = 32) -> np.ndarray:
    """Local RGB mean/min/max preserves small dark structures better than a mean hash."""
    if (
        image.ndim != 3
        or image.shape[2] != 3
        or image.dtype != np.uint8
        or min(image.shape[:2]) <= 0
    ):
        raise ValueError("Signature requires a nonempty RGB uint8 image")
    height, width = image.shape[:2]
    rows, columns = min(cells, height), min(cells, width)
    block_h, block_w = math.ceil(height / rows), math.ceil(width / columns)
    padded = np.pad(
        image, ((0, rows * block_h - height), (0, columns * block_w - width), (0, 0)), mode="edge"
    )
    blocks = padded.reshape(rows, block_h, columns, block_w, 3).astype(np.float32)
    return (
        np.concatenate(
            (blocks.mean(axis=(1, 3)), blocks.min(axis=(1, 3)), blocks.max(axis=(1, 3))), axis=2
        )
        / 255
    )


def signature_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Maximum local feature difference; thin changes cannot vanish in a global average."""
    return float(np.max(np.abs(a - b))) if a.shape == b.shape else 1.0


def _check_threshold(distance_threshold: float):
    if not math.isfinite(distance_threshold) or not 0 <= distance_threshold <= 1:
        raise ValueError(
            "distance_threshold must be finite in [0,1]; zero selects exact pixels only"
        )


def deduplicate(images, distance_threshold: float = 0.02) -> list[int]:
    """Keep first exact/visually similar frames using conservative local signatures."""
    _check_threshold(distance_threshold)
    seen, keep, signatures = set(), [], []
    for index, image in enumerate(images):
        digest = pixel_digest(image)
        signature = visual_signature(image)
        near = distance_threshold > 0 and any(
            image.shape == shape and signature_distance(signature, other) <= distance_threshold
            for shape, other in signatures
        )
        if digest not in seen and not near:
            seen.add(digest)
            keep.append(index)
            signatures.append((image.shape, signature))
    return keep


def grouped_split(
    rows: list[dict], seed: int = 42, ratios=(0.7, 0.15, 0.15)
) -> dict[str, list[dict]]:
    if (
        len(ratios) != 3
        or not all(math.isfinite(r) and r >= 0 for r in ratios)
        or not math.isclose(sum(ratios), 1)
    ):
        raise ValueError("Three nonnegative ratios must sum to one")
    ids, groups = set(), {}
    for row in rows:
        if not row.get("id") or not row.get("group") or row["id"] in ids:
            raise ValueError("Each sample needs a unique id and explicit collection-session group")
        ids.add(row["id"])
        groups.setdefault(str(row["group"]), []).append(row)
    names = ("train", "val", "test")
    result = {name: [] for name in names}
    ordered = sorted(
        groups, key=lambda group: hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()
    )
    count = len(ordered)
    if count < sum(ratio > 0 for ratio in ratios):
        raise ValueError("Need at least one independent group per requested split")
    sizes = [math.floor(count * ratio) for ratio in ratios]
    for index in sorted(range(3), key=lambda i: (-(count * ratios[i] - sizes[i]), i))[
        : count - sum(sizes)
    ]:
        sizes[index] += 1
    # Keep positive splits nonempty without splitting any collection group.
    for index, ratio in enumerate(ratios):
        if ratio > 0 and sizes[index] == 0:
            donor = max(range(3), key=lambda i: sizes[i])
            sizes[donor] -= 1
            sizes[index] += 1
    start = 0
    for name, size in zip(names, sizes, strict=True):
        for group in ordered[start : start + size]:
            result[name].extend(sorted(groups[group], key=lambda row: row["id"]))
        start += size
    return result


def load_manifest(path: str | Path) -> list[dict]:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    for row in rows:
        if set(row) - {"id", "group", "image", "label", "timestamp", "sha256"} or not {
            "id",
            "group",
            "image",
            "label",
        } <= set(row):
            raise ValueError(
                "Manifest rows require id/group/image/label with optional timestamp/sha256"
            )
    return rows


def prepare_manifest(
    manifest: str | Path, distance_threshold: float = 0.02, require_labels: bool = True
) -> tuple[list[dict], dict]:
    """Link similar-session components before splitting; retain cable examples for review."""
    from PIL import Image

    _check_threshold(distance_threshold)
    path = Path(manifest)
    rows = load_manifest(path)
    if len({row["id"] for row in rows}) != len(rows) or any(
        not row["id"] or not row["group"] for row in rows
    ):
        raise ValueError("Unique IDs and explicit session groups required")
    parents = {str(row["group"]): str(row["group"]) for row in rows}

    def root(group):
        while parents[group] != group:
            parents[group] = parents[parents[group]]
            group = parents[group]
        return group

    records, keep, matches, dropped = [], [], [], []
    for row in sorted(rows, key=lambda item: item["id"]):
        label_path = path.parent / row["label"]
        labels = validate_yolo_labels(label_path.read_text()) if label_path.is_file() else None
        if require_labels and labels is None:
            raise FileNotFoundError(f"Unannotated image: {label_path}")
        with Image.open(path.parent / row["image"]) as image:
            pixels = np.asarray(image.convert("RGB"))
            record = {
                "row": row,
                "labels": labels,
                "shape": pixels.shape,
                "digest": pixel_digest(pixels),
                "signature": visual_signature(pixels),
            }
        duplicate_of = None
        for previous in records:
            exact = record["digest"] == previous["digest"]
            near = (
                distance_threshold > 0
                and record["shape"] == previous["shape"]
                and signature_distance(record["signature"], previous["signature"])
                <= distance_threshold
            )
            if not exact and not near:
                continue
            left, right = root(str(row["group"])), root(str(previous["row"]["group"]))
            parents[max(left, right)] = min(left, right)
            matches.append({"ids": [previous["row"]["id"], row["id"]], "exact": exact})
            if exact and labels != previous["labels"]:
                raise ValueError("Duplicate pixels have conflicting labels")
            # Never automatically remove cable positives from approximate comparisons.
            cable = any(
                label[0] == CLASSES.index("cable")
                for label in (labels or []) + (previous["labels"] or [])
            )
            if exact or (near and labels == previous["labels"] and not cable):
                duplicate_of = previous["row"]["id"]
        records.append(record)
        if duplicate_of is None:
            keep.append(record)
        else:
            dropped.append({"id": row["id"], "duplicate_of": duplicate_of})
    unique = [
        {**record["row"], "group": root(str(record["row"]["group"])), "sha256": record["digest"]}
        for record in keep
    ]
    review = {
        "distance_threshold": distance_threshold,
        "signature": "32x32 RGB block mean/min/max; maximum absolute normalized feature distance",
        "matches": matches,
        "dropped": dropped,
        "cable_policy": "near cable-positive samples retained; matching sessions linked before splitting",
        "review_required": True,
    }
    return unique, review


def export_dataset(
    manifest: str | Path, destination: str | Path, seed: int = 42, distance_threshold: float = 0.02
) -> dict:
    import yaml

    path, destination = Path(manifest), Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Export destination must be empty")
    unique, review = prepare_manifest(path, distance_threshold, require_labels=True)
    split = grouped_split(unique, seed)
    for name, entries in split.items():
        (destination / "images" / name).mkdir(parents=True, exist_ok=True)
        (destination / "labels" / name).mkdir(parents=True, exist_ok=True)
        for index, row in enumerate(entries):
            image_path, label_path = path.parent / row["image"], path.parent / row["label"]
            stem = f"{index:07d}"
            shutil.copyfile(
                image_path, destination / "images" / name / f"{stem}{image_path.suffix.lower()}"
            )
            shutil.copyfile(label_path, destination / "labels" / name / f"{stem}.txt")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "data.yaml").write_text(
        yaml.safe_dump(
            {
                "path": str(destination.resolve()),
                "train": "images/train",
                "val": "images/val",
                "test": "images/test",
                "names": dict(enumerate(CLASSES)),
            },
            sort_keys=False,
        )
    )
    (destination / "split.json").write_text(json.dumps(split, indent=2) + "\n")
    (destination / "dedup-review.json").write_text(json.dumps(review, indent=2) + "\n")
    return {name: len(entries) for name, entries in split.items()}

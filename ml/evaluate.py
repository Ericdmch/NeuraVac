"""Greedy confidence-ranked class-aware box evaluation, with cable misses."""

import json
import math
from pathlib import Path

from neuravac_core.perception.providers import CLASSES, box_iou


def evaluate_detections(
    truth: list[dict], predictions: list[dict], iou_threshold: float = 0.5
) -> dict:
    if not 0 < iou_threshold <= 1:
        raise ValueError("IoU threshold must be in (0,1]")
    for rows, is_prediction in ((truth, False), (predictions, True)):
        for row in rows:
            bbox = row.get("bbox", [])
            if (
                not row.get("image_id")
                or row.get("class_name") not in CLASSES
                or len(bbox) != 4
                or not all(math.isfinite(v) for v in bbox)
                or bbox[2] <= bbox[0]
                or bbox[3] <= bbox[1]
            ):
                raise ValueError("Expected image_id, known class and finite positive xyxy box")
            if is_prediction and not 0 <= row.get("confidence", -1) <= 1:
                raise ValueError("Prediction requires finite confidence in [0,1]")
    counts = {
        name: {"true_positives": 0, "false_positives": 0, "false_negatives": 0} for name in CLASSES
    }
    used, ious = set(), []
    for prediction in sorted(predictions, key=lambda item: -item["confidence"]):
        candidates = [
            (box_iou(item["bbox"], prediction["bbox"]), index)
            for index, item in enumerate(truth)
            if index not in used
            and item["image_id"] == prediction["image_id"]
            and item["class_name"] == prediction["class_name"]
        ]
        best = max(candidates, default=(0, -1))
        if best[0] >= iou_threshold:
            used.add(best[1])
            ious.append(best[0])
            counts[prediction["class_name"]]["true_positives"] += 1
        else:
            counts[prediction["class_name"]]["false_positives"] += 1
    for index, item in enumerate(truth):
        if index not in used:
            counts[item["class_name"]]["false_negatives"] += 1
    for values in counts.values():
        tp, fp, fn = values["true_positives"], values["false_positives"], values["false_negatives"]
        values["precision"] = tp / (tp + fp) if tp + fp else None
        values["recall"] = tp / (tp + fn) if tp + fn else None
    tp = sum(v["true_positives"] for v in counts.values())
    fp = sum(v["false_positives"] for v in counts.values())
    fn = sum(v["false_negatives"] for v in counts.values())
    return {
        "iou_threshold": iou_threshold,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "mean_matched_iou": sum(ious) / len(ious) if ious else None,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "per_class": counts,
    }


def write_report(report: dict, output: str | Path):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix(".json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    lines = [
        "# Measured detector evaluation",
        "",
        "Values reflect only the supplied held-out annotations and predictions.",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    lines += [
        f"| {key} | {report.get(key)} |"
        for key in (
            "precision",
            "recall",
            "mean_matched_iou",
            "true_positives",
            "false_positives",
            "false_negatives",
        )
    ]
    lines += [
        f"| cable false negatives | {report['per_class']['cable']['false_negatives']} |",
        "",
        "## Runtime measurements",
        "",
        "```json",
        json.dumps(report.get("runtime", {}), indent=2),
        "```",
        "",
    ]
    output.with_suffix(".md").write_text("\n".join(lines))

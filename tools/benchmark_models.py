"""Measured CPU latency/memory and held-out detection metrics; no synthetic accuracy."""

import argparse
import asyncio
import json
import resource
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

from ml.evaluate import evaluate_detections, write_report
from neuravac_core.perception import CameraFrame, ONNXProvider


def _max_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


async def benchmark_provider(provider, samples: list[tuple[str, CameraFrame]], warmup: int = 3):
    if not samples or warmup < 0:
        raise ValueError("Nonempty samples and nonnegative warmup required")
    for _ in range(warmup):
        await provider.detect(samples[0][1])
    durations, predictions = [], []
    tracemalloc.start()
    try:
        for image_id, frame in samples:
            start = time.perf_counter()
            result = await provider.detect(frame)
            durations.append((time.perf_counter() - start) * 1000)
            for item in result:
                if item.bbox is not None:
                    predictions.append(
                        {
                            "image_id": image_id,
                            "class_name": item.class_name,
                            "confidence": item.confidence,
                            "bbox": list(item.bbox),
                        }
                    )
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    runtime = {
        "frames": len(samples),
        "warmup_frames": warmup,
        "latency_ms": {
            "mean": float(np.mean(durations)),
            "p50": float(np.percentile(durations, 50)),
            "p95": float(np.percentile(durations, 95)),
        },
        "peak_python_bytes": peak,
        "process_peak_rss_bytes": _max_rss_bytes(),
        "memory_scope": "RSS high-water mark for entire process incl native runtime; tracemalloc measures Python allocations only",
        "provider": type(provider).__name__,
    }
    return runtime, predictions


async def run(model: Path, samples_path: Path, output: Path, warmup: int):
    from PIL import Image

    rows = [json.loads(line) for line in samples_path.read_text().splitlines() if line.strip()]
    samples, truth, ids = [], [], set()
    for row in rows:
        if set(row) != {"image_id", "image", "truth"} or row["image_id"] in ids:
            raise ValueError("Samples require unique image_id, image path and explicit truth list")
        ids.add(row["image_id"])
        with Image.open(samples_path.parent / row["image"]) as image:
            rgb = np.array(image.convert("RGB"))
        samples.append((row["image_id"], CameraFrame(rgb, float(len(samples)))))
        truth.extend({**item, "image_id": row["image_id"]} for item in row["truth"])
    provider = ONNXProvider(model)
    runtime, predictions = await benchmark_provider(provider, samples, warmup)
    runtime["model_size_bytes"] = model.stat().st_size
    runtime["execution_provider"] = "CPUExecutionProvider"
    report = evaluate_detections(truth, predictions)
    report["runtime"] = runtime
    report["dataset"] = str(samples_path)
    report["model"] = str(model)
    write_report(report, output)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmup", type=int, default=3)
    args = parser.parse_args(argv)
    asyncio.run(run(args.model, args.samples, args.output, args.warmup))


if __name__ == "__main__":
    main()

"""Measure this host; absent device/model/cloud measurements remain null."""

import argparse
import asyncio
import json
import os
import platform
import resource
import time
from pathlib import Path

import numpy as np

from neuravac_core.runtime import SimulationRuntime


def summary(values: list[float]) -> dict:
    return {
        "samples": len(values),
        "mean_ms": float(np.mean(values)) if values else None,
        "p95_ms": float(np.percentile(values, 95)) if values else None,
        "max_ms": max(values) if values else None,
    }


def temperature() -> float | None:
    path = Path("/sys/class/thermal/thermal_zone0/temp")
    try:
        return float(path.read_text()) / 1000
    except (OSError, ValueError):
        return None


async def benchmark(
    duration_s: float = 5,
    control_hz: float = 20,
    model: Path | None = None,
    camera: int | None = None,
    cloud: bool = False,
    dashboard_url: str | None = None,
) -> dict:
    if duration_s <= 0 or control_hz < 10:
        raise ValueError("positive duration and control rate ≥10 required")
    runtime = SimulationRuntime(move_chair=False)
    await runtime.initialize()
    runtime.start()
    provider = None
    capture = None
    inference = []
    camera_count = 0
    if model:
        from neuravac_core.perception import ONNXProvider

        provider = ONNXProvider(model)
    if camera is not None:
        import cv2

        capture = cv2.VideoCapture(camera)
        if not capture.isOpened():
            await runtime.close()
            capture.release()
            raise RuntimeError("camera unavailable")
    started = time.perf_counter()
    cpu_started = time.process_time()
    callbacks = []
    jitter = []
    stop_at = started + duration_s
    frames = 0

    async def vision() -> None:
        nonlocal camera_count, frames
        from neuravac_core.perception import CameraFrame

        while time.perf_counter() < stop_at:
            image = np.zeros((320, 320, 3), dtype=np.uint8)
            if capture:
                import cv2

                ok, bgr = await asyncio.to_thread(capture.read)
                if not ok:
                    raise RuntimeError("camera lost during benchmark")
                image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                camera_count += 1
            if provider:
                begin = time.perf_counter()
                await provider.detect(CameraFrame(image, time.monotonic()))
                inference.append((time.perf_counter() - begin) * 1000)
                frames += 1
            await asyncio.sleep(0.01 if capture and not provider else 0.2)

    vision_task = asyncio.create_task(vision()) if capture or provider else None
    deadline = started
    try:
        while time.perf_counter() < stop_at:
            before = time.perf_counter()
            jitter.append(max(0, (before - deadline) * 1000))
            await runtime.tick()
            callbacks.append((time.perf_counter() - before) * 1000)
            deadline += 1 / control_hz
            await asyncio.sleep(max(0, deadline - time.perf_counter()))
        if vision_task:
            await vision_task
    finally:
        if vision_task and not vision_task.done():
            vision_task.cancel()
        if capture:
            capture.release()
        await runtime.close()
    elapsed = time.perf_counter() - started
    usage = resource.getrusage(resource.RUSAGE_SELF)
    cloud_latency = None
    if cloud:
        from neuravac_core.cloud import NebiusClient, NebiusConfig

        async with NebiusClient(NebiusConfig.from_env()) as client:
            await client.decide(
                {
                    "mission": "benchmark safe high-level reasoning",
                    "battery_percent": 100,
                    "dirty_regions": [],
                    "hazards": [],
                    "recent_changes": [],
                }
            )
            cloud_latency = client.last_telemetry.get("latency_ms")
    dashboard_latency = None
    if dashboard_url:
        import httpx

        begin = time.perf_counter()
        async with httpx.AsyncClient(timeout=2) as client:
            headers = {}
            if os.getenv("NEURAVAC_API_TOKEN"):
                headers["Authorization"] = "Bearer " + os.environ["NEURAVAC_API_TOKEN"]
            response = await client.get(dashboard_url.rstrip("/") + "/api/state", headers=headers)
            response.raise_for_status()
        dashboard_latency = (time.perf_counter() - begin) * 1000
    return {
        "schema_version": 1,
        "mode": "simulation_core",
        "host": platform.machine(),
        "python": platform.python_version(),
        "duration_s": elapsed,
        "cpu_percent_one_core": 100 * (time.process_time() - cpu_started) / elapsed,
        "peak_rss_mb": usage.ru_maxrss / (1024**2 if platform.system() == "Darwin" else 1024),
        "cpu_temperature_c": temperature(),
        "control_callback": summary(callbacks),
        "control_jitter": summary(jitter),
        "control_effective_hz": len(callbacks) / elapsed,
        "perception_fps": frames / elapsed if provider else None,
        "perception_latency": summary(inference),
        "perception_input": "live_camera" if capture else "synthetic" if provider else None,
        "camera_fps": camera_count / elapsed if capture else None,
        "cloud_latency_ms": cloud_latency,
        "dashboard_request_ms": dashboard_latency,
        "ros_callback_latency_ms": None,
        "dashboard_cpu_percent": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=5)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--camera", type=int)
    parser.add_argument(
        "--cloud", action="store_true", help="Explicit opt-in to a billed Nebius request"
    )
    parser.add_argument("--dashboard-url")
    parser.add_argument("--output", type=Path, default=Path("artifacts/benchmark.json"))
    args = parser.parse_args()
    result = asyncio.run(
        benchmark(
            args.duration,
            model=args.model,
            camera=args.camera,
            cloud=args.cloud,
            dashboard_url=args.dashboard_url,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(
        "# NeuraVac host benchmark\n\nMeasurements are from this host, not claimed Pi performance. Null means not measured.\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in result.items())
        + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

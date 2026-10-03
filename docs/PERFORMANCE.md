# Pi 4 performance validation

Architecture targets: safety20Hz, base≥10Hz, CPU ONNX perception2–5Hz at320×320, WebSocket4Hz. These are targets until measured on Pi hardware. The dashboard serves static assets; training and large NVIDIA models run remotely. Camera capture stores one latest frame and drops backlog; ONNX is off the control thread.

```bash
python tools/benchmark_pi.py --duration 10
python tools/benchmark_pi.py --duration 30 --camera 0 --model /path/to/floormess.onnx
python tools/benchmark_pi.py --duration 5 --cloud
python tools/benchmark_pi.py --dashboard-url http://127.0.0.1:8000
```

`--cloud` explicitly opts into a real billed request. Report JSON and Markdown include one-core process CPU utilization, peak resident memory, thermal-zone temperature when present, actual control callback samples/p95/jitter/effective rate, actual camera/perception FPS and inference latency when supplied, cloud round-trip latency and dashboard HTTP latency. Without a camera, supplied-model inference uses synthetic pixels and is labeled synthetic. ROS callback latency and per-dashboard-process CPU remain null in this host-only tool; use ROS tracing/process telemetry for them. No unavailable value is invented.

Compare model results with `python tools/benchmark_models.py --help` and `python -m ml.evaluate --help`. Use real labeled held-out sessions, class-specific cable false negatives, precision/recall and matched-box IoU, model size, memory and latency. Box IoU is not segmentation-mask IoU. Tune confidence/hazard expansion only after reviewing safety-critical missed cables. Run at least a30-minute thermal soak with camera, Nav2, dashboard and cloud active before selecting deployment rates.

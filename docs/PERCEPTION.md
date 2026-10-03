# Perception and FloorMess

No floor detector checkpoint, real labeled FloorMess dataset, measured model accuracy,
or Raspberry Pi inference benchmark is bundled. Synthetic tests validate software
contracts; they do not validate recognition. Camera calibration, trained weights,
held-out evaluation and real cable-miss measurements remain deployment requirements.

## Provider boundary

`CameraFrame(image, timestamp)` accepts nonempty RGB uint8 HWC arrays and finite
nonnegative observation time. Use the injected runtime monotonic clock; do not mix
wall, ROS and monotonic timestamps. `PerceptionProvider.detect(frame)` is async and
returns `list[Detection]`. Exceptions are failed observations, not clean-floor evidence.

- `MockProvider(labels={timestamp: [Detection,...]})` uses only explicitly provided
  simulation labels. No image content generates detections.
- `ReplayProvider(path)` consumes JSONL with exactly `timestamp` and `detections` per
  row; timestamps must be unique and every detection must match its row. Matching is
  exact: unmatched frames return no recorded detections rather than borrowing another time.
  Version-1 SessionRecorder envelopes (`version`, `event`, `timestamp`, `data`) are
  also accepted: detections events contain `data.detections`; other event types are skipped.
- `ONNXProvider(path)` requires actual supplied weights and `neuravac[vision]`.
  Initialization checks the input contract and inference checks output shape and values.
  CPU inference runs outside the event loop. Missing weights raise `FileNotFoundError`;
  absent ONNX Runtime raises a clear `RuntimeError`. Neither returns fabricated boxes.
- `RemoteProvider(endpoint, model, health_url, ...)` uses a specifically configured HTTPS
  vision endpoint (HTTP is allowed only on loopback). Same-origin GET health must return
  `{"ready":true,"model":"configured-model"}` before inference. POST receives `model`,
  `timestamp`, RGB `shape` and flattened uint8 `rgb`; it returns only `detections` with
  strict shared schemas and matching timestamps. Inputs are bounded to 320×320 pixels.
  Timeout is bounded, redirects disabled, and credentials use headers. This protocol
  requires a real deployed service; it does not imply that any Nebius model supports it.

ONNX `debris` observations populate `debris_score` with confidence multiplied by the
clipped bounding-box image fraction. For example, an 80%-confidence box covering one
quarter of the image scores 0.2. Other classes score zero. Remote observations use the
same proxy only when the endpoint omitted `debris_score`; explicit endpoint values,
including zero, are preserved. This proxy measures visible image extent, not physical
debris count, mass or calibrated floor area. Camera viewpoint, overlapping boxes and
detector errors affect it; cleaning thresholds need calibration and before/after
comparisons need consistent image geometry. A failed observation still cannot imply zero.

`CameraCapture` uses optional OpenCV and exposes a thread-safe one-slot latest-frame
buffer. Old frames are replaced while inference runs, preventing an expanding queue.
A stopped or failed camera must cause runtime heartbeat expiry; never reuse a stale
frame as a new observation. Capture errors propagate through `latest()`.

## ONNX tensor contract

Input: one float32 tensor `images`, fixed shape `[1,3,320,320]`, RGB channel order,
values divided by 255. Direct nearest-neighbor resize to 320×320 is applied; this is
not letterboxing. Output: `[1,N,6]` rows `(x1,y1,x2,y2,confidence,class_id)`, xyxy in
320-pixel coordinates before NMS. Class order:

`clean_floor, debris, cable, clothing, paper, liquid, shoe, large_object, unknown`.

Class IDs are integers; confidence is in [0,1]; all values must be finite. Boxes are
clipped to the image and positive-area boxes scale back to the input frame size.
Class-aware confidence-ranked NMS applies configured IoU and confidence thresholds.
Unknown tensor contracts fail. Raw Ultralytics `[1,4+C,N]` outputs are incompatible.
`python -m ml.export_onnx` wraps trained YOLOv8/v11 outputs to this contract. The
wrapper performs xywh-to-xyxy conversion and class-score selection, leaving NMS to
the provider. It does not download weights. Export requires the optional training
runtime, torch/ONNX, an actual trained checkpoint, and deployment smoke testing.
Ultralytics training augmentation/letterbox differs from direct inference resize;
measure this preprocessing choice on held-out data before accepting a checkpoint.

## Calibrated floor geometry

`FloorProjector(K, camera_to_robot, image_size=(width,height))` takes calibrated
intrinsics and a rigid homogeneous optical-to-robot transform. Optical axes are
x right, y down, z forward; robot axes are x forward, y left, z up. Translation
includes positive camera height above the flat robot z=0 floor. Undistort images
before projection if your lens has distortion. This implementation assumes a flat
floor and does not invent depth or handle stairs/sloped terrain.

`project_pixel(u,v,Pose(...))` intersects the ray with z=0 and rotates/translates
into map meters. Pixels outside the image, rays at/above the horizon, intersections
behind the robot or beyond `max_distance_m` are rejected. `project_detection`
projects the bounding-box bottom center and returns a copied detection with map
position or `None`. Bounding-box floor contact is an approximation that needs real
validation for cables, shoes and objects that obscure the contact point. The YAML
reference intentionally contains no pretend calibration; projection must remain
disabled until measured calibration is supplied.

## FloorMess collection and annotation

Install optional `vision` dependencies for image/video commands. From repository root:

```sh
python -m tools.floormess record datasets/raw/session01.mp4 --seconds 60
python -m tools.floormess extract datasets/raw/session01.mp4 datasets/session01 --group homeA-roomA-session01 --every-s 1
python -m tools.floormess dedup datasets/session01/manifest.jsonl datasets/session01/dedup.jsonl --distance-threshold 0.02
python -m tools.floormess validate datasets/all/manifest.jsonl
python -m tools.floormess visualize image.png labels.txt preview.png
python -m tools.floormess split datasets/all/manifest.jsonl datasets/all/split.json --seed 42
python -m tools.floormess export datasets/all/manifest.jsonl datasets/export --seed 42
```

Extraction creates RGB images and manifest rows with `id`, `group`, `image`, `label`
and video-relative `timestamp`. **It does not create annotation files.** Annotate
all extracted images. An existing empty `.txt` explicitly marks an inspected negative;
a missing label means unannotated and blocks export. YOLO detection labels must have
five fields: integer class ID, normalized center x/y, width/height. Nonfinite numbers,
unknown classes, zero-area boxes and out-of-image bounds fail validation.

Merge manifests with globally unique IDs and paths relative to their new manifest
location. Choose group IDs to encompass correlated room/session/household footage;
never assign adjacent frames independent groups. Grouped deterministic train/val/test
splits use whole groups and require at least three independent groups by default.
Dedup, split and export compare images globally using exact decoded RGB pixels plus a
32×32 local RGB mean/min/max signature. Distance is the maximum absolute normalized
feature difference; the default 0.02 tolerates small exposure/compression differences,
while local extrema help retain thin changed cables that a global mean hash can erase.
`--distance-threshold 0` selects exact-pixel comparisons only; larger values are more
aggressive. Only matching image dimensions are compared approximately.

Exact duplicates with conflicting annotations reject preparation. Similar examples
with identical labels can be removed, but cable-positive examples are automatically
retained for manual review unless pixel-identical. Differing annotations are also
retained. All matched session groups are linked before splitting, including retained
cable examples, preventing known visual matches and connected similarity chains from
crossing split boundaries. This can reduce the number of independent groups below the
minimum and correctly stop export. Unannotated frames lack cable protection, so annotate
and review them before accepting removal. Dedup/split write `.review.json` sidecars;
export writes `dedup-review.json` listing matches and removals. These signatures are
heuristics and cannot guarantee detection of every near-duplicate or preserve every
subtle cable. Inspect the review output and use broader room/household groups for honest
generalization. Split proportions approximate group counts, not frame counts.

## Training and evaluation

Provision an authorized remote GPU environment with the training extras. Copy the
exported dataset and an explicitly obtained initialization checkpoint there. Nothing
here provisions a cloud instance, bills a provider, or downloads trained weights.

```sh
python -m ml.train --weights /data/authorized-init.pt --data /data/floormess/data.yaml --output /data/runs --device 0 --epochs 100
python -m ml.export_onnx --weights /data/runs/floormess/weights/best.pt --output /data/floor320.onnx
python -m tools.benchmark_models --model /data/floor320.onnx --samples /data/heldout.jsonl --output /data/results/floor320
```

Benchmark sample rows have exactly `image_id`, `image` (relative path), and `truth`:
`[{"class_name":"cable","bbox":[x1,y1,x2,y2]}]`. Truth uses original-image pixels.
Only held-out frames should be passed. Reports include JSON and Markdown precision,
recall, mean IoU of matched boxes, per-class TP/FP/FN, cable false negatives,
inference latency mean/p50/p95 after warmup, model file size, Python allocation peak,
and total-process RSS high-water mark. Native ONNX allocations are not measured by
tracemalloc; RSS includes them and other process memory. Metrics use greedy
confidence-ranked, class-aware one-to-one matching at IoU≥0.5. Undefined denominators
are `null`, not fictitious perfect scores. No mAP, deployment FPS, accuracy or cable
safety guarantee is claimed before running actual evaluation on the target device.

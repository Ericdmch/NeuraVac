"""Wrap a trained Ultralytics YOLOv8/v11 detector into the explicit edge contract."""

import argparse
import json
from pathlib import Path

from neuravac_core.perception.providers import CLASSES


def export_model(weights: Path, output: Path):
    if not weights.is_file():
        raise FileNotFoundError(f"Trained local checkpoint required: {weights}")
    if output.exists():
        raise FileExistsError(output)
    import torch
    from ultralytics import YOLO

    loaded = YOLO(str(weights))
    if [loaded.names.get(i) for i in range(len(CLASSES))] != list(CLASSES) or len(
        loaded.names
    ) != len(CLASSES):
        raise ValueError("Checkpoint class order differs from FloorMess")
    model = loaded.model.cpu().eval()

    class ContractDetector(torch.nn.Module):
        def __init__(self, detector):
            super().__init__()
            self.detector = detector

        def forward(self, images):
            raw = self.detector(images)
            raw = raw[0] if isinstance(raw, tuple) else raw
            # YOLOv8/v11: B,(xywh + class probabilities),N; excludes objectness.
            rows = raw.transpose(1, 2)
            xy, wh = rows[..., :2], rows[..., 2:4]
            score, class_id = rows[..., 4:].max(dim=-1)
            return torch.cat(
                (
                    xy - wh / 2,
                    xy + wh / 2,
                    score.unsqueeze(-1),
                    class_id.to(score.dtype).unsqueeze(-1),
                ),
                dim=-1,
            )

    wrapper = ContractDetector(model)
    sample = torch.zeros(1, 3, 320, 320)
    with torch.no_grad():
        raw = model(sample)
        raw = raw[0] if isinstance(raw, tuple) else raw
        if raw.ndim != 3 or raw.shape[1] != 4 + len(CLASSES):
            raise ValueError("Only YOLOv8/v11 raw B,(4+C),N output is supported")
        result = wrapper(sample)
        if not torch.isfinite(result).all():
            raise ValueError("Nonfinite export output")
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        wrapper,
        sample,
        str(output),
        input_names=["images"],
        output_names=["detections"],
        opset_version=17,
        dynamo=False,
        dynamic_axes=None,
    )
    output.with_suffix(".contract.json").write_text(
        json.dumps(
            {
                "input": [1, 3, 320, 320],
                "dtype": "float32",
                "color": "RGB",
                "normalization": "divide by 255",
                "resize": "nearest direct 320x320",
                "output": "[1,N,6] x1,y1,x2,y2,confidence,class_id in 320-pixel coordinates; no NMS",
                "classes": list(CLASSES),
                "checkpoint": str(weights),
            },
            indent=2,
        )
        + "\n"
    )
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(export_model(args.weights, args.output))


if __name__ == "__main__":
    main()

"""Run on an explicitly provisioned remote GPU; never auto-download weights."""

import argparse
from pathlib import Path

import yaml

from neuravac_core.perception.providers import CLASSES


def train(
    weights: Path, data: Path, output: Path, epochs: int = 100, device: str = "0", seed: int = 42
):
    if not weights.is_file():
        raise FileNotFoundError(
            f"Provide an existing authorized local initialization checkpoint: {weights}"
        )
    if not data.is_file():
        raise FileNotFoundError(data)
    if epochs <= 0:
        raise ValueError("epochs must be positive")
    config = yaml.safe_load(data.read_text())
    names = config.get("names")
    if isinstance(names, dict):
        names = [names.get(i) for i in range(len(CLASSES))]
    if names != list(CLASSES):
        raise ValueError("Training classes must exactly match the FloorMess contract in order")
    from ultralytics import YOLO

    model = YOLO(str(weights))
    return model.train(
        data=str(data),
        imgsz=320,
        epochs=epochs,
        device=device,
        seed=seed,
        deterministic=True,
        project=str(output),
        name="floormess",
        exist_ok=False,
        pretrained=True,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--device", default="0")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    train(args.weights, args.data, args.output, args.epochs, args.device, args.seed)


if __name__ == "__main__":
    main()

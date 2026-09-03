"""Immutable r006 asset and split preflight; does not open test images."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


MODELS = {
    "oriented_rcnn_r50": {
        "config": "baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/cell06_orcnn_hrsc_3x_sgd_lr020.py",
        "checkpoint": "baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth",
        "declared_strides": [4, 8, 16, 32],
    },
    "rotated_rtmdet_m": {
        "config": "baseline_rotated_rtmdet_m_fpn_9x_le90/HRSC_trainval_test/config.py",
        "checkpoint": "baseline_rotated_rtmdet_m_fpn_9x_le90/HRSC_trainval_test/best_mAP_9065_epoch_32.pth",
        "declared_strides": [8, 16, 32],
    },
}


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--pth-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    trainval = _ids(args.dataset / "splits/trainval.txt")
    test = _ids(args.dataset / "splits/test.txt")
    overlap = sorted(set(trainval) & set(test))
    payload = {
        "protocol": "r006-preflight-v1",
        "dataset": str(args.dataset.resolve()),
        "trainval_images": len(trainval),
        "test_images": len(test),
        "split_overlap": overlap,
        "models": {},
        "test_unopened": True,
    }
    for name, spec in MODELS.items():
        config = args.pth_root / spec["config"]
        checkpoint = args.pth_root / spec["checkpoint"]
        if not config.is_file() or not checkpoint.is_file():
            raise FileNotFoundError(f"missing r006 asset for {name}: {config} / {checkpoint}")
        payload["models"][name] = {
            "config": str(config), "config_sha256": _hash(config),
            "checkpoint": str(checkpoint), "checkpoint_sha256": _hash(checkpoint),
            "declared_input_pixel_strides": spec["declared_strides"],
        }
    if overlap:
        raise RuntimeError(f"official split overlap: {overlap[:5]}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

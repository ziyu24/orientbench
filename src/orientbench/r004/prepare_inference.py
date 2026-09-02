"""Prepare a frozen r004 full-image intervention and MMRotate inference config.

This script never reads test annotations for calibration.  It only materialises
the requested split's images and emits a runtime config; inference itself is
run by the standard MMRotate test entry point through cqc-fabric.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import cv2

from .observability import corrupt


MODELS = {
    "oriented_rcnn_r50": {
        "config": "baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/cell06_orcnn_hrsc_3x_sgd_lr020.py",
        "checkpoint": "baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth",
    },
    "rotated_rtmdet_m": {
        "config": "baseline_rotated_rtmdet_m_fpn_9x_le90/HRSC_trainval_test/config.py",
        "checkpoint": "baseline_rotated_rtmdet_m_fpn_9x_le90/HRSC_trainval_test/best_mAP_9065_epoch_32.pth",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _link(target: Path, name: Path) -> None:
    target = target.resolve()
    if name.is_symlink():
        if name.resolve() == target:
            return
        # This entry is exclusively inside this run's generated adapter.
        name.unlink()
    elif name.exists():
        raise RuntimeError(f"refuse to replace existing adapter entry: {name}")
    name.symlink_to(target)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run-root", required=True, type=Path)
    p.add_argument("--dataset-root", required=True, type=Path)
    p.add_argument("--pth-root", required=True, type=Path)
    p.add_argument("--model", required=True, choices=MODELS)
    p.add_argument("--split", required=True, choices=("trainval", "test"))
    p.add_argument("--corruption", default="clean", choices=("clean", "blur", "downsample"))
    p.add_argument("--dose", type=float, default=0.0)
    args = p.parse_args()
    if args.corruption == "clean" and args.dose != 0:
        raise ValueError("clean requires dose=0")
    if args.corruption != "clean" and args.dose <= 0:
        raise ValueError("corruption requires positive dose")
    ids = [x.strip() for x in (args.dataset_root / "splits" / f"{args.split}.txt").read_text().splitlines() if x.strip()]
    label = "clean" if args.corruption == "clean" else f"{args.corruption}_{args.dose:g}"
    root = (args.run_root / "inference" / args.split / args.model / label).resolve()
    shared_images = (args.run_root / "interventions" / args.split / label / "images").resolve()
    shared_images.parent.mkdir(parents=True, exist_ok=True)
    if args.corruption == "clean":
        # Keep the data canonical: a symlink, not a project-local data copy.
        _link(args.dataset_root / "images", shared_images)
    else:
        shared_images.mkdir(parents=True, exist_ok=True)
        for image_id in ids:
            out = shared_images / f"{image_id}.bmp"
            if out.exists():
                continue
            inp = cv2.imread(str(args.dataset_root / "images" / f"{image_id}.bmp"), cv2.IMREAD_COLOR)
            if inp is None:
                raise RuntimeError(f"cannot read source image {image_id}")
            if not cv2.imwrite(str(out), corrupt(inp, args.corruption, args.dose)):
                raise RuntimeError(f"cannot write intervention image {out}")
    adapter = root / "adapter"
    (adapter / "FullDataSet").mkdir(parents=True, exist_ok=True)
    _link(shared_images, adapter / "FullDataSet" / "AllImages")
    _link(args.dataset_root / "annfiles", adapter / "FullDataSet" / "Annotations")
    _link(args.dataset_root / "splits", adapter / "ImageSets")
    from mmengine.config import Config
    spec = MODELS[args.model]
    base = args.pth_root / spec["config"]
    ckpt = args.pth_root / spec["checkpoint"]
    cfg = Config.fromfile(base)
    dataset = cfg.test_dataloader.dataset
    dataset.data_root = str(adapter)
    dataset.ann_file = f"ImageSets/{args.split}.txt"
    dataset.data_prefix.sub_data_root = "FullDataSet/"
    dataset.test_mode = True
    cfg.work_dir = str(root / "work")
    cfg.launcher = "none"
    runtime_cfg = root / "runtime_config.py"
    cfg.dump(runtime_cfg)
    manifest = {"model": args.model, "split": args.split, "corruption": args.corruption, "dose": args.dose,
                "images": len(ids), "checkpoint_sha256": sha256(ckpt), "base_config_sha256": sha256(base),
                "runtime_config": str(runtime_cfg), "checkpoint": str(ckpt)}
    (root / "RUN.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()

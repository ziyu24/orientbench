#!/usr/bin/env python3
"""Run frozen r014 identity/hflip/vflip forward passes.

Runtime configs and prediction dumps are written only below the gitignored
orientbench_r014 persistent-artifact namespace.  No detector weights change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r014"
ENV = Path("/home/rspip/anaconda3/envs/mr_dev1x")
TEST = ENV / "lib/python3.10/site-packages/mmdet/.mim/tools/test.py"
FAIR_BASE = Path(
    "/home/rspip/cqc/pro/study/pth_data/"
    "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/"
    "FAIR1M_train_only_val/config.py"
)
FAIR_CKPT = FAIR_BASE.parent / "best_mAP_3462_epoch_12.pth"
FAIR_IMAGES = Path("/home/rspip/cqc/data/dataset/fair1m1.0/split/val/images")
FAIR_ANNS = ROOT / "top_journal_v3_reaudit_055/data_prep/FAIR1M_val20/annfiles_dotaformat"
DIOR_IMAGES = ROOT / "top_journal_v3_reaudit_055/data_prep/DIOR/dotaformat_images/test"
DIOR_ANNS = ROOT / "top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test"
DIOR_UNITS = {
    "dior22": (
        "/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py",
        "/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth",
    ),
    "dior3": (
        "/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/cell03_orcnn_dior_sgd_lr020.py",
        "/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/best_dota_mAP_epoch_11.pth",
    ),
    "dior61": (
        "/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py",
        "/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/best_mAP_5489_epoch_32.pth",
    ),
}
HRSC_BASE = Path("/home/rspip/cqc/pro/study/third_party/ai4rs/projects/LSKNet/configs/lsk_s_fpn_3x_hrsc_le90.py")
HRSC_CKPT = Path("/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_lsknet_s_fpn_3x_le90/HRSC_trainval_test/best_mAP_epoch_33.pth")
HRSC_ROOT = Path("/home/rspip/cqc/data/dataset/HRSC2016")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def config_text(view: str, output: Path, base: Path = FAIR_BASE,
                checkpoint: Path = FAIR_CKPT, images: Path = FAIR_IMAGES,
                annotations: Path = FAIR_ANNS, image_suffix: str = "png",
                scale: tuple[int, int] = (1024, 1024)) -> str:
    flip = ""
    if view != "identity":
        direction = "horizontal" if view == "hflip" else "vertical"
        flip = f"    dict(type='mmdet.RandomFlip', prob=1.0, direction='{direction}'),\n"
    pipeline = (
        "[\n"
        "    dict(type='mmdet.LoadImageFromFile', backend_args=None),\n"
        f"    dict(type='mmdet.Resize', scale={scale!r}, keep_ratio=True),\n"
        f"{flip}"
        "    dict(type='mmdet.PackDetInputs', meta_keys=(\n"
        "        'img_id','img_path','ori_shape','img_shape','scale_factor',\n"
        "        'flip','flip_direction')),\n"
        "]"
    )
    return f"""_base_ = [{str(base)!r}]

test_dataloader = dict(
    batch_size=1,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type='DOTADataset',
        data_root={str(images)!r},
        ann_file={str(annotations)!r},
        data_prefix=dict(img_path=''),
        img_suffix={image_suffix!r},
        test_mode=True,
        filter_cfg=None,
        pipeline={pipeline}))
test_evaluator = dict(
    _delete_=True,
    type='mmdet.DumpDetResults',
    out_file_path={str(output)!r})
load_from = {str(checkpoint)!r}
work_dir = {str(RUNTIME / ('work_dirs/' + output.parent.name))!r}
"""


def prepare() -> dict:
    if not FAIR_BASE.is_file() or not FAIR_CKPT.is_file():
        raise FileNotFoundError("frozen FAIR config/checkpoint unavailable")
    images = sorted(FAIR_IMAGES.glob("*.png"))
    anns = sorted(FAIR_ANNS.glob("*.txt"))
    if len(images) != 4362 or len(anns) != 4362:
        raise RuntimeError(f"FAIR full universe mismatch: images={len(images)} anns={len(anns)}")
    if {p.stem for p in images} != {p.stem for p in anns}:
        raise RuntimeError("FAIR image/annotation ID sets differ")
    cfg_dir = RUNTIME / "configs/fair24"
    pred_dir = RUNTIME / "raw/fair24"
    log_dir = RUNTIME / "logs/fair24"
    for path in (cfg_dir, pred_dir, log_dir, RUNTIME / "work_dirs/fair24"):
        path.mkdir(parents=True, exist_ok=True)
    configs = {}
    for view in ("identity", "hflip", "vflip"):
        output = pred_dir / f"{view}.pkl"
        cfg = cfg_dir / f"fair24_{view}.py"
        cfg.write_text(config_text(view, output), encoding="utf-8")
        configs[view] = {"config": str(cfg), "output": str(output)}
    registry = {
        "schema_version": "r014_fair_forward_v1",
        "dataset": "FAIR1M-v1.0",
        "unit": "FAIR1M-v1.0/24",
        "images": len(images),
        "image_set_sha256": hashlib.sha256(("\n".join(p.stem for p in images) + "\n").encode()).hexdigest(),
        "config": str(FAIR_BASE),
        "config_sha256": sha256(FAIR_BASE),
        "checkpoint": str(FAIR_CKPT),
        "checkpoint_sha256": sha256(FAIR_CKPT),
        "views": configs,
    }
    (RUNTIME / "fair_forward_registry.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return registry


def prepare_dior(unit: str) -> dict:
    base = Path(DIOR_UNITS[unit][0])
    checkpoint = Path(DIOR_UNITS[unit][1])
    images = sorted(DIOR_IMAGES.glob("*.jpg"))
    anns = sorted(DIOR_ANNS.glob("*.txt"))
    if not base.is_file() or not checkpoint.is_file():
        raise FileNotFoundError(f"frozen {unit} config/checkpoint unavailable")
    if len(images) != 11738 or len(anns) != 11738:
        raise RuntimeError(f"DIOR full universe mismatch: images={len(images)} anns={len(anns)}")
    if {p.stem for p in images} != {p.stem for p in anns}:
        raise RuntimeError("DIOR image/annotation ID sets differ")
    cfg_dir = RUNTIME / f"configs/{unit}"
    pred_dir = RUNTIME / f"raw/{unit}"
    log_dir = RUNTIME / f"logs/{unit}"
    for path in (cfg_dir, pred_dir, log_dir, RUNTIME / f"work_dirs/{unit}"):
        path.mkdir(parents=True, exist_ok=True)
    configs = {}
    for view in ("identity", "hflip", "vflip"):
        output = pred_dir / f"{view}.pkl"
        cfg = cfg_dir / f"{unit}_{view}.py"
        scale = (800, 800) if unit == "dior61" else (1024, 1024)
        cfg.write_text(config_text(view, output, base, checkpoint, DIOR_IMAGES,
                                   DIOR_ANNS, "jpg", scale), encoding="utf-8")
        configs[view] = {"config": str(cfg), "output": str(output)}
    registry = {
        "schema_version": "r014_dior_forward_v1",
        "dataset": "DIOR-R",
        "unit": unit,
        "images": len(images),
        "image_set_sha256": hashlib.sha256(("\n".join(p.stem for p in images) + "\n").encode()).hexdigest(),
        "config": str(base), "config_sha256": sha256(base),
        "checkpoint": str(checkpoint), "checkpoint_sha256": sha256(checkpoint),
        "views": configs,
    }
    (RUNTIME / f"{unit}_forward_registry.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return registry


def prepare_hrsc() -> dict:
    ids = [line.strip() for line in (HRSC_ROOT / "splits/test.txt").read_text().splitlines() if line.strip()]
    if len(ids) != 453 or len(set(ids)) != 453:
        raise RuntimeError(f"HRSC test split mismatch: {len(ids)}/{len(set(ids))}")
    if not HRSC_BASE.is_file() or not HRSC_CKPT.is_file():
        raise FileNotFoundError("frozen HRSC/LSKNet config/checkpoint unavailable")
    cfg_dir = RUNTIME / "configs/hrsc_lsknet"
    pred_dir = RUNTIME / "raw/hrsc_lsknet"
    log_dir = RUNTIME / "logs/hrsc_lsknet"
    for path in (cfg_dir, pred_dir, log_dir, RUNTIME / "work_dirs/hrsc_lsknet"):
        path.mkdir(parents=True, exist_ok=True)
    configs = {}
    for view in ("identity", "hflip", "vflip"):
        flip = ""
        if view != "identity":
            direction = "horizontal" if view == "hflip" else "vertical"
            flip = f"    dict(type='mmdet.RandomFlip', prob=1.0, direction='{direction}'),\n"
        output = pred_dir / f"{view}.pkl"
        cfg = cfg_dir / f"hrsc_lsknet_{view}.py"
        cfg.write_text(f"""_base_ = [{str(HRSC_BASE)!r}]
test_dataloader = dict(
    batch_size=1, num_workers=4, persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type='HRSCDataset', data_root={str(HRSC_ROOT)!r}, ann_file='splits/test.txt',
        img_subdir='images', ann_subdir='annfiles',
        data_prefix=dict(sub_data_root=''),
        test_mode=True,
        pipeline=[
            dict(type='mmdet.LoadImageFromFile', backend_args=None),
            dict(type='mmdet.Resize', scale=(800, 800), keep_ratio=True),
{flip}            dict(type='mmdet.PackDetInputs', meta_keys=(
                'img_id','img_path','ori_shape','img_shape','scale_factor','flip','flip_direction'))]))
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path={str(output)!r})
load_from = {str(HRSC_CKPT)!r}
work_dir = {str(RUNTIME / 'work_dirs/hrsc_lsknet')!r}
""", encoding="utf-8")
        configs[view] = {"config": str(cfg), "output": str(output)}
    registry = {
        "schema_version": "r014_hrsc_forward_v1", "dataset": "HRSC2016",
        "unit": "HRSC2016/LSKNet", "images": 453, "image_set_sha256": hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest(),
        "config": str(HRSC_BASE), "config_sha256": sha256(HRSC_BASE),
        "checkpoint": str(HRSC_CKPT), "checkpoint_sha256": sha256(HRSC_CKPT), "views": configs,
    }
    (RUNTIME / "hrsc_forward_registry.json").write_text(json.dumps(registry, indent=2) + "\n")
    return registry


def validate_dump(path: Path, expected: int = 4362) -> dict:
    with path.open("rb") as handle:
        records = pickle.load(handle)
    ids = [str(row["img_id"]) for row in records]
    if len(ids) != expected or len(set(ids)) != expected:
        raise RuntimeError(f"invalid FAIR dump universe: {path}: {len(ids)}/{len(set(ids))}")
    pred_count = sum(len(row["pred_instances"]["scores"]) for row in records)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "image_records": len(ids),
        "prediction_count": pred_count,
        "zero_prediction_images": sum(len(row["pred_instances"]["scores"]) == 0 for row in records),
    }


def run_view(view: str, registry: dict) -> dict:
    spec = registry["views"][view]
    output = Path(spec["output"])
    if output.is_file():
        return validate_dump(output, int(registry["images"]))
    unit_slug = output.parent.name
    log_path = RUNTIME / "logs" / unit_slug / f"{view}.log"
    command = [
        str(ENV / "bin/python"), "-m", "torch.distributed.run",
        "--nproc_per_node=4", "--master_port", str(29840 + ("identity", "hflip", "vflip").index(view)),
        str(TEST), spec["config"], registry["checkpoint"], "--launcher", "pytorch",
    ]
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": "0,1,2,3",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
    })
    started = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        log.write("command=" + " ".join(command) + "\n")
        log.flush()
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    if completed.returncode:
        raise RuntimeError(f"FAIR {view} forward failed rc={completed.returncode}; log={log_path}")
    result = validate_dump(output, int(registry["images"]))
    result.update({"elapsed_seconds": round(time.time() - started, 3), "log": str(log_path)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--view", choices=("identity", "hflip", "vflip", "all"), default="all")
    parser.add_argument("--unit", choices=("fair24", "dior22", "dior3", "dior61", "hrsc_lsknet"), default="fair24")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if args.unit == "fair24":
        registry = prepare()
    elif args.unit == "hrsc_lsknet":
        registry = prepare_hrsc()
    else:
        registry = prepare_dior(args.unit)
    if args.prepare_only:
        print(json.dumps(registry, ensure_ascii=False))
        return
    views = ("identity", "hflip", "vflip") if args.view == "all" else (args.view,)
    results = {view: run_view(view, registry) for view in views}
    status_path = RUNTIME / f"{args.unit}_forward_status.json"
    previous = json.loads(status_path.read_text()) if status_path.is_file() else {}
    previous.update(results)
    status_path.write_text(json.dumps(previous, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()

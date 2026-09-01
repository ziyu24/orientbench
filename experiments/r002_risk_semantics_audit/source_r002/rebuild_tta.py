#!/usr/bin/env python3
"""Run frozen r002 identity/hflip/vflip forward passes.

Runtime configs and prediction dumps are written only below the gitignored
orientbench_r002 persistent-artifact namespace.  No detector weights change.
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


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r002_gr_eqs_method_admission"
ENV = Path("${PYTHON_ENV}")
TEST = ENV / "lib/python3.10/site-packages/mmdet/.mim/tools/test.py"
FAIR_BASE = Path(
    "${CHECKPOINT_ROOT}/"
    "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/"
    "FAIR1M_train_only_val/config.py"
)
FAIR_CKPT = FAIR_BASE.parent / "best_mAP_3462_epoch_12.pth"
FAIR_IMAGES = Path("${RUNTIME_DATA_ROOT}/fair1m-v1.0/val_tiles_r002")
FAIR_ANNS = Path("${ORIENTBENCH_ROOT}/top_journal_v3_reaudit_055/data_prep/FAIR1M_val20/annfiles_dotaformat")
DIOR_IMAGES = Path("${RUNTIME_DATA_ROOT}/DIOR/images/test")
DIOR_ANNS = Path("${ORIENTBENCH_ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test")
DIOR_UNITS = {
    "dior22": (
        "${CHECKPOINT_ROOT}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py",
        "${CHECKPOINT_ROOT}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth",
    ),
    "dior3": (
        "${CHECKPOINT_ROOT}/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/cell03_orcnn_dior_sgd_lr020.py",
        "${CHECKPOINT_ROOT}/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/best_dota_mAP_epoch_11.pth",
    ),
    "dior61": (
        "${CHECKPOINT_ROOT}/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py",
        "${CHECKPOINT_ROOT}/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/best_mAP_5489_epoch_32.pth",
    ),
}
# The legacy r061 checkpoint config keeps an old relative third_party path
# beside the checkpoint cache.  The semantic base is present on this host;
# use that resolved base only for inference and retain the frozen DIOR model
# overrides below.
DIOR61_PORTABLE_BASE = Path('${THIRD_PARTY_ROOT}/ai4rs/configs/rotated_rtmdet/rotated_rtmdet_s-3x-dota.py')
SODA_IMAGES = Path("${RUNTIME_DATA_ROOT}/SODA-A/val_tiled_r002/images")
SODA_ANNS = Path("${RUNTIME_DATA_ROOT}/SODA-A/val_tiled_r002/annfiles")
SODA_UNITS = {
    "soda23": (
        "${CHECKPOINT_ROOT}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py",
        "${CHECKPOINT_ROOT}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/best_mAP_5991_epoch_12.pth",
    ),
    "soda4": (
        "${CHECKPOINT_ROOT}/baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/config.py",
        "${CHECKPOINT_ROOT}/baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/best_mAP_7295_epoch_09.pth",
    ),
}
HRSC_BASE = Path("${THIRD_PARTY_ROOT}/ai4rs/projects/LSKNet/configs/lsk_s_fpn_3x_hrsc_le90.py")
HRSC_CKPT = Path("${CHECKPOINT_ROOT}/baseline_oriented_rcnn_lsknet_s_fpn_3x_le90/HRSC_trainval_test/best_mAP_epoch_33.pth")
HRSC_ROOT = Path("${RUNTIME_DATA_ROOT}/HRSC2016")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def config_text(view: str, output: Path, base: Path = FAIR_BASE,
                checkpoint: Path = FAIR_CKPT, images: Path = FAIR_IMAGES,
                annotations: Path = FAIR_ANNS, image_suffix: str = "png",
                scale: tuple[int, int] = (1024, 1024), model_override: str = "",
                metainfo_text: str = "") -> str:
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
{model_override}

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
        {metainfo_text}
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
    runtime_base = DIOR61_PORTABLE_BASE if unit == 'dior61' else base
    if not runtime_base.is_file():
        raise FileNotFoundError(f"resolved inference base unavailable: {runtime_base}")
    model_override = ("model = dict(data_preprocessor=dict(pad_size_divisor=32), "
                      "bbox_head=dict(num_classes=20))\n") if unit == 'dior61' else ""
    dior_classes = (
        'airplane', 'airport', 'baseballfield', 'basketballcourt', 'bridge',
        'chimney', 'Expressway-Service-area', 'Expressway-toll-station', 'dam',
        'golffield', 'groundtrackfield', 'harbor', 'overpass', 'ship', 'stadium',
        'storagetank', 'tenniscourt', 'trainstation', 'vehicle', 'windmill',
    ) if unit == 'dior61' else ()
    metainfo_text = f"metainfo=dict(classes={dior_classes!r})," if dior_classes else ""
    configs = {}
    for view in ("identity", "hflip", "vflip"):
        output = pred_dir / f"{view}.pkl"
        cfg = cfg_dir / f"{unit}_{view}.py"
        scale = (800, 800) if unit == "dior61" else (1024, 1024)
        cfg.write_text(config_text(view, output, runtime_base, checkpoint, DIOR_IMAGES,
                                   DIOR_ANNS, "jpg", scale, model_override, metainfo_text), encoding="utf-8")
        configs[view] = {"config": str(cfg), "output": str(output)}
    registry = {
        "schema_version": "r014_dior_forward_v1",
        "dataset": "DIOR-R",
        "unit": unit,
        "images": len(images),
        "image_set_sha256": hashlib.sha256(("\n".join(p.stem for p in images) + "\n").encode()).hexdigest(),
        "config": str(base), "config_sha256": sha256(base),
        "resolved_inference_base": str(runtime_base), "resolved_inference_base_sha256": sha256(runtime_base),
        "checkpoint": str(checkpoint), "checkpoint_sha256": sha256(checkpoint),
        "views": configs,
    }
    (RUNTIME / f"{unit}_forward_registry.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return registry


def prepare_soda(unit: str) -> dict:
    base = Path(SODA_UNITS[unit][0])
    checkpoint = Path(SODA_UNITS[unit][1])
    images = sorted(SODA_IMAGES.glob("*.jpg"))
    anns = sorted(SODA_ANNS.glob("*.txt"))
    if not base.is_file() or not checkpoint.is_file():
        raise FileNotFoundError(f"frozen {unit} config/checkpoint unavailable")
    if len(images) != 22994 or len(anns) != 22994:
        raise RuntimeError(f"SODA full universe mismatch: images={len(images)} anns={len(anns)}")
    if {p.stem for p in images} != {p.stem for p in anns}:
        raise RuntimeError("SODA image/annotation ID sets differ")
    cfg_dir = RUNTIME / f"configs/{unit}"
    pred_dir = RUNTIME / f"raw/{unit}"
    log_dir = RUNTIME / f"logs/{unit}"
    for path in (cfg_dir, pred_dir, log_dir, RUNTIME / f"work_dirs/{unit}"):
        path.mkdir(parents=True, exist_ok=True)
    configs = {}
    for view in ("identity", "hflip", "vflip"):
        output = pred_dir / f"{view}.pkl"
        cfg = cfg_dir / f"{unit}_{view}.py"
        cfg.write_text(config_text(view, output, base, checkpoint, SODA_IMAGES,
                                   SODA_ANNS, "jpg", (1024, 1024)), encoding="utf-8")
        configs[view] = {"config": str(cfg), "output": str(output)}
    registry = {
        "schema_version": "r002_soda_forward_v1", "dataset": "SODA-A", "unit": unit,
        "images": len(images),
        "image_set_sha256": hashlib.sha256(("\n".join(p.stem for p in images) + "\n").encode()).hexdigest(),
        "config": str(base), "config_sha256": sha256(base),
        "checkpoint": str(checkpoint), "checkpoint_sha256": sha256(checkpoint), "views": configs,
    }
    (RUNTIME / f"{unit}_forward_registry.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
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
    selected = env_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    devices = [item for item in selected.split(",") if item]
    if len(devices) != 2:
        raise RuntimeError("r002 G1 requires exactly the two cqc-fabric selected GPUs")
    # Concurrent Core-6 workers use distinct rendezvous ports; view ordinal
    # alone is insufficient once different detector units run in parallel.
    unit_port = {"fair24": 29840, "dior22": 29900, "dior3": 29910,
                 "dior61": 29920, "soda23": 29930, "soda4": 29940}.get(unit_slug)
    if unit_port is None:
        raise RuntimeError(f"no rendezvous port allocated for {unit_slug}")
    command = [
        str(ENV / "bin/python"), "-m", "torch.distributed.run",
        "--nproc_per_node=2", "--master_port", str(unit_port + ("identity", "hflip", "vflip").index(view)),
        str(TEST), spec["config"], registry["checkpoint"], "--out", str(output), "--launcher", "pytorch",
    ]
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": env_visible,
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
    parser.add_argument("--unit", choices=("fair24", "dior22", "dior3", "dior61", "soda23", "soda4", "hrsc_lsknet"), default="fair24")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if args.unit == "fair24":
        registry = prepare()
    elif args.unit == "hrsc_lsknet":
        registry = prepare_hrsc()
    elif args.unit in SODA_UNITS:
        registry = prepare_soda(args.unit)
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

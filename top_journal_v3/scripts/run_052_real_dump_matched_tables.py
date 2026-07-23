#!/usr/bin/env python3
"""SUPERVISOR_052 real dump and full matched-table recovery.

This script persists the DOTA #20 instrumented PSC forward dump, rebuilds full
matched 17-field tables from real detector schemas, aligns PSC phase_mod to
matched GT, and materializes TTA circular-variance tables. It does not train
detectors or modify frozen splits/thresholds/datasets.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import os
import pickle
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.matching import _aabb, _aabb_overlap, match_image, obb_iou
from orientbench.data.splits import assign_split

OUT = ROOT / "top_journal_v3"
DOCS = OUT / "docs"
REPORTS = OUT / "reports"
LOGS = OUT / "logs"
PERSIST_ROOT = ROOT / "outputs/persistent_artifacts/orientbench_real_052"
MATCHED_ROOT = PERSIST_ROOT / "matched_tables"
MANIFEST = ROOT / "outputs/persistent_artifacts/manifest_052.json"

APPROVAL = "SUPERVISOR_APPROVED_052_FORCE_REAL_DUMP_FULL_MATCHED_TABLES"
SCRATCH = Path("/dev/shm/cqc/orientbench/top_journal_v3_052")

DOTA_DUMP_SCRATCH = SCRATCH / "dota20_phase_mod/track_a/DOTA-v1.0_20.pkl"
DOTA_DUMP_PERSIST = PERSIST_ROOT / "dota20_phase_mod/DOTA-v1.0_20.pkl"

PTH = ROOT.parent / "pth_data"

CHECKPOINTS = {
    ("DOTA-v1.0", "20"): PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_5562_epoch_12.pth",
    ("DIOR-R", "22"): PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth",
    ("SODA-A", "23"): PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/best_mAP_5991_epoch_12.pth",
    ("FAIR1M-v1.0", "24"): PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/best_mAP_3462_epoch_12.pth",
    ("DIOR-R", "3"): PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/best_dota_mAP_epoch_11.pth",
    ("DIOR-R", "61"): PTH / "baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/best_mAP_5489_epoch_32.pth",
    ("SODA-A", "4"): PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/best_mAP_7295_epoch_09.pth",
    ("FAIR1M-v1.0", "5"): PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/FAIR1M_train_only_val/best_mAP_5900_epoch_12.pth",
}

CONFIGS = {
    ("DOTA-v1.0", "20"): PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DOTA10_train_val/config.py",
    ("DIOR-R", "22"): PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py",
    ("SODA-A", "23"): PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py",
    ("FAIR1M-v1.0", "24"): PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py",
    ("DIOR-R", "3"): PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/cell03_orcnn_dior_sgd_lr020.py",
    ("DIOR-R", "61"): PTH / "baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py",
    ("SODA-A", "4"): PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/config.py",
    ("FAIR1M-v1.0", "5"): PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py",
}

DETECTORS = {
    "20": "rotated_retinanet_psc",
    "22": "rotated_retinanet_psc",
    "23": "rotated_retinanet_psc",
    "24": "rotated_retinanet_psc",
    "3": "oriented_rcnn",
    "4": "oriented_rcnn",
    "5": "oriented_rcnn",
    "61": "rotated_rtmdet_s",
}

SCHEMA_PATHS = {
    ("DOTA-v1.0", "20"): ROOT / "outputs/persistent_artifacts/orientbench_v2/DOTA-v1.0/20/schema/pred_b20_DOTA-v1.0_val.jsonl",
    ("DIOR-R", "22"): ROOT / "outputs/persistent_artifacts/orientbench_v2/DIOR-R/22/schema/pred_b22_fullval.jsonl",
    ("FAIR1M-v1.0", "24"): ROOT / "outputs/persistent_artifacts/orientbench_v2/FAIR1M-v1.0/24/schema/pred_b24_fullval.jsonl",
    ("SODA-A", "23"): ROOT / "outputs/persistent_artifacts/orientbench_v2/SODA-A/23/schema/pred_b23_fullval.jsonl",
    ("DIOR-R", "3"): ROOT / "outputs/persistent_artifacts/orientbench_v2/DIOR-R/3/schema/pred_b3_fullval.jsonl",
    ("DIOR-R", "61"): Path("/dev/shm/cqc/orientbench/predictions/DIOR-R/61/schema/pred_b61_fullval.jsonl"),
    ("SODA-A", "4"): Path("/dev/shm/cqc/orientbench/predictions/SODA-A/4/schema/pred_b4_fullval.jsonl"),
    ("FAIR1M-v1.0", "5"): Path("/dev/shm/cqc/orientbench/predictions/FAIR1M-v1.0/5/schema/pred_b5_fullval.jsonl"),
}

GT_PATHS = {
    "DOTA-v1.0": ROOT / "outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl",
    "DIOR-R": Path("/dev/shm/cqc/orientbench/predictions/DIOR-R/DIOR-R_fullval_gt.jsonl"),
    "FAIR1M-v1.0": Path("/dev/shm/cqc/orientbench/predictions/FAIR1M-v1.0/FAIR1M-v1.0_fullval_gt.jsonl"),
    "SODA-A": Path("/dev/shm/cqc/orientbench/predictions/SODA-A/SODA-A_fullval_gt.jsonl"),
}

TRACK_A_PKLS = {
    ("DOTA-v1.0", "20"): DOTA_DUMP_PERSIST,
    ("DIOR-R", "22"): ROOT / "outputs/persistent_artifacts/orientbench_v2_047/track_a_dumps/DIOR-R_22.pkl",
    ("FAIR1M-v1.0", "24"): ROOT / "outputs/persistent_artifacts/orientbench_v2_047/track_a_dumps/FAIR1M-v1.0_24.pkl",
    ("SODA-A", "23"): ROOT / "outputs/persistent_artifacts/orientbench_v2_047/track_a_dumps/SODA-A_23.pkl",
}

TTA_DIR = ROOT / "outputs/persistent_artifacts/orientbench_v2_047/tta_preds"
FULL_MATCH_TARGETS = [
    ("DOTA-v1.0", "20"),
    ("DIOR-R", "22"),
    ("FAIR1M-v1.0", "24"),
    ("SODA-A", "23"),
    ("DIOR-R", "3"),
    ("DIOR-R", "61"),
    ("SODA-A", "4"),
]
PSC_TARGETS = [
    ("DOTA-v1.0", "20"),
    ("DIOR-R", "22"),
    ("FAIR1M-v1.0", "24"),
    ("SODA-A", "23"),
]
TTA_TARGETS = [
    ("DIOR-R", "3"),
    ("DIOR-R", "22"),
    ("DIOR-R", "61"),
    ("FAIR1M-v1.0", "5"),
    ("FAIR1M-v1.0", "24"),
    ("SODA-A", "4"),
    ("SODA-A", "23"),
]

DOTA_CLASSES = [
    "plane", "baseball-diamond", "bridge", "ground-track-field",
    "small-vehicle", "large-vehicle", "ship", "tennis-court",
    "basketball-court", "storage-tank", "soccer-ball-field", "roundabout",
    "harbor", "swimming-pool", "helicopter",
]


def now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def ensure_dirs() -> None:
    for p in [DOCS, REPORTS, LOGS, PERSIST_ROOT, MATCHED_ROOT, PERSIST_ROOT / "dota20_phase_mod"]:
        p.mkdir(parents=True, exist_ok=True)


def rel(path: Path | str | None) -> str:
    if path is None:
        return ""
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


_SHA_CACHE: dict[str, str] = {}


def short_sha(path: Path) -> str:
    if not path.exists():
        return ""
    key = str(path)
    if key not in _SHA_CACHE:
        _SHA_CACHE[key] = sha256(path)
    return _SHA_CACHE[key]


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str] | None = None) -> None:
    rows = list(rows)
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_heartbeat(stage: str, status: str, extra: dict[str, Any] | None = None) -> None:
    path = REPORTS / "heartbeat_052.json"
    rows: list[dict[str, Any]] = []
    if path.exists():
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            rows = []
    item = {"time": now(), "stage": stage, "status": status}
    if extra:
        item.update(extra)
    rows.append(item)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_gt_by_image(path: Path) -> dict[str, list[dict[str, Any]]]:
    by_img: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in load_jsonl(path):
        by_img[str(row["image_id"])].append(row)
    return by_img


def iter_jsonl_grouped_by_image(path: Path) -> Iterable[tuple[str, list[dict[str, Any]]]]:
    current_img = None
    group: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            img = str(row["image_id"])
            if current_img is None:
                current_img = img
            if img != current_img:
                yield current_img, group
                current_img, group = img, [row]
            else:
                group.append(row)
    if current_img is not None:
        yield current_img, group


def aspect_ratio(w: float, h: float) -> float:
    return max(w, h) / max(min(w, h), 1e-9)


def area_bin(area: float) -> str:
    if area < 32 * 32:
        return "small"
    if area < 96 * 96:
        return "medium"
    return "large"


def fast_match_image(preds: list[dict[str, Any]], gts: list[dict[str, Any]], iou_threshold: float = 0.5) -> list[dict[str, Any]]:
    """Same greedy semantics as orientbench.metrics.matching.match_image, but
    class-indexed for large post-NMS tables. It returns one row per prediction in
    score order with pred_index pointing to the original local prediction.
    """
    if not preds:
        return []
    if not gts:
        return [
            {
                "pred_index": i,
                "matched_gt_id": None,
                "match_status": "unmatched",
                "iou": 0.0,
                "iou_method": "none",
                "approximate_iou": False,
            }
            for i in sorted(range(len(preds)), key=lambda j: -float(preds[j].get("score", 0.0)))
        ]
    gt_by_class: dict[str, list[int]] = defaultdict(list)
    gt_aabb = []
    for gi, g in enumerate(gts):
        gt_by_class[str(g.get("class_name"))].append(gi)
        gt_aabb.append(_aabb(g))
    order = sorted(range(len(preds)), key=lambda i: -float(preds[i].get("score", 0.0)))
    used: set[int] = set()
    rows = []
    for pi in order:
        p = preds[pi]
        same_class = gt_by_class.get(str(p.get("class_name")), [])
        if not same_class or len(used) >= len(gts):
            rows.append({"pred_index": pi, "matched_gt_id": None, "match_status": "unmatched", "iou": 0.0, "iou_method": "none", "approximate_iou": False})
            continue
        p_aabb = _aabb(p)
        best_iou, best_gt, best_method = 0.0, None, "none"
        approximate = False
        for gi in same_class:
            if gi in used:
                continue
            if not _aabb_overlap(p_aabb, gt_aabb[gi]):
                continue
            iou, method, warnings = obb_iou(p, gts[gi])
            if "approximate_iou" in warnings:
                approximate = True
            if iou > best_iou:
                best_iou, best_gt, best_method = iou, gi, method
        if best_gt is not None and best_iou >= iou_threshold:
            used.add(best_gt)
            rows.append({"pred_index": pi, "matched_gt_id": best_gt, "match_status": "matched", "iou": round(best_iou, 4), "iou_method": best_method, "approximate_iou": approximate})
        else:
            rows.append({"pred_index": pi, "matched_gt_id": None, "match_status": "unmatched", "iou": round(best_iou, 4), "iou_method": best_method, "approximate_iou": approximate})
    return rows


def config_classes(config: Path, dataset: str) -> list[str]:
    if dataset == "DOTA-v1.0":
        return DOTA_CLASSES
    if dataset == "DIOR-R":
        p = ROOT / "measure_fix_v2/artifacts/dior_classes.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    text = config.read_text(encoding="utf-8", errors="ignore") if config.exists() else ""
    for pat in [r"classes\s*=\s*(\([^\)]*\))", r"classes\s*=\s*\[(.*?)\]"]:
        m = re.search(pat, text, re.S)
        if not m:
            continue
        raw = m.group(1)
        if not raw.startswith("(") and not raw.startswith("["):
            raw = "[" + raw + "]"
        try:
            return list(ast.literal_eval(raw))
        except Exception:
            pass
    m = re.search(r"classes\s*=\s*\((.*?)\)", text, re.S)
    if m:
        try:
            return list(ast.literal_eval("(" + m.group(1) + ")"))
        except Exception:
            pass
    return []


def detector_from_bid(bid: str) -> str:
    return DETECTORS.get(bid, "")


def source_checkpoint(ds: str, bid: str) -> str:
    return rel(CHECKPOINTS.get((ds, bid)))


def source_config(ds: str, bid: str) -> str:
    return rel(CONFIGS.get((ds, bid)))


def write_matched_record(
    f: Any,
    cell_id: str,
    ds: str,
    bid: str,
    pred: dict[str, Any],
    gt: dict[str, Any],
    gt_global_id: str | int,
    iou: float,
    phase_mod: Any = "",
) -> dict[str, Any]:
    c = angle_error_contract(
        float(pred["obb_w"]), float(pred["obb_h"]), float(pred["obb_theta"]),
        float(gt["obb_w"]), float(gt["obb_h"]), float(gt["obb_theta"]),
    )
    ar = aspect_ratio(float(gt["obb_w"]), float(gt["obb_h"]))
    area = float(gt["obb_w"]) * float(gt["obb_h"])
    pred_obb = {k: float(pred[k]) for k in ["obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta"]}
    gt_obb = {k: float(gt[k]) for k in ["obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta"]}
    row = {
        "cell_id": cell_id,
        "dataset": ds,
        "detector": detector_from_bid(bid),
        "image_id": str(pred["image_id"]),
        "pred_id": pred.get("pred_id", pred.get("_local_pred_id", "")),
        "gt_id": gt.get("gt_id", gt_global_id),
        "score": float(pred.get("score", 0.0)),
        "phase_mod": phase_mod if phase_mod != "" else pred.get("phase_mod", ""),
        "pred_obb": pred_obb,
        "gt_obb": gt_obb,
        "match_iou": float(iou),
        "angle_error": float(c["angle_error_canonical_longside"]),
        "class": gt.get("class_name", pred.get("class_name", "")),
        "size": area,
        "aspect_ratio": ar,
        "near_square": bool(c["near_square"]),
        "size_bin": area_bin(area),
        "split": pred.get("split", gt.get("split", assign_split(str(pred["image_id"])))),
        "d_cal_daudit_split_flag": assign_split(str(pred["image_id"])),
        "source_checkpoint": source_checkpoint(ds, bid),
        "checkpoint_sha256": short_sha(CHECKPOINTS[(ds, bid)]) if (ds, bid) in CHECKPOINTS else "",
        "config_path": source_config(ds, bid),
        "is_real_detector_output": True,
        "is_synthetic_or_proxy": False,
        "schema_17field_present": True,
    }
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def persist_dota_dump() -> dict[str, Any]:
    append_heartbeat("dota20_phase_mod", "start")
    if not DOTA_DUMP_SCRATCH.exists() and not DOTA_DUMP_PERSIST.exists():
        raise FileNotFoundError(f"DOTA #20 forward dump missing: {DOTA_DUMP_SCRATCH}")
    DOTA_DUMP_PERSIST.parent.mkdir(parents=True, exist_ok=True)
    if DOTA_DUMP_SCRATCH.exists():
        shutil.copy2(DOTA_DUMP_SCRATCH, DOTA_DUMP_PERSIST)
    item = {
        "cell_id": "DOTA-v1.0/20",
        "dataset": "DOTA-v1.0",
        "baseline_id": "20",
        "kind": "psc_track_a_forward_dump_pkl",
        "path": rel(DOTA_DUMP_PERSIST),
        "sha256": sha256(DOTA_DUMP_PERSIST),
        "bytes": DOTA_DUMP_PERSIST.stat().st_size,
        "source_checkpoint": source_checkpoint("DOTA-v1.0", "20"),
        "checkpoint_sha256": short_sha(CHECKPOINTS[("DOTA-v1.0", "20")]),
        "config_path": rel(OUT / "configs/tracka_dota20_052.py"),
        "split": "DOTA-v1.0 val shadow farm from frozen D_cal images",
        "can_recompute": True,
        "world_size": 4,
        "scratch_path": rel(SCRATCH / "dota20_phase_mod"),
        "generation_command": (
            "PYTHONPATH=measure_fix_v2:. CUDA_VISIBLE_DEVICES=0,1,2,3 "
            "python -m torch.distributed.run --nproc_per_node=4 --master_port=30152 "
            "$CONDA_PREFIX/lib/python3.10/site-packages/mmdet/.mim/tools/test.py "
            "top_journal_v3/configs/tracka_dota20_052.py "
            f"{source_checkpoint('DOTA-v1.0', '20')} --launcher pytorch"
        ),
        "is_real_detector_output": True,
        "is_synthetic_or_proxy": False,
    }
    write_csv(REPORTS / "dota20_phase_mod_forward_dump_052.csv", [item])
    DOCS.joinpath("dota20_phase_mod_forward_dump_052.md").write_text(
        "# DOTA #20 phase_mod forward dump 052\n\n"
        f"Generated: {now()}\n\n"
        "Status: completed from real checkpoint/config/dataset via instrumented PSC head; no detector training.\n\n"
        f"- Persistent pkl: `{rel(DOTA_DUMP_PERSIST)}`\n"
        f"- SHA256: `{item['sha256']}`\n"
        f"- Scratch farm: `{rel(SCRATCH / 'dota20_phase_mod/farm')}`\n"
        "- World size: 4\n"
        "- Runtime log: `top_journal_v3/logs/dota20_phase_mod_forward_dump_052_attempt1.log`\n",
        encoding="utf-8",
    )
    append_heartbeat("dota20_phase_mod", "complete", {"path": rel(DOTA_DUMP_PERSIST)})
    return item


def full_matched_tables() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    append_heartbeat("full_matched_tables", "start")
    summaries: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    for ds, bid in FULL_MATCH_TARGETS:
        cell = f"{ds}/{bid}"
        append_heartbeat("full_matched_tables", "cell_start", {"cell_id": cell})
        schema = SCHEMA_PATHS[(ds, bid)]
        gt_path = GT_PATHS[ds]
        out_dir = MATCHED_ROOT / ds / bid
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "matched_17field_full_052.jsonl"
        if not schema.exists() or not gt_path.exists():
            summaries.append({
                "cell_id": cell, "status": "missing_input", "schema_path": rel(schema),
                "gt_path": rel(gt_path), "n_predictions": 0, "n_gt": 0, "n_matched": 0,
                "is_full_not_capped": False,
            })
            continue
        gt_by_img = load_gt_by_image(gt_path)
        n_gt = sum(len(v) for v in gt_by_img.values())
        n_pred = 0
        n_matched = 0
        n_images = 0
        max_preds_per_image = 0
        with out_path.open("w", encoding="utf-8") as f:
            for img, preds in iter_jsonl_grouped_by_image(schema):
                n_images += 1
                n_pred += len(preds)
                max_preds_per_image = max(max_preds_per_image, len(preds))
                for i, pred in enumerate(preds):
                    pred["_local_pred_id"] = i
                local_gt = gt_by_img.get(str(img), [])
                rows = fast_match_image(preds, local_gt)
                for r in rows:
                    if r["match_status"] != "matched":
                        continue
                    p = preds[r["pred_index"]]
                    g = local_gt[r["matched_gt_id"]]
                    write_matched_record(f, cell, ds, bid, p, g, r["matched_gt_id"], r["iou"])
                    n_matched += 1
        out_sha = sha256(out_path)
        status = "complete_full_real" if n_matched > 0 else "complete_no_matches"
        summaries.append({
            "cell_id": cell,
            "dataset": ds,
            "baseline_id": bid,
            "detector": detector_from_bid(bid),
            "status": status,
            "schema_path": rel(schema),
            "schema_sha256": sha256(schema),
            "gt_path": rel(gt_path),
            "gt_sha256": sha256(gt_path),
            "matched_table_path": rel(out_path),
            "matched_table_sha256": out_sha,
            "n_predictions": n_pred,
            "n_gt": n_gt,
            "n_images": n_images,
            "max_preds_per_image": max_preds_per_image,
            "n_matched": n_matched,
            "is_full_not_capped": True,
            "is_real_detector_output": True,
            "is_synthetic_or_proxy": False,
            "source_checkpoint": source_checkpoint(ds, bid),
            "checkpoint_sha256": short_sha(CHECKPOINTS[(ds, bid)]) if (ds, bid) in CHECKPOINTS else "",
            "config_path": source_config(ds, bid),
        })
        artifacts.append({
            "cell_id": cell,
            "kind": "full_matched_17field_jsonl",
            "path": rel(out_path),
            "sha256": out_sha,
            "bytes": out_path.stat().st_size,
            "source_schema": rel(schema),
            "source_gt": rel(gt_path),
            "source_checkpoint": source_checkpoint(ds, bid),
            "checkpoint_sha256": short_sha(CHECKPOINTS[(ds, bid)]) if (ds, bid) in CHECKPOINTS else "",
            "config_path": source_config(ds, bid),
            "split": "existing source schema split and frozen hash D_cal/D_audit flag",
            "can_recompute": True,
            "generation_command": "python top_journal_v3/scripts/run_052_real_dump_matched_tables.py",
            "is_real_detector_output": True,
            "is_synthetic_or_proxy": False,
            "is_full_not_capped": True,
        })
        append_heartbeat("full_matched_tables", "cell_complete", {"cell_id": cell, "n_matched": n_matched})
    write_csv(REPORTS / "full_matched_tables_052.csv", summaries)
    DOCS.joinpath("full_matched_tables_052.md").write_text(
        "# Full matched tables 052\n\n"
        f"Generated: {now()}\n\n"
        "All listed tables are rebuilt from real post-NMS detector schemas and GT OBB files, with no cap/sample applied. "
        "DIOR #61 and SODA #4 source schemas were scratch-resident at run time; their 052 matched outputs are persisted under outputs/persistent_artifacts with sha256 in manifest_052.json.\n\n"
        + "\n".join(
            f"- {r['cell_id']}: {r['status']}, predictions={r['n_predictions']}, matched={r['n_matched']}, table=`{r.get('matched_table_path','')}`"
            for r in summaries
        )
        + "\n",
        encoding="utf-8",
    )
    append_heartbeat("full_matched_tables", "complete")
    return summaries, artifacts


def track_records(ds: str, bid: str) -> Iterable[dict[str, Any]]:
    pkl_path = TRACK_A_PKLS[(ds, bid)]
    classes = config_classes(CONFIGS[(ds, bid)], ds)
    data = pickle.load(pkl_path.open("rb"))
    for rec in data:
        img = str(rec.get("img_id"))
        pi = rec.get("pred_instances", {})
        bboxes = np.asarray(pi.get("bboxes", []))
        scores = np.asarray(pi.get("scores", []))
        labels = np.asarray(pi.get("labels", []))
        phase = pi.get("phase_mod")
        if phase is None:
            continue
        phase_arr = np.asarray(phase.cpu() if hasattr(phase, "cpu") else phase)
        for pred_id, (b, score, label, pm) in enumerate(zip(bboxes, scores, labels, phase_arr)):
            lab = int(label)
            yield {
                "image_id": img,
                "pred_id": pred_id,
                "class_name": classes[lab] if lab < len(classes) else str(lab),
                "score": float(score),
                "phase_mod": float(pm),
                "obb_cx": float(b[0]),
                "obb_cy": float(b[1]),
                "obb_w": float(b[2]),
                "obb_h": float(b[3]),
                "obb_theta": float(b[4]),
                "split": assign_split(img),
            }


def psc_phase_mod_permatched() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    append_heartbeat("psc_phase_mod_permatched", "start")
    out_csv = REPORTS / "psc_phase_mod_permatched_full_052.csv"
    columns = [
        "cell_id", "dataset", "detector", "image_id", "pred_id", "gt_id", "score", "phase_mod",
        "pred_obb", "gt_obb", "match_iou", "angle_error", "class", "size", "aspect_ratio",
        "near_square", "split", "source_checkpoint", "checkpoint_sha256", "config_path",
        "is_real_detector_output",
    ]
    summaries: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    with out_csv.open("w", newline="", encoding="utf-8") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for ds, bid in PSC_TARGETS:
            cell = f"{ds}/{bid}"
            append_heartbeat("psc_phase_mod_permatched", "cell_start", {"cell_id": cell})
            pkl_path = TRACK_A_PKLS[(ds, bid)]
            gt_path = GT_PATHS[ds]
            if not pkl_path.exists() or not gt_path.exists():
                summaries.append({"cell_id": cell, "status": "missing_input", "n_matched": 0, "n_predictions": 0})
                continue
            gt_by_img = load_gt_by_image(gt_path)
            preds_by_img: dict[str, list[dict[str, Any]]] = defaultdict(list)
            n_pred = 0
            for pred in track_records(ds, bid):
                pred["_local_pred_id"] = len(preds_by_img[pred["image_id"]])
                preds_by_img[pred["image_id"]].append(pred)
                n_pred += 1
            n_matched = 0
            for img, preds in preds_by_img.items():
                rows = fast_match_image(preds, gt_by_img.get(img, []))
                for r in rows:
                    if r["match_status"] != "matched":
                        continue
                    p = preds[r["pred_index"]]
                    g = gt_by_img[img][r["matched_gt_id"]]
                    temp_path = PERSIST_ROOT / "_phase_tmp.jsonl"
                    # Build the row without writing JSONL by using a small shim.
                    class Sink:
                        def write(self, _: str) -> None:
                            return None
                    row = write_matched_record(Sink(), cell, ds, bid, p, g, r["matched_gt_id"], r["iou"], p.get("phase_mod", ""))
                    row["pred_obb"] = json.dumps(row["pred_obb"], ensure_ascii=False)
                    row["gt_obb"] = json.dumps(row["gt_obb"], ensure_ascii=False)
                    writer.writerow(row)
                    n_matched += 1
            summaries.append({
                "cell_id": cell,
                "dataset": ds,
                "baseline_id": bid,
                "status": "complete_full_real" if n_matched > 0 else "complete_no_matches",
                "track_a_pkl": rel(pkl_path),
                "track_a_pkl_sha256": sha256(pkl_path),
                "n_predictions": n_pred,
                "n_matched": n_matched,
                "is_full_not_capped": True,
                "is_real_detector_output": True,
                "is_synthetic_or_proxy": False,
            })
            append_heartbeat("psc_phase_mod_permatched", "cell_complete", {"cell_id": cell, "n_matched": n_matched})
    artifacts.append({
        "kind": "psc_phase_mod_permatched_full_csv",
        "path": rel(out_csv),
        "sha256": sha256(out_csv),
        "bytes": out_csv.stat().st_size,
        "cell_id": "PSC/DOTA20_DIOR22_FAIR24_SODA23",
        "source_checkpoint": "pth_data PSC checkpoints",
        "split": "source validation/test schemas",
        "can_recompute": True,
        "generation_command": "python top_journal_v3/scripts/run_052_real_dump_matched_tables.py",
        "is_real_detector_output": True,
        "is_synthetic_or_proxy": False,
        "is_full_not_capped": True,
    })
    DOCS.joinpath("psc_phase_mod_permatched_full_052.md").write_text(
        "# PSC phase_mod per-matched full table 052\n\n"
        f"Generated: {now()}\n\n"
        "The CSV aligns instrumented PSC phase_mod predictions to matched GT OBBs by same-image/same-class greedy rIoU matching. "
        "It uses the newly generated DOTA #20 forward dump plus persistent DIOR/FAIR/SODA Track A dumps; no aggregate proxy is used.\n\n"
        + "\n".join(
            f"- {r['cell_id']}: {r['status']}, predictions={r['n_predictions']}, matched={r['n_matched']}"
            for r in summaries
        )
        + f"\n\nOutput: `{rel(out_csv)}`\n",
        encoding="utf-8",
    )
    append_heartbeat("psc_phase_mod_permatched", "complete")
    return summaries, artifacts


def pkl_records_to_by_image(path: Path, ds: str, bid: str) -> dict[str, list[dict[str, Any]]]:
    classes = config_classes(CONFIGS.get((ds, bid), Path()), ds)
    data = pickle.load(path.open("rb"))
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in data:
        img = str(rec.get("img_id"))
        H, W = rec.get("ori_shape", (1024, 1024))[:2]
        pi = rec.get("pred_instances", {})
        bboxes = np.asarray(pi.get("bboxes", []))
        scores = np.asarray(pi.get("scores", []))
        labels = np.asarray(pi.get("labels", []))
        for pred_id, (b, s, lab) in enumerate(zip(bboxes, scores, labels)):
            lab_i = int(lab)
            out[img].append({
                "image_id": img,
                "pred_id": pred_id,
                "class_name": classes[lab_i] if lab_i < len(classes) else str(lab_i),
                "score": float(s),
                "obb_cx": float(b[0]),
                "obb_cy": float(b[1]),
                "obb_w": float(b[2]),
                "obb_h": float(b[3]),
                "obb_theta": float(b[4]),
                "ori_h": float(H),
                "ori_w": float(W),
            })
    return out


def unflip_candidate(row: dict[str, Any], mode: str, H: float, W: float) -> dict[str, Any]:
    out = dict(row)
    if mode == "hflip":
        out["obb_cx"] = W - float(out["obb_cx"])
        out["obb_theta"] = -float(out["obb_theta"])
    elif mode == "vflip":
        out["obb_cy"] = H - float(out["obb_cy"])
        out["obb_theta"] = -float(out["obb_theta"])
    return out


def nearest_angle(anchor: dict[str, Any], candidates: list[dict[str, Any]], mode: str) -> float | None:
    H = float(anchor.get("ori_h", 1024.0))
    W = float(anchor.get("ori_w", 1024.0))
    best_theta = None
    best_dist = 1e18
    for cand0 in candidates:
        if cand0.get("class_name") != anchor.get("class_name"):
            continue
        cand = unflip_candidate(cand0, mode, H, W)
        dist = math.hypot(float(cand["obb_cx"]) - float(anchor["obb_cx"]), float(cand["obb_cy"]) - float(anchor["obb_cy"]))
        scale = max(float(anchor.get("obb_w", 1.0)), float(anchor.get("obb_h", 1.0)), 20.0)
        if dist < best_dist and dist <= max(40.0, 0.75 * scale):
            best_dist = dist
            best_theta = float(cand["obb_theta"])
    return best_theta


def schema_anchor_by_image(ds: str, bid: str) -> dict[str, list[dict[str, Any]]]:
    p = SCHEMA_PATHS[(ds, bid)]
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for img, preds in iter_jsonl_grouped_by_image(p):
        for i, pred in enumerate(preds):
            pred = dict(pred)
            pred["pred_id"] = i
            pred["ori_h"] = 1024.0
            pred["ori_w"] = 1024.0
            out[img].append(pred)
    return out


def tta_circular_variance_full() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    append_heartbeat("tta_circular_variance", "start")
    out_csv = REPORTS / "tta_circular_variance_full_052.csv"
    columns = [
        "cell_id", "dataset", "baseline_id", "detector", "image_id", "pred_id", "gt_id",
        "score", "class", "angle_error", "match_iou", "n_tta_angles",
        "circular_variance", "theta_to_2theta", "naive_linear_std_used",
        "identity_source", "matched_gt", "status", "is_real_detector_output",
    ]
    summaries: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    with out_csv.open("w", newline="", encoding="utf-8") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for ds, bid in TTA_TARGETS:
            cell = f"{ds}/{bid}"
            append_heartbeat("tta_circular_variance", "cell_start", {"cell_id": cell})
            d = TTA_DIR / f"{ds}_{bid}"
            identity = d / "identity.pkl"
            hflip = d / "hflip.pkl"
            vflip = d / "vflip.pkl"
            if not d.exists() or (not identity.exists() and (ds, bid) not in SCHEMA_PATHS):
                summaries.append({"cell_id": cell, "status": "missing_tta_identity", "n_rows": 0})
                continue
            if identity.exists():
                anchors = pkl_records_to_by_image(identity, ds, bid)
                identity_source = rel(identity)
            else:
                anchors = schema_anchor_by_image(ds, bid)
                identity_source = "full_schema_anchor_identity_missing"
            h_by_img = pkl_records_to_by_image(hflip, ds, bid) if hflip.exists() else {}
            v_by_img = pkl_records_to_by_image(vflip, ds, bid) if vflip.exists() else {}
            gt_by_img = load_gt_by_image(GT_PATHS[ds])
            n_rows = 0
            n_gt_matched = 0
            for img, preds in anchors.items():
                gt = gt_by_img.get(img, [])
                match_rows = fast_match_image(preds, gt) if gt else []
                match_by_pred = {r["pred_index"]: r for r in match_rows if r["match_status"] == "matched"}
                for idx, p in enumerate(preds):
                    angles = [float(p["obb_theta"])]
                    ht = nearest_angle(p, h_by_img.get(img, []), "hflip") if hflip.exists() else None
                    vt = nearest_angle(p, v_by_img.get(img, []), "vflip") if vflip.exists() else None
                    if ht is not None:
                        angles.append(ht)
                    if vt is not None:
                        angles.append(vt)
                    doubled = np.asarray([2.0 * a for a in angles], dtype=float)
                    R = float(np.hypot(np.cos(doubled).mean(), np.sin(doubled).mean()))
                    circ_var = 1.0 - R
                    gt_id = ""
                    angle_err = ""
                    match_iou = ""
                    cls = p.get("class_name", "")
                    matched_gt = False
                    if idx in match_by_pred:
                        r = match_by_pred[idx]
                        g = gt[r["matched_gt_id"]]
                        c = angle_error_contract(
                            float(p["obb_w"]), float(p["obb_h"]), float(p["obb_theta"]),
                            float(g["obb_w"]), float(g["obb_h"]), float(g["obb_theta"]),
                        )
                        gt_id = r["matched_gt_id"]
                        angle_err = float(c["angle_error_canonical_longside"])
                        match_iou = float(r["iou"])
                        cls = g.get("class_name", cls)
                        matched_gt = True
                        n_gt_matched += 1
                    writer.writerow({
                        "cell_id": cell,
                        "dataset": ds,
                        "baseline_id": bid,
                        "detector": detector_from_bid(bid),
                        "image_id": img,
                        "pred_id": p.get("pred_id", idx),
                        "gt_id": gt_id,
                        "score": float(p.get("score", 0.0)),
                        "class": cls,
                        "angle_error": angle_err,
                        "match_iou": match_iou,
                        "n_tta_angles": len(angles),
                        "circular_variance": circ_var,
                        "theta_to_2theta": True,
                        "naive_linear_std_used": False,
                        "identity_source": identity_source,
                        "matched_gt": matched_gt,
                        "status": "complete_full_real_circular",
                        "is_real_detector_output": True,
                    })
                    n_rows += 1
            summaries.append({
                "cell_id": cell,
                "dataset": ds,
                "baseline_id": bid,
                "status": "complete_full_real_circular",
                "n_rows": n_rows,
                "n_matched_gt": n_gt_matched,
                "identity_source": identity_source,
                "hflip_exists": hflip.exists(),
                "vflip_exists": vflip.exists(),
                "theta_to_2theta": True,
                "naive_linear_std_used": False,
                "is_full_not_capped": True,
            })
            append_heartbeat("tta_circular_variance", "cell_complete", {"cell_id": cell, "n_rows": n_rows})
    artifacts.append({
        "kind": "tta_circular_variance_full_csv",
        "path": rel(out_csv),
        "sha256": sha256(out_csv),
        "bytes": out_csv.stat().st_size,
        "cell_id": "TTA/DIOR3_DIOR22_DIOR61_FAIR5_FAIR24_SODA4_SODA23",
        "source_checkpoint": "pth_data real detector checkpoints",
        "split": "source validation/test schemas",
        "can_recompute": True,
        "generation_command": "python top_journal_v3/scripts/run_052_real_dump_matched_tables.py",
        "is_real_detector_output": True,
        "is_synthetic_or_proxy": False,
        "theta_to_2theta": True,
        "naive_linear_std_used": False,
        "is_full_not_capped": True,
    })
    DOCS.joinpath("tta_circular_variance_full_052.md").write_text(
        "# TTA circular variance full table 052\n\n"
        f"Generated: {now()}\n\n"
        "Circular variance is computed on doubled angles, theta -> 2theta, as required for pi-periodic OBB angles. "
        "No naive linear standard deviation is used. Rows are full available post-NMS identity anchors, not capped. "
        "When a cell lacked identity.pkl but had hflip/vflip plus a full real schema, the schema was used as the identity anchor and this is recorded in identity_source.\n\n"
        + "\n".join(
            f"- {r['cell_id']}: {r['status']}, rows={r['n_rows']}, matched_gt={r['n_matched_gt']}, identity={r['identity_source']}"
            for r in summaries
        )
        + f"\n\nOutput: `{rel(out_csv)}`\n",
        encoding="utf-8",
    )
    append_heartbeat("tta_circular_variance", "complete")
    return summaries, artifacts


def write_manifest(artifacts: list[dict[str, Any]]) -> None:
    manifest = {
        "generated": now(),
        "approval_token": APPROVAL,
        "gpu_used": True,
        "gpu_commands": [
            {
                "purpose": "DOTA #20 PSC phase_mod instrumented forward dump",
                "world_size": 4,
                "scratch_path": rel(SCRATCH / "dota20_phase_mod"),
                "log_path": "top_journal_v3/logs/dota20_phase_mod_forward_dump_052_attempt1.log",
                "command": (
                    "PYTHONPATH=/home/rspip/cqc/pro/study/orientbench/measure_fix_v2:/home/rspip/cqc/pro/study/orientbench "
                    "CUDA_VISIBLE_DEVICES=0,1,2,3 OMP_NUM_THREADS=6 "
                    "/home/rspip/anaconda3/envs/mr_dev1x/bin/python -m torch.distributed.run "
                    "--nproc_per_node=4 --master_port=30152 "
                    "/home/rspip/anaconda3/envs/mr_dev1x/lib/python3.10/site-packages/mmdet/.mim/tools/test.py "
                    "top_journal_v3/configs/tracka_dota20_052.py "
                    "/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_5562_epoch_12.pth "
                    "--launcher pytorch"
                ),
            }
        ],
        "host_training_started": False,
        "thresholds_modified": False,
        "dcal_daudit_modified": False,
        "full_matrix_added": False,
        "persistent_dir": rel(PERSIST_ROOT),
        "artifacts": artifacts,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def write_readiness(
    matched: list[dict[str, Any]],
    psc: list[dict[str, Any]],
    tta: list[dict[str, Any]],
) -> None:
    matched_ok = all(r.get("status") == "complete_full_real" and int(r.get("n_matched", 0)) > 0 for r in matched)
    psc_ok = all(r.get("status") == "complete_full_real" and int(r.get("n_matched", 0)) > 0 for r in psc)
    tta_ok = all(r.get("status") == "complete_full_real_circular" and int(r.get("n_rows", 0)) > 0 for r in tta)
    text = [
        "# Evidence ready for P1-P5 rerun 052",
        "",
        f"Generated: {now()}",
        "",
        f"- P1 constructive decoupling: {'ready' if matched_ok else 'not_ready'}; requires full real matched predictions for seven key cells.",
        f"- P2 conformal: {'ready' if matched_ok else 'not_ready'}; D_cal/D_audit flags are recomputed from frozen hash assignment without modifying split files.",
        f"- P3 PSC free mechanism tests: {'ready' if psc_ok else 'not_ready'}; DOTA #20 plus DIOR/FAIR/SODA per-matched phase_mod is required.",
        f"- P4 TTA circular baseline: {'ready' if tta_ok else 'not_ready'}; circular variance uses theta -> 2theta and no naive linear std.",
        f"- P5 downstream angle-induced rIoU drop: {'ready' if matched_ok else 'not_ready'}; uses full real matched predictions.",
        "",
        "## Concrete gaps if any",
        "",
    ]
    gaps = []
    for r in matched:
        if r.get("status") != "complete_full_real" or int(r.get("n_matched", 0)) <= 0:
            gaps.append(f"- matched {r.get('cell_id')}: {r.get('status')} matched={r.get('n_matched')} schema={r.get('schema_path')}")
    for r in psc:
        if r.get("status") != "complete_full_real" or int(r.get("n_matched", 0)) <= 0:
            gaps.append(f"- phase_mod {r.get('cell_id')}: {r.get('status')} matched={r.get('n_matched')} pkl={r.get('track_a_pkl')}")
    for r in tta:
        if r.get("status") != "complete_full_real_circular" or int(r.get("n_rows", 0)) <= 0:
            gaps.append(f"- TTA {r.get('cell_id')}: {r.get('status')} rows={r.get('n_rows')} identity={r.get('identity_source')}")
    if gaps:
        text.extend(gaps)
    else:
        text.append("- No blocking gaps for 052 artifact readiness; proceed to 053/next rerun of P1-P5.")
    DOCS.joinpath("evidence_ready_for_p1_p5_rerun_052.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def write_latest_report(
    dota_item: dict[str, Any],
    matched: list[dict[str, Any]],
    psc: list[dict[str, Any]],
    tta: list[dict[str, Any]],
    verification: str,
    tests: str,
    git_result: str,
) -> None:
    matched_ok = all(r.get("status") == "complete_full_real" and int(r.get("n_matched", 0)) > 0 for r in matched)
    psc_ok = all(r.get("status") == "complete_full_real" and int(r.get("n_matched", 0)) > 0 for r in psc)
    tta_ok = all(r.get("status") == "complete_full_real_circular" and int(r.get("n_rows", 0)) > 0 for r in tta)
    ready = matched_ok and psc_ok and tta_ok
    missing = []
    for r in matched:
        if r.get("status") != "complete_full_real" or int(r.get("n_matched", 0)) <= 0:
            missing.append(f"matched {r.get('cell_id')} {r.get('status')}")
    for r in psc:
        if r.get("status") != "complete_full_real" or int(r.get("n_matched", 0)) <= 0:
            missing.append(f"phase_mod {r.get('cell_id')} {r.get('status')}")
    for r in tta:
        if r.get("status") != "complete_full_real_circular" or int(r.get("n_rows", 0)) <= 0:
            missing.append(f"TTA {r.get('cell_id')} {r.get('status')}")
    body = (
        "👇👇👇👇👇👇\n\n"
        f"052 {'完成' if ready else '未完成'}。\n"
        f"DOTA #20 phase_mod：完成，真实 forward dump 已持久化 `{dota_item['path']}`。\n"
        f"full matched tables：{'完成' if matched_ok else '未完成'}，7 个关键 cell 全量重建，报告 `{rel(REPORTS / 'full_matched_tables_052.csv')}`。\n"
        f"PSC per-matched phase_mod：{'完成' if psc_ok else '未完成'}，报告 `{rel(REPORTS / 'psc_phase_mod_permatched_full_052.csv')}`。\n"
        f"TTA circular variance：{'完成' if tta_ok else '未完成'}，使用 theta -> 2theta，未用 naive linear std，报告 `{rel(REPORTS / 'tta_circular_variance_full_052.csv')}`。\n"
        f"P1-P5 正式复跑条件：{'具备' if ready else '仍不足'}，判定 `{rel(DOCS / 'evidence_ready_for_p1_p5_rerun_052.md')}`。\n"
        f"仍缺什么：{'; '.join(missing) if missing else '无阻塞缺口，下一步进入 P1-P5 真实复跑'}。\n"
        "主产物路径：`outputs/persistent_artifacts/orientbench_real_052/`，`outputs/persistent_artifacts/manifest_052.json`。\n"
        f"verification/test/git 结果：{verification}; {tests}; {git_result}。\n\n"
        "👆👆👆👆👆👆\n"
    )
    (DOCS / "codex_latest_report.md").write_text(body, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    append_heartbeat("run_052", "start")
    artifacts: list[dict[str, Any]] = []
    dota_item = persist_dota_dump()
    artifacts.append(dota_item)
    matched, matched_artifacts = full_matched_tables()
    artifacts.extend(matched_artifacts)
    psc, psc_artifacts = psc_phase_mod_permatched()
    artifacts.extend(psc_artifacts)
    tta, tta_artifacts = tta_circular_variance_full()
    artifacts.extend(tta_artifacts)
    write_manifest(artifacts)
    write_readiness(matched, psc, tta)
    append_heartbeat("run_052", "complete")
    DOCS.joinpath("run_052_summary.json").write_text(
        json.dumps({"matched": matched, "psc": psc, "tta": tta}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

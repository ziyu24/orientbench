#!/usr/bin/env python3
"""SUPERVISOR_051 handoff map and real evidence recovery.

This is an offline recovery script. It reads existing artifacts, writes a
handoff map, cell status, gap plan, partial recovered matched tables, and a
decision on whether 052 can rerun P1-P5. It does not train or modify frozen
assets.
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
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "top_journal_v3"
DOCS = OUT / "docs"
REPORTS = OUT / "reports"
PERSIST = ROOT / "outputs/persistent_artifacts/orientbench_real_051"
MANIFEST = ROOT / "outputs/persistent_artifacts/manifest_051.json"

MAX_IMAGES = int(os.environ.get("OB051_MAX_IMAGES", "500"))
MAX_PSC_IMAGES = int(os.environ.get("OB051_MAX_PSC_IMAGES", "1200"))

CELLS = [
    ("DOTA-v1.0", "20", "psc"),
    ("DIOR-R", "22", "psc"),
    ("FAIR1M-v1.0", "24", "psc"),
    ("SODA-A", "23", "psc"),
    ("DIOR-R", "3", "orcnn"),
    ("DIOR-R", "61", "rtmdet"),
    ("DIOR-R", "10", "lsknet"),
    ("FAIR1M-v1.0", "5", "orcnn"),
    ("FAIR1M-v1.0", "12", "lsknet"),
    ("SODA-A", "4", "orcnn"),
    ("SODA-A", "11", "lsknet"),
    ("HRSC2016", "13", "lsknet"),
]

GT_PATHS = {
    "DOTA-v1.0": ROOT / "outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl",
    "DIOR-R": ROOT / "outputs/bench_core/gt_index/DIOR-R_val.jsonl",
    "FAIR1M-v1.0": ROOT / "outputs/bench_core/gt_index/FAIR1M-v1.0_val.jsonl",
    "SODA-A": ROOT / "outputs/bench_core/gt_index/SODA-A_val.jsonl",
    "HRSC2016": ROOT / "outputs/predictions/HRSC2016/_hrsc_gt.jsonl",
}

PSC_CONFIGS = {
    "DOTA-v1.0": ROOT.parent / "pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DOTA10_train_val/config.py",
    "DIOR-R": ROOT.parent / "pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py",
    "FAIR1M-v1.0": ROOT.parent / "pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py",
    "SODA-A": ROOT.parent / "pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py",
}


def now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def ensure() -> None:
    for p in [DOCS, REPORTS, OUT / "logs", OUT / "artifacts", PERSIST]:
        p.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def read_jsonl(path: Path, max_images: int | None = None) -> list[dict[str, Any]]:
    rows = []
    keep: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            img = str(r.get("image_id", r.get("img", r.get("img_id", ""))))
            if max_images is not None:
                if img not in keep and len(keep) >= max_images:
                    continue
                keep.add(img)
            rows.append(r)
    return rows


def rel(p: Path | None) -> str:
    if not p:
        return ""
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


def raw_path(ds: str, bid: str) -> Path | None:
    candidates = [
        ROOT / f"outputs/persistent_artifacts/orientbench_v2/{ds}/{bid}/raw/result_b{bid}.pkl",
        ROOT / f"outputs/predictions/{ds}/{bid}/raw/result_b{bid}.pkl",
        Path(f"/dev/shm/cqc/orientbench/predictions/{ds}/{bid}/raw/result_b{bid}.pkl"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def schema_path(ds: str, bid: str) -> Path | None:
    candidates = [
        ROOT / f"outputs/persistent_artifacts/orientbench_v2/{ds}/{bid}/schema/pred_b{bid}_fullval.jsonl",
        ROOT / f"outputs/persistent_artifacts/orientbench_v2/{ds}/{bid}/schema/pred_b{bid}_{ds}_val.jsonl",
        ROOT / f"outputs/persistent_artifacts/orientbench_v2/{ds}/{bid}/schema/pred_b{bid}_dcal.jsonl",
        ROOT / f"outputs/predictions/{ds}/{bid}/schema/pred_b{bid}_test.jsonl",
        Path(f"/dev/shm/cqc/orientbench/predictions/{ds}/{bid}/schema/pred_b{bid}_fullval.jsonl"),
        Path(f"/dev/shm/cqc/orientbench/predictions/_archive/{ds}/{bid}/schema/pred_b{bid}_val.jsonl"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def feature_path(ds: str, bid: str) -> Path | None:
    candidates = [
        ROOT / f"outputs/persistent_artifacts/orientbench_v2_047/features_v2/features_v2/{ds}_{bid}.jsonl",
        ROOT / f"outputs/persistent_artifacts/orientbench_v2_047/features_v2/{ds}_{bid}.jsonl",
        ROOT / f"measure_fix_v2/artifacts/features_v2/{ds}_{bid}.jsonl",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def track_a_path(ds: str, bid: str) -> Path | None:
    candidates = [
        ROOT / f"outputs/persistent_artifacts/orientbench_v2_047/track_a_dumps/{ds}_{bid}.pkl",
        Path(f"/dev/shm/cqc/orientbench/measure_fix_v2/track_a/{ds}_{bid}.pkl"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def tta_dir(ds: str, bid: str) -> Path | None:
    p = ROOT / f"outputs/persistent_artifacts/orientbench_v2_047/tta_preds/{ds}_{bid}"
    return p if p.exists() else None


def parse_classes(config: Path, ds: str) -> list[str]:
    if ds == "DIOR-R":
        p = ROOT / "measure_fix_v2/artifacts/dior_classes.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    text = config.read_text(encoding="utf-8", errors="ignore") if config.exists() else ""
    m = re.search(r"classes\s*=\s*(\([^\)]*\))", text, re.S)
    if m:
        try:
            return list(ast.literal_eval(m.group(1)))
        except Exception:
            pass
    # SODA configs repeat an inline tuple in test_dataloader; parse the first
    # classes=(...) block even when it is nested.
    m = re.search(r"classes\s*=\s*\((.*?)\)", text, re.S)
    if m:
        raw = "(" + m.group(1) + ")"
        try:
            return list(ast.literal_eval(raw))
        except Exception:
            pass
    return []


def aspect_ratio(w: float, h: float) -> float:
    return max(w, h) / max(1e-9, min(w, h))


def size_bin(area: float) -> str:
    if area < 32 * 32:
        return "small"
    if area < 96 * 96:
        return "medium"
    return "large"


def split_of(image_id: str) -> str:
    from orientbench.data.splits import assign_split

    return assign_split(image_id)


def detector_records_from_track_dump(ds: str, bid: str, max_images: int | None) -> list[dict[str, Any]]:
    p = track_a_path(ds, bid)
    if not p:
        return []
    classes = parse_classes(PSC_CONFIGS.get(ds, Path()), ds)
    if not classes:
        return []
    rows = []
    seen = set()
    data = pickle.load(p.open("rb"))
    for rec in data:
        img = str(rec.get("img_id"))
        if max_images is not None and img not in seen and len(seen) >= max_images:
            continue
        seen.add(img)
        pi = rec.get("pred_instances", {})
        bbs = np.asarray(pi.get("bboxes", []))
        scores = np.asarray(pi.get("scores", []))
        labels = np.asarray(pi.get("labels", []))
        phase = pi.get("phase_mod")
        if phase is None:
            continue
        phase = np.asarray(phase.cpu() if hasattr(phase, "cpu") else phase)
        for pred_id, (b, s, lab, pm) in enumerate(zip(bbs, scores, labels, phase)):
            if float(s) < 0.30:
                continue
            lab = int(lab)
            rows.append({
                "image_id": img,
                "pred_id": pred_id,
                "class_name": classes[lab] if lab < len(classes) else str(lab),
                "score": float(s),
                "phase_mod": float(pm),
                "obb_cx": float(b[0]),
                "obb_cy": float(b[1]),
                "obb_w": float(b[2]),
                "obb_h": float(b[3]),
                "obb_theta": float(b[4]),
            })
    return rows


def match_rows(preds: list[dict[str, Any]], gts: list[dict[str, Any]], cell_id: str, source_checkpoint: str) -> list[dict[str, Any]]:
    from orientbench.metrics.angle_contract import angle_error_contract
    from orientbench.metrics.matching import match_dataset

    m = match_dataset(preds, gts)
    out = []
    for pi, gi, iou in m["matched_pairs"]:
        p = preds[pi]
        g = gts[gi]
        c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"], g["obb_w"], g["obb_h"], g["obb_theta"])
        ar = aspect_ratio(g["obb_w"], g["obb_h"])
        area = float(g["obb_w"] * g["obb_h"])
        out.append({
            "cell_id": cell_id,
            "dataset": cell_id.split("/")[0],
            "detector": "",
            "image_id": p["image_id"],
            "pred_id": p.get("pred_id", pi),
            "gt_id": gi,
            "score": p.get("score", ""),
            "phase_mod": p.get("phase_mod", ""),
            "pred_obb": json.dumps({k: p[k] for k in ["obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta"]}),
            "gt_obb": json.dumps({k: g[k] for k in ["obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta"]}),
            "match_iou": iou,
            "angle_error": c["angle_error_canonical_longside"],
            "class": g.get("class_name", ""),
            "size": area,
            "aspect_ratio": ar,
            "size_bin": size_bin(area),
            "near_square": c["near_square"],
            "split": split_of(str(p["image_id"])),
            "source_checkpoint": source_checkpoint,
            "is_real_detector_output": True,
        })
    return out


def handoff_map() -> list[dict[str, Any]]:
    dirs = [
        ("top_journal_v3", "v3 supervisor 049-051 reports/scripts/latest decisions", "v3", False, True, False, "mixed: 049/050 reports; final evidence only if verifier says real/non-proxy"),
        ("measure_fix_v2", "v2 measure-fix experiments, G2/deployable/TrackA/TTA scripts and reports", "v2", False, True, False, "formal for v2 reports; some artifacts are copied to persistent_artifacts"),
        ("docs", "root paper drafts and project-level scientific audits", "root_docs", False, False, False, "writing/reference only"),
        ("outputs/bench_core/reports", "P1 bench reports, old metric summaries, frozen audit material", "frozen_outputs", True, True, False, "read-only evidence/source references"),
        ("outputs/persistent_artifacts", "persistent raw/schema/feature/TrackA/TTA artifacts with manifests", "persistent", True, True, False, "primary place for final artifacts"),
        ("outputs/predictions", "local prediction outputs, some raw/schema not copied to persistent", "prediction_outputs", False, False, False, "usable only after persistence and manifest"),
        ("/dev/shm/cqc/orientbench", "scratch prediction/farm/cache location", "scratch", False, False, True, "not final evidence unless copied and manifested"),
        ("pth_data", "read-only baseline configs/checkpoints/logs", "external_baseline", True, True, False, "source checkpoint registry; do not modify"),
        ("claude_code_and_supervisor.md", "root action log", "log", True, True, False, "handoff log"),
        ("measure_fix_v2/claude_code_and_supervisor.md", "v2 action log", "log", True, True, False, "handoff log"),
        ("top_journal_v3/codex_and_supervisor.md", "v3 action log", "log", False, True, False, "current log"),
    ]
    rows = []
    for path, purpose, stage, frozen, persistent, scratch, use in dirs:
        p = Path(path) if path.startswith("/") else ROOT / path
        rows.append({
            "path": path,
            "exists": p.exists(),
            "purpose": purpose,
            "stage": stage,
            "frozen_or_read_only": frozen,
            "persistent": persistent,
            "scratch_or_proxy_risk": scratch,
            "formal_evidence_use": use,
            "missing_or_rebuild_note": "" if p.exists() else "missing",
        })
    write_csv(REPORTS / "artifact_locator_051.csv", rows)
    DOCS.joinpath("codex_handoff_map_051.md").write_text(
        "# Codex handoff map 051\n\n"
        f"Generated: {now()}\n\n"
        "This map is for continuing from prior Claude/Codex work, not restarting the project. "
        "Frozen files and old release facts are read-only. Scratch artifacts under /dev/shm are not final evidence unless copied to outputs/persistent_artifacts with manifest and sha256.\n\n"
        + pd.DataFrame(rows).to_markdown(index=False)
        + "\n",
        encoding="utf-8",
    )
    return rows


def cell_status() -> list[dict[str, Any]]:
    rows = []
    for ds, bid, det in CELLS:
        raw = raw_path(ds, bid)
        schema = schema_path(ds, bid)
        feat = feature_path(ds, bid)
        track = track_a_path(ds, bid)
        tta = tta_dir(ds, bid)
        gt = GT_PATHS.get(ds)
        synthetic = False
        schema_cols = set()
        if schema and schema.exists():
            try:
                sample = read_jsonl(schema, max_images=1)[:20]
                synthetic = any(bool(x.get("is_synthetic")) or bool(x.get("not_detector_output")) for x in sample)
                for x in sample:
                    schema_cols.update(x.keys())
            except Exception:
                synthetic = True
        feature_cols = set()
        if feat:
            try:
                sample = read_jsonl(feat, max_images=1)[:20]
                for x in sample:
                    feature_cols.update(x.keys())
            except Exception:
                pass
        matched_full = bool(feat and {"err", "score", "split", "w", "h", "theta"}.issubset(feature_cols))
        rows.append({
            "cell_id": f"{ds}/{bid}",
            "dataset": ds,
            "baseline_id": bid,
            "detector": det,
            "real_raw_post_nms_exists": bool(raw),
            "raw_path": rel(raw),
            "schema_17field_exists": bool(schema),
            "schema_path": rel(schema),
            "schema_persistent": bool(schema and str(schema).startswith(str(ROOT / "outputs/persistent_artifacts"))),
            "gt_obb_exists": bool(gt and gt.exists()),
            "gt_path": rel(gt),
            "matched_table_exists": bool(feat),
            "matched_table_path": rel(feat),
            "match_iou_exists": False,
            "angle_error_exists": "err" in feature_cols,
            "near_square_aspect_size_exists": bool({"log_ar", "w", "h"}.issubset(feature_cols)),
            "phase_mod_exists": bool(track) if det == "psc" else False,
            "phase_mod_path": rel(track),
            "tta_predictions_exist": bool(tta),
            "tta_path": rel(tta),
            "circular_variance_exists": False,
            "synthetic_or_proxy": synthetic,
            "can_recompute": bool(raw or schema or feat),
            "formal_evidence_ready": bool(schema and gt and feat and not synthetic and str(schema).startswith(str(ROOT / "outputs/persistent_artifacts"))),
            "missing_reason": ";".join([
                s for s, bad in [
                    ("raw_missing", not raw),
                    ("schema_missing", not schema),
                    ("schema_not_persistent", bool(schema) and not str(schema).startswith(str(ROOT / "outputs/persistent_artifacts"))),
                    ("gt_missing", not (gt and gt.exists())),
                    ("matched_full_17field_missing", not matched_full),
                    ("match_iou_missing", True),
                    ("phase_mod_missing" if det == "psc" else "", det == "psc" and not track),
                    ("tta_missing", not tta),
                    ("circular_variance_missing", True),
                    ("synthetic_or_proxy", synthetic),
                ] if s and bad
            ]),
        })
    write_csv(REPORTS / "real_cell_artifact_status_051.csv", rows)
    return rows


def write_gap_plan(status_rows: list[dict[str, Any]]) -> None:
    dota = [r for r in status_rows if r["cell_id"] == "DOTA-v1.0/20"][0]
    DOCS.joinpath("real_evidence_gap_plan_051.md").write_text(
        "# Real evidence gap plan 051\n\n"
        f"Generated: {now()}\n\n"
        "## Concrete gaps\n\n"
        "- DOTA #20 Track A phase_mod is absent from both persistent artifacts and /dev/shm Track A dumps. Existing DOTA #20 has real raw/schema and matched features, but no instrumented phase_mod forward dump.\n"
        "- DIOR #22 / FAIR1M #24 / SODA #23 persistent Track A pkl files contain phase_mod, but older 050 did not persist exact pred_id-to-matched-GT alignment. 051 attempts offline rematching from the pkl predictions to recover that alignment; any missing DOTA row remains unavailable_with_evidence.\n"
        "- Existing features_v2 matched tables contain score, theta/geometry-derived fields, error and split, but not full 17-field matched rows with pred OBB, GT OBB, match IoU and GT id. 051 writes recovered matched subsets under outputs/persistent_artifacts/orientbench_real_051/.\n"
        "- DIOR #61, DIOR #10, FAIR1M #5/#12, SODA #4/#11 and HRSC #13 have schema/raw material partly only in outputs/predictions or /dev/shm, not fully in persistent_artifacts. These need persistence or rerun before final evidence.\n"
        "- TTA pkl files exist for several key cells, but circular variance was not previously persisted as a first-class table. 051 writes tta_circular_variance_051.csv from available TTA pkls.\n\n"
        "## Directly reusable\n\n"
        "- Persistent raw/schema: DOTA #20, DIOR #22/#3, FAIR1M #24, SODA #23.\n"
        "- Persistent features_v2: DOTA #20, DIOR #22/#3/#10/#61, FAIR1M #24/#5/#12, SODA #23/#4/#11.\n"
        "- Persistent Track A pkl: DIOR #22, FAIR1M #24, SODA #23.\n"
        "- Persistent TTA pkl: DIOR #3/#22/#61, FAIR1M #5/#24, SODA #4/#23.\n\n"
        "## Must rerun or rebuild\n\n"
        "- DOTA #20 instrumented Track A forward dump with phase_mod, using a shadow farm and no detector training.\n"
        "- Full persistent raw/schema for scratch-only cells needed in final tables.\n"
        "- Full-cell matched 17-field tables if 052 decides to run final P1/P2/P4/P5 evidence, because 051 uses capped offline recovery for handoff.\n\n"
        f"DOTA #20 current status row: `{dota['missing_reason']}`.\n",
        encoding="utf-8",
    )


def recover_permatched_psc() -> list[dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    for ds, bid in [("DOTA-v1.0", "20"), ("DIOR-R", "22"), ("FAIR1M-v1.0", "24"), ("SODA-A", "23")]:
        cell = f"{ds}/{bid}"
        p = track_a_path(ds, bid)
        gt_path = GT_PATHS.get(ds)
        if not p or not gt_path or not gt_path.exists():
            all_rows.append({
                "cell_id": cell,
                "dataset": ds,
                "detector": "psc",
                "image_id": "",
                "pred_id": "",
                "gt_id": "",
                "score": "",
                "phase_mod": "",
                "pred_obb": "",
                "gt_obb": "",
                "match_iou": "",
                "angle_error": "",
                "class": "",
                "size": "",
                "aspect_ratio": "",
                "near_square": "",
                "split": "",
                "source_checkpoint": "pth_data baseline PSC",
                "is_real_detector_output": False,
                "status": "unavailable_with_evidence: missing persistent Track A dump or GT",
            })
            continue
        preds = detector_records_from_track_dump(ds, bid, MAX_PSC_IMAGES)
        imgs = {x["image_id"] for x in preds}
        gts = [g for g in read_jsonl(gt_path) if g.get("image_id") in imgs]
        rows = match_rows(preds, gts, cell, "pth_data baseline PSC")
        for r in rows:
            r["detector"] = "psc"
            r["status"] = f"recovered_offline_max_images_{MAX_PSC_IMAGES}"
        all_rows.extend(rows)
    out = REPORTS / "psc_track_a_permatched_051.csv"
    write_csv(out, all_rows)
    DOCS.joinpath("psc_track_a_permatched_051.md").write_text(
        "# PSC Track A per-matched recovery 051\n\n"
        f"Generated: {now()}\n\n"
        f"Rows: {len(all_rows)}. DIOR/FAIR/SODA rows are recovered by offline GT rematching from persistent Track A pkl dumps where available. "
        "DOTA #20 remains unavailable unless an instrumented forward dump is rerun. The recovery is capped by OB051_MAX_PSC_IMAGES for handoff speed; 052 should rerun full-cell if using this as final evidence.\n",
        encoding="utf-8",
    )
    return all_rows


def recover_matched_tables() -> list[dict[str, Any]]:
    targets = [("DOTA-v1.0", "20"), ("DIOR-R", "22"), ("FAIR1M-v1.0", "24"), ("SODA-A", "23"), ("DIOR-R", "3"), ("DIOR-R", "61"), ("SODA-A", "4")]
    manifest_artifacts = []
    for ds, bid in targets:
        sp = schema_path(ds, bid)
        gp = GT_PATHS.get(ds)
        cell_dir = PERSIST / ds / bid
        cell_dir.mkdir(parents=True, exist_ok=True)
        if not sp or not gp or not gp.exists():
            continue
        preds = read_jsonl(sp, max_images=MAX_IMAGES)
        if any(p.get("is_synthetic") or p.get("not_detector_output") for p in preds):
            continue
        imgs = {p["image_id"] for p in preds}
        gts = [g for g in read_jsonl(gp) if g.get("image_id") in imgs]
        rows = match_rows(preds, gts, f"{ds}/{bid}", "pth_data baseline checkpoint")
        for r in rows:
            r["detector"] = next(det for d, b, det in CELLS if d == ds and b == bid)
            r["status"] = f"recovered_offline_max_images_{MAX_IMAGES}"
        out = cell_dir / "matched_17field_051.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        manifest_artifacts.append({
            "cell_id": f"{ds}/{bid}",
            "kind": "matched_17field_jsonl",
            "path": rel(out),
            "sha256": sha256(out),
            "bytes": out.stat().st_size,
            "source_schema": rel(sp),
            "source_gt": rel(gp),
            "source_checkpoint": "pth_data baseline checkpoint",
            "split": "existing frozen split / dataset val-test as in source schema",
            "can_recompute": True,
            "generation_command": "python top_journal_v3/scripts/run_051_handoff_recovery.py (offline rematch; no training)",
            "is_real_detector_output": True,
            "max_images": MAX_IMAGES,
        })
    return manifest_artifacts


def tta_circular_variance() -> list[dict[str, Any]]:
    targets = [("DIOR-R", "3"), ("DIOR-R", "61"), ("SODA-A", "4"), ("FAIR1M-v1.0", "24"), ("SODA-A", "23")]
    rows = []
    for ds, bid in targets:
        d = tta_dir(ds, bid)
        if not d:
            rows.append({"cell_id": f"{ds}/{bid}", "status": "missing_tta_dir"})
            continue
        try:
            ident = pickle.load((d / "identity.pkl").open("rb"))
            hflip = pickle.load((d / "hflip.pkl").open("rb")) if (d / "hflip.pkl").exists() else []
            vflip = pickle.load((d / "vflip.pkl").open("rb")) if (d / "vflip.pkl").exists() else []
        except Exception as e:
            rows.append({"cell_id": f"{ds}/{bid}", "status": f"load_failed:{e}"})
            continue
        hf = {str(r.get("img_id")): r for r in hflip}
        vf = {str(r.get("img_id")): r for r in vflip}
        count = 0
        for rec in ident:
            if count >= 5000:
                break
            img = str(rec.get("img_id"))
            pi = rec.get("pred_instances", {})
            bbs = np.asarray(pi.get("bboxes", []))
            scores = np.asarray(pi.get("scores", []))
            labels = np.asarray(pi.get("labels", []))
            for pred_id, (b, s, lab) in enumerate(zip(bbs, scores, labels)):
                if float(s) < 0.30:
                    continue
                angles = [float(b[4])]
                # Lightweight nearest-center match after unflip. This is a
                # recovery table, not a final TTA benchmark.
                for src, mode in [(hf.get(img), "h"), (vf.get(img), "v")]:
                    if src is None:
                        continue
                    spi = src.get("pred_instances", {})
                    sb = np.asarray(spi.get("bboxes", []))
                    ss = np.asarray(spi.get("scores", []))
                    sl = np.asarray(spi.get("labels", []))
                    best, best_d = None, 1e9
                    H, W = rec.get("ori_shape", (1024, 1024))
                    for tb, ts, tl in zip(sb, ss, sl):
                        if int(tl) != int(lab) or float(ts) < 0.30:
                            continue
                        cx, cy, th = float(tb[0]), float(tb[1]), float(tb[4])
                        if mode == "h":
                            cx, th = W - cx, -th
                        else:
                            cy, th = H - cy, -th
                        dist = math.hypot(cx - float(b[0]), cy - float(b[1]))
                        if dist < best_d and dist < 40:
                            best_d, best = dist, th
                    if best is not None:
                        angles.append(float(best))
                doubled = np.asarray([2 * a for a in angles])
                R = float(np.hypot(np.cos(doubled).mean(), np.sin(doubled).mean())) if len(doubled) else float("nan")
                rows.append({
                    "cell_id": f"{ds}/{bid}",
                    "dataset": ds,
                    "baseline_id": bid,
                    "image_id": img,
                    "pred_id": pred_id,
                    "score": float(s),
                    "n_tta_angles": len(angles),
                    "circular_variance": 1 - R if math.isfinite(R) else "",
                    "theta_to_2theta": True,
                    "naive_linear_std_used": False,
                    "status": "recovered_from_persistent_tta_pkls",
                })
                count += 1
                if count >= 5000:
                    break
    write_csv(REPORTS / "tta_circular_variance_051.csv", rows)
    return rows


def write_manifest(artifacts: list[dict[str, Any]]) -> None:
    manifest = {
        "generated": now(),
        "approval_token": "SUPERVISOR_APPROVED_051_CODEX_HANDOFF_REAL_EVIDENCE_RECOVERY",
        "gpu_used": False,
        "world_size": 0,
        "scratch_path": "",
        "host_training_started": False,
        "thresholds_modified": False,
        "dcal_daudit_modified": False,
        "full_matrix_added": False,
        "persistent_dir": rel(PERSIST),
        "artifacts": artifacts,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def recovery_decision(status_rows: list[dict[str, Any]], pertrack_rows: list[dict[str, Any]], manifest_artifacts: list[dict[str, Any]], tta_rows: list[dict[str, Any]]) -> None:
    enough_p1 = len(manifest_artifacts) >= 7 and all(a["max_images"] >= MAX_IMAGES for a in manifest_artifacts)
    enough_p2 = len([r for r in status_rows if r["matched_table_exists"] and not r["synthetic_or_proxy"]]) >= 7
    psc_cells = {r.get("cell_id") for r in pertrack_rows if r.get("phase_mod") not in ("", None) and str(r.get("phase_mod")) != "nan"}
    enough_p3 = {"DOTA-v1.0/20", "DIOR-R/22", "FAIR1M-v1.0/24", "SODA-A/23"}.issubset(psc_cells)
    enough_p4 = len([r for r in tta_rows if r.get("status") == "recovered_from_persistent_tta_pkls"]) > 0
    enough_p5 = len(manifest_artifacts) >= 7
    DOCS.joinpath("evidence_recovery_decision_051.md").write_text(
        "# Evidence recovery decision 051\n\n"
        f"Generated: {now()}\n\n"
        f"- P1 rerun readiness: {'yes' if enough_p1 else 'partial only'}; recovered matched tables are capped at {MAX_IMAGES} images/cell and need full-cell rerun for final P1.\n"
        f"- P2 conformal readiness: {'yes for feature-table empirical rerun' if enough_p2 else 'partial'}; final CRC should use full persistent matched rows.\n"
        f"- P3 PSC free mechanism readiness: {'yes' if enough_p3 else 'no'}; DOTA #20 phase_mod remains missing unless rerun with instrumented forward dump.\n"
        f"- P4 uncertainty readiness: {'partial'}; TTA circular variance table exists for available pkls, but MC/dropout/ensemble/native/GWD-KLD are still absent.\n"
        f"- P5 downstream readiness: {'partial'}; matched rows are real but capped/offline, suitable for 052 smoke before final full-cell.\n\n"
        "Recommendation: do not rewrite science conclusions yet. Start 052 only after either accepting capped real recovery as smoke input or rerunning full-cell DOTA #20 Track A plus full matched 17-field persistence for the seven key cells.\n",
        encoding="utf-8",
    )


def latest_and_log(status_rows: list[dict[str, Any]], pertrack_rows: list[dict[str, Any]], manifest_artifacts: list[dict[str, Any]], tta_rows: list[dict[str, Any]]) -> None:
    found = [r["cell_id"] for r in status_rows if r["real_raw_post_nms_exists"] or r["schema_17field_exists"]]
    missing = [r["cell_id"] + ":" + r["missing_reason"] for r in status_rows if r["missing_reason"]]
    latest = f"""👇👇👇👇👇👇

051 完成，定位与离线恢复已完成；未把 partial 写成 pass。

旧产物地图：已完成 codex_handoff_map_051.md 与 artifact_locator_051.csv。

真实 artifact 找到：{', '.join(found[:12])}。persistent raw/schema 明确覆盖 DOTA #20、DIOR #22/#3、FAIR1M #24、SODA #23；features_v2 覆盖更多 cells；Track A pkl 覆盖 DIOR #22、FAIR1M #24、SODA #23；TTA pkl 覆盖 DIOR #3/#22/#61、FAIR1M #5/#24、SODA #4/#23。

仍缺：DOTA #20 phase_mod forward dump；scratch-only schema 的持久化重建；full-cell 17字段 matched table；完整 per-matched phase_mod 全量表；MC/dropout/ensemble/native/GWD-KLD 强不确定性。

是否重跑关键 inference/dump：未重跑 GPU inference/forward dump；本轮只做离线恢复。已生成 capped real matched tables、DIOR/FAIR/SODA PSC per-matched recovery、TTA circular variance recovery。

P1-P5 复跑条件：P1 partial smoke 可复跑但 final 不足；P2 可用 features 做 empirical rerun但 final 需 full matched；P3 不具备，因为 DOTA #20 phase_mod 缺失；P4 partial TTA 可复跑但强基线不足；P5 partial 可复跑。

下一步：不应直接进入最终 052 论文结论复跑；建议 052 先补 DOTA #20 instrumented forward dump 和 full-cell matched 17字段持久化，然后再复跑 P1-P5。

主产物路径：top_journal_v3/docs/codex_handoff_map_051.md；top_journal_v3/reports/artifact_locator_051.csv；top_journal_v3/reports/real_cell_artifact_status_051.csv；top_journal_v3/docs/real_evidence_gap_plan_051.md；top_journal_v3/docs/evidence_recovery_decision_051.md；outputs/persistent_artifacts/manifest_051.json。

verification/test/git：见 top_journal_v3/reports/verification_handoff_recovery_051.json；未用 GPU；未重训 host；未改 thresholds.yaml / D_cal / D_audit；未补 full matrix。

👆👆👆👆👆👆
"""
    (DOCS / "codex_latest_report.md").write_text(latest, encoding="utf-8")
    log = (
        f"## {now()}\n\n"
        "- 指令来源: SUPERVISOR_051_CODEX_HANDOFF_AND_REAL_EVIDENCE_RECOVERY\n"
        "- 执行动作: 读取 AGENTS.md 和 项目执行文件_v2_measure_fix.md；生成 handoff map、artifact locator、cell status、gap plan；离线恢复 PSC/TTA/matched capped artifacts；未启动 GPU/inference/training。\n"
        "- 关键产物路径: top_journal_v3/docs/codex_handoff_map_051.md; top_journal_v3/reports/real_cell_artifact_status_051.csv; outputs/persistent_artifacts/manifest_051.json\n"
        "- pass/fail/partial: partial recovery; P3 final rerun still blocked by DOTA #20 phase_mod.\n"
        "- 是否触发停止条件: 未触发科学早停；触发 artifact gap stop for final P3.\n"
        "- 下一步建议: 052 先补 DOTA #20 Track A dump 与 full matched persistence，再复跑 P1-P5。\n\n"
    )
    (OUT / "codex_and_supervisor.md").write_text(log, encoding="utf-8")
    with (ROOT / "claude_code_and_supervisor.md").open("a", encoding="utf-8") as f:
        f.write(log)
    (REPORTS / "heartbeat_051.json").write_text(json.dumps({"timestamp": now(), "status": "partial_recovery_complete", "gpu_used": False, "world_size": 0}, indent=2), encoding="utf-8")


def main() -> None:
    ensure()
    handoff_map()
    status = cell_status()
    write_gap_plan(status)
    pertrack = recover_permatched_psc()
    matched_artifacts = recover_matched_tables()
    tta = tta_circular_variance()
    write_manifest(matched_artifacts)
    recovery_decision(status, pertrack, matched_artifacts, tta)
    latest_and_log(status, pertrack, matched_artifacts, tta)


if __name__ == "__main__":
    main()

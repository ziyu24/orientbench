"""Prediction import matrix — baseline_id x dataset status.

Merges baseline inventory, dataset inventory, and prediction discovery to give,
per (baseline, dataset), whether a prediction can be imported now.

Statuses: ready_schema | convertible_nonformal | needs_inference |
blocked_missing_dataset | blocked_missing_detector | unsupported | not_applicable
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

PRESENT_DATASETS = {"DOTA-v1.0", "DOTA-v1.5", "DIOR-R", "HRSC2016", "FAIR1M-v1.0"}


def _norm_dataset(name: str) -> Optional[str]:
    n = (name or "").upper()
    if "SODA" in n:
        return None  # SODA-A missing
    if "ICDAR" in n:
        return None  # ICDAR-MLT missing
    if "DOTA-V1.5" in n:
        return "DOTA-v1.5"
    if "DOTA-V1.0" in n:
        return "DOTA-v1.0"
    if "DIOR" in n:
        return "DIOR-R"
    if "HRSC" in n:
        return "HRSC2016"
    if "FAIR1M" in n:
        return "FAIR1M-v1.0"
    return None


def _load_json(path: str):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_import_matrix(outputs_dir: str) -> Dict[str, Any]:
    inv = _load_json(os.path.join(outputs_dir, "baseline_inventory.json"))
    # discovery: map baseline_id -> best ingestion_status (read csv directly)
    disc_status: Dict[str, str] = {}
    csv_path = os.path.join(outputs_dir, "reports", "prediction_discovery.csv")
    if os.path.isfile(csv_path):
        import csv as _csv
        with open(csv_path, "r", encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                bid = r.get("baseline_id")
                st = r.get("ingestion_status")
                if bid and st and bid not in ("", "None"):
                    # prefer ready_schema > convertible*
                    prev = disc_status.get(bid)
                    rank = {"ready_schema": 3, "convertible_needs_mapping": 2,
                            "convertible_bbox_only": 1}
                    if prev is None or rank.get(st, 0) > rank.get(prev, 0):
                        disc_status[bid] = st

    rows: List[Dict[str, Any]] = []
    if inv:
        for r in inv["records"]:
            bid = str(r.get("id"))
            norm = _norm_dataset(r.get("dataset", ""))
            present = norm in PRESENT_DATASETS if norm else False
            valid = r.get("valid") is True
            dstat = disc_status.get(bid)
            if dstat == "ready_schema":
                status, reason = "ready_schema", "discovered prediction matches schema"
            elif dstat in ("convertible_needs_mapping", "convertible_bbox_only"):
                status, reason = "convertible_nonformal", f"discovered {dstat} (not formal gate)"
            elif not norm:
                status, reason = "blocked_missing_dataset", f"dataset '{r.get('dataset')}' missing locally"
            elif not present:
                status, reason = "blocked_missing_dataset", f"dataset '{r.get('dataset')}' not present"
            elif not valid:
                status, reason = "not_applicable", "baseline marked invalid in readme"
            else:
                status, reason = "needs_inference", "ckpt+config present; inference required (approval-gated)"
            rows.append({
                "baseline_id": bid, "model_id": r.get("model_id"),
                "dataset": r.get("dataset"), "normalized_dataset": norm or "MISSING",
                "dataset_present": present, "valid": valid,
                "status": status, "reason": reason,
            })

    # missing detector archetypes (RHINO / A4 host) — explicit blocked rows
    for det, note in [("rhino_rotated_detr", "RHINO-style rotated DETR missing (C1/B host)"),
                      ("a4_hybrid_encoder_oriented_detr", "A4 frozen host pending")]:
        rows.append({"baseline_id": None, "model_id": det, "dataset": "(any)",
                     "normalized_dataset": "(any)", "dataset_present": False, "valid": False,
                     "status": "blocked_missing_detector", "reason": note})

    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    n_ready = counts.get("ready_schema", 0)
    return {"n_rows": len(rows), "status_counts": counts,
            "n_ready_schema": n_ready, "rows": rows}

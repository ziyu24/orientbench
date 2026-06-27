"""Inference command PLAN (generate only — never executes inference).

For each valid baseline on a present dataset, assembles what a future inference
run would need (config, checkpoint, dataset, expected output, repo/env clue, GPU
suggestion, conversion need, blocking reason). RHINO / A4 / missing datasets stay
blocked. This module does NOT run anything.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from orientbench.reports.prediction_import_matrix import _norm_dataset

PRESENT_DATASETS = {"DOTA-v1.0", "DOTA-v1.5", "DIOR-R", "HRSC2016", "FAIR1M-v1.0"}


def _load_json(path: str):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_inference_plan(outputs_dir: str, pred_out_root: str) -> Dict[str, Any]:
    inv = _load_json(os.path.join(outputs_dir, "baseline_inventory.json"))
    rows: List[Dict[str, Any]] = []
    if inv:
        for r in inv["records"]:
            norm = _norm_dataset(r.get("dataset", ""))
            present = norm in PRESENT_DATASETS if norm else False
            valid = r.get("valid") is True
            bid = r.get("id")
            blocked_reason = ""
            if not norm or not present:
                blocked_reason = f"blocked_missing_dataset: {r.get('dataset')}"
            elif not valid:
                blocked_reason = "not_applicable: baseline invalid"
            expected_out = os.path.join(pred_out_root, f"pred_baseline{bid}_{norm}.pkl") if norm else ""
            rows.append({
                "baseline_id": bid, "model_id": r.get("model_id"), "dataset": r.get("dataset"),
                "config": r.get("config_abs"), "checkpoint": r.get("pth_abs"),
                "repo_env_clue": f"{r.get('mmrotate_stack')} / env={r.get('env')}",
                "gpu_suggestion": "1-4x A30 (single-gpu test first); reproducible multi-proc",
                "expected_output_path": expected_out,
                "needs_prediction_schema_conversion": True,  # mmrotate pkl -> schema
                "blocked_reason": blocked_reason or "(none — inference approval-gated)",
                "executable_now": False,  # inference not allowed this round
            })
    # explicit blocked host rows
    for det, note in [("rhino_rotated_detr", "RHINO missing — no checkpoint/config"),
                      ("a4_hybrid_encoder_oriented_detr", "A4 frozen host pending")]:
        rows.append({"baseline_id": None, "model_id": det, "dataset": "(any)",
                     "config": None, "checkpoint": None, "repo_env_clue": "n/a",
                     "gpu_suggestion": "n/a", "expected_output_path": "",
                     "needs_prediction_schema_conversion": True,
                     "blocked_reason": f"blocked_missing_detector: {note}",
                     "executable_now": False})

    n_planned = sum(1 for r in rows if r["blocked_reason"].startswith("(none"))
    n_blocked = len(rows) - n_planned
    return {"n_rows": len(rows), "n_inference_planned": n_planned,
            "n_blocked": n_blocked, "any_executable_now": False, "rows": rows}

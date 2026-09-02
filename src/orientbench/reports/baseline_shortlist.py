"""Baseline selection shortlist — minimal set to prioritize for prediction import.

Picks one representative valid baseline per detector archetype (two-stage,
strong-backbone two-stage, one-stage real-time, DETR-like, angle-coder PSC,
weak/pseudo). RHINO is listed SEPARATELY as blocked (missing) — ARS-DETR is the
DETR-like representative and is NOT a RHINO substitute.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

# archetype -> model_id substring(s), preferred dataset, label
ARCHETYPES = [
    ("two_stage_regression", ["oriented_rcnn_r50"], "DOTA-v1.0", "two-stage angle regression"),
    ("two_stage_strong_backbone", ["oriented_rcnn_lsknet", "strip_rcnn"], "DOTA-v1.0",
     "strong-backbone two-stage"),
    ("one_stage_realtime", ["rotated_rtmdet"], "DOTA-v1.0", "one-stage real-time"),
    ("angle_coder_psc", ["rotated_retinanet_psc"], "DOTA-v1.0", "PSC angle-coder (angle distribution)"),
    ("detr_like", ["arsdetr"], "DOTA-v1.0", "DETR-like (ARS-DETR; NOT a RHINO substitute)"),
    ("weak_pseudo", ["h2rbox_v2", "point2rbox_v2", "rotated_fcos"], "DOTA-v1.0", "weak/pseudo supervision"),
]


def _load_inv(outputs_dir: str) -> Optional[dict]:
    p = os.path.join(outputs_dir, "baseline_inventory.json")
    if not os.path.isfile(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_shortlist(outputs_dir: str) -> Dict[str, Any]:
    inv = _load_inv(outputs_dir)
    selected: List[Dict[str, Any]] = []
    if inv:
        for arche, subs, pref_ds, label in ARCHETYPES:
            cands = [r for r in inv["records"]
                     if r.get("valid") is True
                     and any(s in (r.get("model_id") or "").lower() for s in subs)]
            if not cands:
                selected.append({"archetype": arche, "status": "none_valid",
                                 "why_selected": label, "risks": "no valid baseline for archetype"})
                continue
            pref = [c for c in cands if pref_ds.lower() in (c.get("dataset") or "").lower()]
            chosen = (pref or cands)[0]
            selected.append({
                "archetype": arche, "status": "selected",
                "baseline_id": chosen.get("id"), "model_id": chosen.get("model_id"),
                "dataset": chosen.get("dataset"), "config": chosen.get("config_abs"),
                "checkpoint": chosen.get("pth_abs"),
                "why_selected": label,
                "risks": "prediction requires inference (approval-gated) + pkl->schema conversion + angle verify",
            })
    # RHINO blocked row — explicit, not substituted
    selected.append({
        "archetype": "rotated_detr_rhino", "status": "blocked_missing",
        "baseline_id": None, "model_id": "rhino", "dataset": "(C1/B host)",
        "config": None, "checkpoint": None,
        "why_selected": "REQUIRED C1/B host but MISSING",
        "risks": "must NOT be substituted by ARS-DETR; needs collaborator ruling (download/train/supply)",
    })
    n_sel = sum(1 for s in selected if s["status"] == "selected")
    return {"n_selected": n_sel, "n_rows": len(selected), "rows": selected}

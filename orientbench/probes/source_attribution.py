"""A4 causal orientation-evidence attribution mechanism (smoke).

Uses the FROZEN O2-RTDETR (A4) host predictions matched to GT to relate
orientation risk to candidate evidence sources: GV-obliquity, layout source
(E_layout), selection score, and angle-entropy proxy. Computes partial
correlation (controlling for GV + class) and HSIC dependence (permutation
p-value, controlled sampling) with bootstrap CIs. Background source needs raster
images and is marked unavailable in this smoke. NOT a formal A4 conclusion.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List

import numpy as np

from orientbench.buckets.sources import compute_layout_for_image
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.dependence import bootstrap_ci, hsic, partial_correlation
from orientbench.metrics.gv import gv_obliquity
from orientbench.metrics.matching import match_dataset


def _class_dummies(classes: List[str]) -> np.ndarray:
    uniq = sorted(set(classes))
    idx = {c: i for i, c in enumerate(uniq)}
    M = np.zeros((len(classes), max(1, len(uniq) - 1)))
    for r, c in enumerate(classes):
        k = idx[c]
        if k < M.shape[1]:
            M[r, k] = 1.0
    return M


def source_attribution_smoke(preds, gts, image_ids, score_thr: float = 0.30,
                             seed: int = 0) -> Dict[str, Any]:
    pset = [p for p in preds if p["image_id"] in image_ids and p["score"] >= score_thr]
    gset = [g for g in gts if g["image_id"] in image_ids]
    # layout source per image on GT
    by_img = defaultdict(list)
    for g in gset:
        by_img[g["image_id"]].append(g)
    gid_to_layout = {}
    for img, gobs in by_img.items():
        lay = compute_layout_for_image(gobs)
        for g, l in zip(gobs, lay):
            gid_to_layout[id(g)] = l

    m = match_dataset(pset, gset)
    rows = {"orient_risk": [], "gv_needed": [], "E_layout": [], "score": [],
            "entropy": [], "klass": [], "near_square": []}
    for p_idx, g_idx, _ in m["matched_pairs"]:
        p, g = pset[p_idx], gset[g_idx]
        c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"],
                                 g["obb_w"], g["obb_h"], g["obb_theta"])
        risk = c["angle_error_canonical_longside"]
        if not math.isfinite(risk):
            continue
        gv = gv_obliquity(g["obb_w"], g["obb_h"], g["obb_theta"])["gv_obb_needed"]
        lay = gid_to_layout.get(id(g), {})
        sc = float(p["score"])
        rows["orient_risk"].append(risk)
        rows["gv_needed"].append(gv if math.isfinite(gv) else 0.0)
        rows["E_layout"].append(lay.get("E_layout", 0.0) if math.isfinite(lay.get("E_layout", 0.0)) else 0.0)
        rows["score"].append(sc)
        rows["entropy"].append(-math.log(min(max(sc, 1e-6), 1.0)))
        rows["klass"].append(g["class_name"])
        rows["near_square"].append(bool(c["near_square"]))

    # mask near-square for the orientation-risk relationships
    keep = [i for i, ns in enumerate(rows["near_square"]) if not ns]
    def arr(k):
        return np.array([rows[k][i] for i in keep], dtype=float)
    n = len(keep)
    out = {"n_matched": m["n_matched"], "n_used": n, "n_near_square_masked": len(rows["near_square"]) - n,
           "background_source": "unavailable_in_smoke (needs raster images)", "sources": {}}
    if n < 8:
        out["status"] = "insufficient_samples"
        return out
    risk = arr("orient_risk"); gv = arr("gv_needed"); klass = [rows["klass"][i] for i in keep]
    Zbase = np.column_stack([gv, _class_dummies(klass)])
    for src in ("E_layout", "score", "entropy", "gv_needed"):
        x = arr(src)
        # partial corr controlling for GV (+class), except for gv itself control class only
        Z = _class_dummies(klass) if src == "gv_needed" else Zbase
        pc = partial_correlation(x, risk, Z)
        h = hsic(x, risk, max_samples=800, n_perm=200, seed=seed)
        ci = bootstrap_ci((x - x.mean()) * (risk - risk.mean()), n_boot=400, seed=seed)
        out["sources"][src] = {
            "partial_corr_vs_orient_risk": round(pc, 4) if math.isfinite(pc) else None,
            "hsic": round(h["hsic"], 6) if math.isfinite(h["hsic"]) else None,
            "hsic_p_value": h["p_value"], "hsic_truncated": h["truncated"],
            "bootstrap_cov_ci": [round(ci["lo"], 4), round(ci["hi"], 4)],
        }
    # per-class orientation risk summary
    per_class = {}
    cc = defaultdict(list)
    for i in keep:
        cc[rows["klass"][i]].append(rows["orient_risk"][i])
    for k, v in sorted(cc.items()):
        per_class[k] = {"n": len(v), "median_orient_err_deg": round(float(np.median(v)), 3)}
    out["per_class"] = per_class
    out["status"] = "smoke_ok"
    out["seed"] = seed
    return out

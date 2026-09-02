"""C1 cross-view responsibility mechanism (smoke).

Uses the FROZEN RHINO host predictions vs GT (and a deterministic synthetic view
transform) to exercise the C1/B mechanism primitives: OT matching with dustbin,
GT-identity control (R1), responsibility, DropRate, view-consistency risk, and a
failure taxonomy. With no real multi-view capture, the cross-view is a
deterministic geometric transform — labelled synthetic_view_transform_for_
mechanism_smoke. NOT a formal C1 conclusion.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List

import numpy as np

from orientbench.metrics.angle_contract import angle_error_contract, is_near_square
from orientbench.metrics.drop_rate import drop_rate, view_consistency_risk
from orientbench.metrics.matching import match_image
from orientbench.metrics.ot_dustbin import obb_match_cost, sinkhorn_dustbin

HALF_PI = math.pi / 2.0


def _rotate90(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic synthetic view transform: rotate orientation by +90deg."""
    o = dict(obj)
    o["obb_theta"] = ((obj["obb_theta"] + HALF_PI + HALF_PI) % math.pi) - HALF_PI
    return o


def cross_view_smoke(preds: List[Dict[str, Any]], gts: List[Dict[str, Any]],
                     image_ids: set, score_thr: float = 0.30) -> Dict[str, Any]:
    by_img_p, by_img_g = defaultdict(list), defaultdict(list)
    for p in preds:
        if p["image_id"] in image_ids and p["score"] >= score_thr:
            by_img_p[p["image_id"]].append(p)
    for g in gts:
        if g["image_id"] in image_ids:
            by_img_g[g["image_id"]].append(g)

    dust_masses, ot_matched, gt_ident_matched = [], 0, 0
    n_gt_total, n_responsible = 0, 0
    vc_pairs, synth_dust = [], []
    fail_tax = defaultdict(int)
    n_masked = 0
    for img, gobs in by_img_g.items():
        pobs = by_img_p.get(img, [])
        n_gt_total += len(gobs)
        if not pobs or not gobs:
            fail_tax["no_pred_or_gt"] += len(gobs)
            continue
        # OT pred<->GT with dustbin
        C = obb_match_cost(pobs, gobs)
        DUSTBIN_COST = 0.6
        ot = sinkhorn_dustbin(C, dustbin_cost=DUSTBIN_COST, reg=0.05)
        dust_masses.append(ot["dustbin_mass"])
        # responsibility (robust, cost-threshold dustbin): GT j is responsible-matched
        # iff its lowest-cost prediction is below the dustbin cost.
        used = set()
        for j, g in enumerate(gobs):
            order = np.argsort(C[:, j])
            i = next((int(k) for k in order if int(k) not in used), -1)
            responsible = i >= 0 and C[i, j] < DUSTBIN_COST
            if responsible:
                used.add(i)
                n_responsible += 1
                ot_matched += 1
                p = pobs[i]
                c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"],
                                         g["obb_w"], g["obb_h"], g["obb_theta"])
                if c["near_square"]:
                    n_masked += 1
                else:
                    vc_pairs.append({"a": p, "b": g})
                    if c["angle_error_canonical_longside"] > 10:
                        fail_tax["high_orientation_risk"] += 1
            else:
                fail_tax["dropped_no_responsibility"] += 1
                if is_near_square(g["obb_w"], g["obb_h"]):
                    fail_tax["dropped_near_square"] += 1
        # GT-identity control: IoU greedy matching
        rows = match_image(pobs, gobs)
        gt_ident_matched += sum(1 for r in rows if r["match_status"] == "matched")
        # synthetic cross-view: pred(view A) vs rotate90(GT) (view B) -> responsibility under transform
        gobs_b = [_rotate90(g) for g in gobs]
        Cb = obb_match_cost(pobs, gobs_b)
        synth_dust.append(sinkhorn_dustbin(Cb, dustbin_cost=1.0, reg=0.1)["dustbin_mass"])

    vc = view_consistency_risk(vc_pairs)
    dr = drop_rate(n_gt_total, n_responsible)
    # GT-identity tie: OT responsibility ~ GT-identity matching count
    ot_vs_ident = abs(ot_matched - gt_ident_matched) / max(1, gt_ident_matched)
    return {
        "n_images": len(by_img_g), "n_gt": n_gt_total, "n_responsible": n_responsible,
        "ot_matched": ot_matched, "gt_identity_matched": gt_ident_matched,
        "ot_vs_gt_identity_reldiff": round(ot_vs_ident, 4),
        "ot_dustbin_mass_mean": round(float(np.mean(dust_masses)), 4) if dust_masses else None,
        "drop_rate": round(dr, 4) if math.isfinite(dr) else None,
        "view_consistency_orient_err_median_deg": round(vc["median"], 3) if vc["n"] else None,
        "view_consistency_n": vc["n"], "n_near_square_masked": n_masked,
        "synthetic_view_dustbin_mass_mean": round(float(np.mean(synth_dust)), 4) if synth_dust else None,
        "failure_taxonomy": dict(fail_tax),
        "synthetic_view_transform_for_mechanism_smoke": True,
        "missing_real_cross_view_pairs": True,
    }

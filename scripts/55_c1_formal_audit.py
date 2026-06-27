#!/usr/bin/env python3
"""55_c1_formal_audit.py — C1 augmentation-view consistency FORMAL gate on D_audit.

Applies the FROZEN C1 thresholds (read-only) to D_audit; never mutates them.
Verdict: formal_pass / formal_fail / formal_blocked, scoped to augmentation-view
(NOT genuine physical multi-view). Run with mr_dev1x.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
import yaml

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
from orientbench.io.reports import read_jsonl, write_csv  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract, is_near_square  # noqa: E402
from orientbench.metrics.dependence import bootstrap_ci  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.ot_dustbin import obb_match_cost, sinkhorn_dustbin  # noqa: E402
from orientbench.metrics.matching import match_image  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

RDIR = os.path.join(PROOT, "outputs/probes/c1_cross_view_real")
VIEW_A = os.path.join(PROOT, "outputs/predictions/DOTA-v1.0/rhino/schema/pred_rhino_val.jsonl")
VIEW_B = os.path.join(RDIR, "view_b_unrotated.jsonl")
GT = os.path.join(PROOT, "outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl")
CKPT = os.path.join(PROOT, "outputs/training/rhino/best_dota_mAP_epoch_35.pth")
REP = os.path.join(PROOT, "outputs/bench_core/reports")
FDIR = os.path.join(PROOT, "outputs/probes/c1_cross_view_formal")
SCORE_THR = 0.30


def rmap(preds, gts):
    pset = [p for p in preds if p["score"] >= SCORE_THR]
    out = {}
    for p_idx, g_idx, _ in match_dataset(pset, gts)["matched_pairs"]:
        out[g_idx] = pset[p_idx]
    return out, pset


def main():
    os.makedirs(FDIR, exist_ok=True)
    thr = yaml.safe_load(open(os.path.join(PROOT, "configs/thresholds.yaml")))
    c1 = thr["B_C1"]
    assert c1["status"] == "frozen" and c1["gate_name"] == "C1_augmentation_view_consistency"
    p90_max = c1["view_consistency_p90_deg_max"]; drop_max = c1["drop_rate_across_views_max"]
    ck = hashlib.sha256(open(CKPT, "rb").read()).hexdigest()[:16]
    assert ck.startswith("55a90abb"), f"RHINO hash mismatch {ck}"
    A = read_jsonl(VIEW_A); B = read_jsonl(VIEW_B); G = read_jsonl(GT)
    if not B:
        print("[blocked] no view_b"); return
    by = defaultdict(lambda: {"a": [], "b": [], "g": []})
    for p in A: by[p["image_id"]]["a"].append(p)
    for p in B: by[p["image_id"]]["b"].append(p)
    for g in G: by[g["image_id"]]["g"].append(g)
    ids = {i for i in by if assign_split(i) == "D_audit"}

    vc_errs, vc_class = [], defaultdict(list)
    n_gt = n_drop = n_both = n_masked = 0
    dust = []; ot_resp = 0; gt_ident = 0
    fail = defaultdict(int)
    for img in ids:
        d = by[img]
        if not d["g"]:
            continue
        ra, pa = rmap(d["a"], d["g"]); rb, _ = rmap(d["b"], d["g"])
        n_gt += len(d["g"])
        for j, g in enumerate(d["g"]):
            ina, inb = j in ra, j in rb
            if ina and inb:
                n_both += 1
                if is_near_square(g["obb_w"], g["obb_h"]):
                    n_masked += 1; continue
                c = angle_error_contract(ra[j]["obb_w"], ra[j]["obb_h"], ra[j]["obb_theta"],
                                         rb[j]["obb_w"], rb[j]["obb_h"], rb[j]["obb_theta"])
                e = c["angle_error_canonical_longside"]
                if math.isfinite(e):
                    vc_errs.append(e); vc_class[g["class_name"]].append(e)
                    if e > 10: fail["high_view_inconsistency"] += 1
            else:
                n_drop += 1
                if not ina and not inb: fail["dropped_both_views"] += 1
                elif is_near_square(g["obb_w"], g["obb_h"]): fail["dropped_near_square"] += 1
        # OT dustbin between view A and view B preds (cross-view responsibility)
        if pa and d["b"]:
            pb = [p for p in d["b"] if p["score"] >= SCORE_THR]
            if pb:
                C = obb_match_cost(pa, pb)
                dust.append(sinkhorn_dustbin(C, dustbin_cost=0.6, reg=0.05)["dustbin_mass"])
        # OT vs GT-identity: responsibility count vs IoU-matching count
        ot_resp += len(ra)
        gt_ident += sum(1 for r in match_image([p for p in d["a"] if p["score"] >= SCORE_THR], d["g"])
                        if r["match_status"] == "matched")

    vc = np.array(vc_errs)
    p90 = float(np.percentile(vc, 90)) if vc.size else float("nan")
    drop_rate = n_drop / n_gt if n_gt else float("nan")
    ci = bootstrap_ci(vc, stat_fn=lambda v: np.percentile(v, 90), n_boot=400, seed=0)
    ot_vs_ident = abs(ot_resp - gt_ident) / max(1, gt_ident)
    passed = bool(math.isfinite(p90) and p90 <= p90_max and math.isfinite(drop_rate) and drop_rate <= drop_max)
    verdict = "formal_pass" if passed else "formal_fail"
    per_class = {k: round(float(np.median(v)), 3) for k, v in sorted(vc_class.items())}

    row = {"gate": "C1_augmentation_view_consistency", "host": "RHINO", "host_sha256": ck,
           "split": "D_audit", "n_gt": n_gt, "n_both_views": n_both, "n_used": int(vc.size),
           "view_consistency_p90_deg": round(p90, 3), "p90_max_threshold": p90_max,
           "p90_bootstrap_ci": f"[{round(ci['lo'],3)},{round(ci['hi'],3)}]",
           "drop_rate": round(drop_rate, 4), "drop_rate_max_threshold": drop_max,
           "ot_dustbin_mass_mean": round(float(np.mean(dust)), 4) if dust else None,
           "ot_vs_gt_identity_reldiff": round(ot_vs_ident, 4),
           "near_square_masked": n_masked, "verdict": verdict,
           "scope": "augmentation_view_only_NOT_genuine_physical_multiview"}
    write_csv(os.path.join(REP, "c1_formal_audit.csv"), [row], list(row.keys()))
    json.dump({"row": row, "failure_taxonomy": dict(fail), "per_class_median_err": per_class},
              open(os.path.join(FDIR, "c1_formal_detail.json"), "w"), indent=2, ensure_ascii=False)
    L = ["# C1 Formal Audit — D_audit (augmentation-view consistency)", "",
         f"> RHINO frozen sha256 {ck}…; frozen thresholds applied (NOT mutated); D_audit holdout.",
         f"> **scope: augmentation-view only — NOT genuine physical multi-view evidence.**", "",
         f"## VERDICT: **{verdict}** {'(within augmentation-view scope only; not genuine physical multi-view)' if passed else ''}",
         "",
         f"- view-consistency p90 = **{round(p90,3)}°** (threshold <= {p90_max}; bootstrap CI {row['p90_bootstrap_ci']})",
         f"- DropRate across views = **{round(drop_rate,4)}** (threshold <= {drop_max})",
         f"- OT dustbin mass mean = {row['ot_dustbin_mass_mean']}; OT vs GT-identity reldiff = {row['ot_vs_gt_identity_reldiff']}",
         f"- both-views responsible = {n_both}; near-square masked = {n_masked}",
         f"- failure taxonomy: {dict(fail)}",
         f"- per-class median view-consistency err (deg): {per_class}",
         "", "## 边界", "- formal_pass 仅在 augmentation-view scope；**不是** genuine physical multi-view 证据；DOTA partial；阈值未调。"]
    open(os.path.join(REP, "c1_formal_audit.md"), "w").write("\n".join(L) + "\n")
    print(f"[C1 formal] verdict={verdict} p90={round(p90,3)}<={p90_max} drop={round(drop_rate,4)}<={drop_max}")


if __name__ == "__main__":
    main()

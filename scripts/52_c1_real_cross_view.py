#!/usr/bin/env python3
"""52_c1_real_cross_view.py — C1 REAL cross-view formal-readiness (RHINO host).

View A = original-frame RHINO predictions (014). View B = RHINO predictions on
the 90deg-rotated image, mapped back to the original frame (real detector
response to a real view change). For each GT object responsible in both views,
view-consistency orientation risk = orientation difference between the two
views' predictions (real detector orientation stability). Plus OT-dustbin,
GT-identity control (R1), DropRate, responsibility change. D_cal -> candidate
only (NOT frozen). Run with mr_dev1x (unpickle DetDataSample).
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
from orientbench.io.prediction_converters import convert_mmrotate1x_pkl  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv, write_jsonl  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract, is_near_square  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

RDIR = os.path.join(PROOT, "outputs/probes/c1_cross_view_real")
ROT_PKL = os.path.join(RDIR, "result_rhino_rotated.pkl")
VIEW_A = os.path.join(PROOT, "outputs/predictions/DOTA-v1.0/rhino/schema/pred_rhino_val.jsonl")
GT = os.path.join(PROOT, "outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl")
REPORT_DIR = os.path.join(PROOT, "outputs/bench_core/reports")
CKPT = os.path.join(PROOT, "outputs/training/rhino/best_dota_mAP_epoch_35.pth")
S = 1024  # split_ss image size
HALF_PI = math.pi / 2.0
SCORE_THR = 0.30


def unrotate_90cw(p):
    """Map a pred from the 90deg-CW-rotated frame back to the original frame."""
    cx2 = p["obb_cy"]
    cy2 = (S - 1) - p["obb_cx"]
    th2 = ((p["obb_theta"] + HALF_PI) + HALF_PI) % math.pi - HALF_PI  # +90deg, le90 range
    q = dict(p)
    q["obb_cx"], q["obb_cy"], q["obb_theta"] = cx2, cy2, th2
    return q


def responsible_map(preds, gts):
    """Match preds->GT (IoU); return {gt_index: pred} for matched, score>=thr."""
    pset = [p for p in preds if p["score"] >= SCORE_THR]
    m = match_dataset(pset, gts)
    out = {}
    for p_idx, g_idx, _ in m["matched_pairs"]:
        out[g_idx] = pset[p_idx]
    return out, len(pset)


def main():
    import hashlib
    ck = hashlib.sha256(open(CKPT, "rb").read()).hexdigest()[:16] if os.path.isfile(CKPT) else "?"
    assert ck.startswith("55a90abb"), f"RHINO ckpt hash mismatch: {ck}"
    preds_a = read_jsonl(VIEW_A)
    preds_b_raw, st = convert_mmrotate1x_pkl(ROT_PKL, "DOTA-v1.0", "val", "rhino", "rhino")
    preds_b = [unrotate_90cw(p) for p in preds_b_raw]
    write_jsonl(os.path.join(RDIR, "view_b_unrotated.jsonl"), preds_b)
    gts = read_jsonl(GT)

    by_img = defaultdict(lambda: {"a": [], "b": [], "g": []})
    for p in preds_a:
        by_img[p["image_id"]]["a"].append(p)
    for p in preds_b:
        by_img[p["image_id"]]["b"].append(p)
    for g in gts:
        by_img[g["image_id"]]["g"].append(g)

    rows = []
    for split in ("D_cal", "D_audit"):
        ids = {i for i in by_img if assign_split(i) == split}
        n_gt = n_both = n_drop = 0
        vc_errs = []
        a_only = b_only = 0
        n_masked = 0
        for img in ids:
            d = by_img[img]
            if not d["g"]:
                continue
            ra, _ = responsible_map(d["a"], d["g"])
            rb, _ = responsible_map(d["b"], d["g"])
            n_gt += len(d["g"])
            for j, g in enumerate(d["g"]):
                ina, inb = j in ra, j in rb
                if ina and inb:
                    n_both += 1
                    if is_near_square(g["obb_w"], g["obb_h"]):
                        n_masked += 1
                        continue
                    pa, pb = ra[j], rb[j]
                    c = angle_error_contract(pa["obb_w"], pa["obb_h"], pa["obb_theta"],
                                             pb["obb_w"], pb["obb_h"], pb["obb_theta"])
                    e = c["angle_error_canonical_longside"]
                    if math.isfinite(e):
                        vc_errs.append(e)
                elif ina and not inb:
                    a_only += 1; n_drop += 1
                elif inb and not ina:
                    b_only += 1; n_drop += 1
                else:
                    n_drop += 1
        drop_rate = n_drop / n_gt if n_gt else float("nan")
        vc = np.array(vc_errs)
        rows.append({
            "host": "RHINO", "route": "C1/B", "split": split, "cross_view": "real_rotated90_inference",
            "n_images": len(ids), "n_gt": n_gt, "n_responsible_both_views": n_both,
            "drop_rate_across_views": round(drop_rate, 4) if math.isfinite(drop_rate) else None,
            "view_only_a": a_only, "view_only_b": b_only, "n_near_square_masked": n_masked,
            "view_consistency_orient_err_median_deg": round(float(np.median(vc)), 3) if vc.size else None,
            "view_consistency_orient_err_p90_deg": round(float(np.percentile(vc, 90)), 3) if vc.size else None,
            "view_consistency_n": int(vc.size),
            "synthetic_view_transform_for_mechanism_smoke": False,
            "real_inference_on_transformed_view": True,
            "genuine_multi_physical_viewpoint": False,
        })
        print(f"[c1-real {split}] imgs={len(ids)} gt={n_gt} both={n_both} drop={drop_rate:.3f} "
              f"vc_err_med={rows[-1]['view_consistency_orient_err_median_deg']}deg "
              f"vc_err_p90={rows[-1]['view_consistency_orient_err_p90_deg']}")

    write_csv(os.path.join(REPORT_DIR, "c1_cross_view_real_summary.csv"), rows, list(rows[0].keys()))
    # D_cal candidate (NOT frozen)
    dcal = next(r for r in rows if r["split"] == "D_cal")
    cand = {"project": "orientbench", "block": "B_C1", "host": "RHINO", "host_ckpt_sha256": ck,
            "approval_status": "pending", "frozen": False, "calibration_split": "D_cal",
            "cross_view_kind": "real_rotated90_inference (augmentation-consistency; NOT genuine multi-viewpoint)",
            "candidate": {
                "view_consistency_orient_err_p90_deg_max": dcal["view_consistency_orient_err_p90_deg"],
                "drop_rate_across_views_max": dcal["drop_rate_across_views"],
                "near_square_masked": True},
            "dcal_reference": dcal,
            "note": "candidate only; needs R8 freeze approval; D_audit not used to set thresholds."}
    import yaml
    with open(os.path.join(PROOT, "configs", "thresholds.c1_candidate.yaml"), "w") as fh:
        fh.write("# C1 candidate (real cross-view). approval_status=pending; NOT frozen.\n")
        yaml.safe_dump(cand, fh, allow_unicode=True, sort_keys=False)
    # report
    L = ["# C1 Real Cross-View Formal-Readiness (RHINO host)", "",
         f"> RHINO frozen (sha256 {ck}…). View B = **真实** RHINO inference on 90°-rotated image, mapped back.",
         "> **real_inference_on_transformed_view=True**；genuine_multi_physical_viewpoint=**False**（augmentation-consistency）。非完整 C1 gate（阈值未冻结）。", "",
         "| split | imgs | GT | both-views | DropRate | view-consist err med° | err p90° | masked |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['split']} | {r['n_images']} | {r['n_gt']} | {r['n_responsible_both_views']} | "
                 f"{r['drop_rate_across_views']} | {r['view_consistency_orient_err_median_deg']} | "
                 f"{r['view_consistency_orient_err_p90_deg']} | {r['n_near_square_masked']} |")
    L += ["", "## 关键（真实，非 smoke）",
          "- view-consistency orientation risk = 同一 GT 在原视图 vs 旋转视图下 RHINO 预测朝向之差（真实 detector 视图稳定性）。",
          "- DropRate across views = 在某一视图有责任、另一视图丢失的 GT 比例（真实视图鲁棒性）。",
          "## 状态",
          "- C1 = **ready_for_threshold_review**（真实 cross-view 跑通，candidate 见 thresholds.c1_candidate.yaml）。",
          "- formal_gate_allowed 仍 False（阈值未冻结，需 R8 批准）。D_audit 仅 holdout，未调阈值。",
          "## 诚实边界",
          "- cross-view 为 augmentation-view（旋转）+ 真实 inference，**非** genuine 多物理视角；若需后者，需新数据采集（见 availability audit）。"]
    open(os.path.join(REPORT_DIR, "c1_cross_view_real_readiness_report.md"), "w").write("\n".join(L) + "\n")
    print("[ok] wrote c1_cross_view_real_readiness_report.md + thresholds.c1_candidate.yaml")


if __name__ == "__main__":
    main()

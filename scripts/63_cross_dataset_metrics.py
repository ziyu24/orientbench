#!/usr/bin/env python3
"""63_cross_dataset_metrics.py — cross-dataset exploratory metrics (021).

HRSC2016 (real OBB GT via mmrotate HRSCDataset, le90) is the one runnable cell;
angle_error_gate_status=blocked_angle_uncertain (raw mbox->le90 not formally
resolved; mAP 0.906 recorded as consistency sanity). DIOR-R (only HBB GT) and
FAIR1M (empty/missing GT) -> blocked_missing_obb_gt. All EXPLORATORY, no formal
gate, no threshold change. Run with mr_dev1x.
"""
from __future__ import annotations

import math
import os
import pickle
import sys
from collections import defaultdict

import numpy as np

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
from orientbench.io.predictions import validate_predictions  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv, write_jsonl  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402

REP = os.path.join(P, "outputs", "bench_core", "reports")
PRED = os.path.join(P, "outputs", "predictions")
SCORE_THR = 0.30


def convert_hrsc(pkl_path, classes=("ship",)):
    data = pickle.load(open(pkl_path, "rb"))
    preds = []
    for rec in data:
        img = rec.get("img_id") if isinstance(rec, dict) else getattr(rec, "img_id", None)
        pi = rec.get("pred_instances") if isinstance(rec, dict) else getattr(rec, "pred_instances", None)
        if pi is None:
            continue
        bboxes = pi["bboxes"] if isinstance(pi, dict) else pi.bboxes
        scores = pi["scores"] if isinstance(pi, dict) else pi.scores
        labels = pi["labels"] if isinstance(pi, dict) else pi.labels
        bboxes = np.asarray(bboxes.cpu() if hasattr(bboxes, "cpu") else bboxes)
        scores = np.asarray(scores.cpu() if hasattr(scores, "cpu") else scores)
        labels = np.asarray(labels.cpu() if hasattr(labels, "cpu") else labels)
        for b, s, l in zip(bboxes, scores, labels):
            cx, cy, w, h, th = [float(x) for x in b[:5]]
            preds.append({"image_id": str(img), "class_name": classes[int(l)] if int(l) < len(classes) else "ship",
                          "obb_cx": cx, "obb_cy": cy, "obb_w": w, "obb_h": h, "obb_theta": th,
                          "score": float(s), "is_synthetic": False, "not_detector_output": False,
                          "detector_id": "oriented_rcnn_lsknet", "baseline_id": "13",
                          "dataset": "HRSC2016", "split": "test", "angle_version": "le90",
                          "source_path": pkl_path, "converter_version": "hrsc_v1", "warnings": ""})
    return preds


def metrics_for(preds, gts):
    pset = [p for p in preds if p["score"] >= SCORE_THR]
    m = match_dataset(pset, gts)
    scores, risk, masked = [], [], 0
    for p_idx, g_idx, _ in m["matched_pairs"]:
        p, g = pset[p_idx], gts[g_idx]
        c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"], g["obb_w"], g["obb_h"], g["obb_theta"])
        if c["near_square"]:
            masked += 1; continue
        e = c["angle_error_canonical_longside"]
        if math.isfinite(e):
            scores.append(p["score"]); risk.append(e)
    rc = risk_coverage_summary(np.array(scores), np.array(risk)) if scores else {}
    nr = nrc_auc(np.array(scores), np.array(risk)) if scores else {}
    return {"n_pred": len(pset), "n_matched": m["n_matched"], "n_used": len(scores), "n_masked": masked,
            "median_orient_err_deg": round(float(np.median(risk)), 3) if risk else None,
            "Risk@70": round(rc.get("risk_at_70", float("nan")), 4) if scores else None,
            "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if scores else None,
            "AURC": round(rc.get("aurc", float("nan")), 4) if scores else None,
            "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (scores and math.isfinite(nr.get("nrc_auc", float("nan")))) else None}


def main():
    rows, fails = [], []
    # HRSC2016 — real cell, angle uncertain
    pkl = f"{PRED}/HRSC2016/13/raw/result_b13.pkl"
    gtp = f"{PRED}/HRSC2016/_hrsc_gt.jsonl"
    if os.path.isfile(pkl) and os.path.isfile(gtp):
        preds = convert_hrsc(pkl)
        os.makedirs(f"{PRED}/HRSC2016/13/schema", exist_ok=True)
        write_jsonl(f"{PRED}/HRSC2016/13/schema/pred_b13_test.jsonl", preds)
        v = validate_predictions(preds)
        gts = read_jsonl(gtp)
        mt = metrics_for(preds, gts)
        rows.append({"dataset": "HRSC2016", "archetype": "lsknet_backbone", "baseline_id": "13",
                     "detector": "oriented_rcnn_lsknet", "n_pred": len(preds), "n_schema_ok": v["n_ok"],
                     "formal_scope": "cross_dataset_exploratory",
                     "angle_error_gate_status": "blocked_angle_uncertain",
                     "map_sanity": 0.9061, **mt})
        print(f"[HRSC] n_used={mt['n_used']} med_err={mt['median_orient_err_deg']} NRC={mt['NRC_AUC']} "
              f"(angle_uncertain; mAP sanity 0.906)")
    else:
        fails.append({"cell": "HRSC2016/lsknet/13", "reason": "missing pkl or gt"})
    # DIOR-R + FAIR1M -> GT-blocked
    fails.append({"cell": "DIOR-R/*", "reason": "blocked_missing_obb_gt (only HBB xml; obb annfiles empty)"})
    fails.append({"cell": "FAIR1M-v1.0/*", "reason": "blocked_missing_gt (val_20 annfiles empty; split_ss path absent)"})

    write_csv(os.path.join(REP, "cross_dataset_metrics_021.csv"),
              rows or [{"dataset": "none"}], list(rows[0].keys()) if rows else ["dataset"])
    write_csv(os.path.join(REP, "cross_dataset_failures_021.csv"), fails, ["cell", "reason"])
    L = ["# Cross-Dataset Exploratory Metrics (021)", "",
         "> ALL exploratory; no formal gate; thresholds unchanged. env solved in 020; "
         "cross-dataset blocker is now GT availability / angle convention, not env.", "",
         "| dataset | archetype | baseline | n_used | median_orient_err° | Risk@90 | NRC-AUC | angle_gate | mAP sanity | scope |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['dataset']} | {r['archetype']} | {r['baseline_id']} | {r['n_used']} | "
                 f"{r['median_orient_err_deg']} | {r['Risk@90']} | {r['NRC_AUC']} | "
                 f"**{r['angle_error_gate_status']}** | {r['map_sanity']} | {r['formal_scope']} |")
    L += ["", "## blocked", "- DIOR-R: only HBB xml GT (annfiles/obb empty) -> blocked_missing_obb_gt（无 OBB 角度 GT，朝向 metrics 不可算）。",
          "- FAIR1M-v1.0: val_20 annfiles empty + split_ss_fair1m1.0 路径缺失 -> blocked_missing_gt。",
          "## HRSC angle 状态",
          "- mAP=0.906（与 baseline 一致）证明 mmrotate HRSCDataset 的 mbox->le90 内部一致、pred/GT 同 convention；",
          "  但 raw mbox->le90 等价未做正式 read-only 证明 -> **angle_error_gate_status=blocked_angle_uncertain**；orientation err 仅 exploratory，不冻结、不 formal。"]
    open(os.path.join(REP, "cross_dataset_metrics_021.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] cross-dataset metrics: {len(rows)} real cell(s), {len(fails)} blocked")


if __name__ == "__main__":
    main()

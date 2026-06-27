#!/usr/bin/env python3
"""61_full_matrix_metrics.py — convert new cells to schema + validate + metrics (019).

For each available/new matrix cell: convert raw pkl -> 17-field schema (if absent),
run validator, then matching + canonical orientation risk + Risk@70/90 + AURC +
NRC-AUC + near-square mask + per-class on the cell's GT subset. DOTA = formal-
compatible (thresholds NOT changed); non-DOTA = cross_dataset_exploratory.
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict

import numpy as np

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
from orientbench.io.prediction_converters import convert_mmrotate1x_pkl  # noqa: E402
from orientbench.io.predictions import validate_predictions  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv, write_jsonl  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402

REP = os.path.join(P, "outputs", "bench_core", "reports")
PRED = os.path.join(P, "outputs", "predictions")
SCORE_THR = 0.30

# cell registry: (archetype, dataset, baseline_id, raw_pkl, schema_jsonl, gt, detector_id, formal_scope)
CELLS = [
    ("two_stage_oriented_rcnn", "DOTA-v1.0", "1", None,
     f"{PRED}/DOTA-v1.0/1/schema/pred_b1_DOTA-v1.0_val.jsonl",
     f"{PRED}/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl", "oriented_rcnn", "formal_compatible"),
    ("angle_coder_psc", "DOTA-v1.0", "20", None,
     f"{PRED}/DOTA-v1.0/20/schema/pred_b20_DOTA-v1.0_val.jsonl",
     f"{PRED}/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl", "rotated_retinanet_psc", "formal_compatible"),
    ("rotated_detr_rhino", "DOTA-v1.0", "rhino", None,
     f"{PRED}/DOTA-v1.0/rhino/schema/pred_rhino_val.jsonl",
     f"{PRED}/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl", "rhino_rotated_detr", "formal_compatible_locked_host"),
    ("hybrid_encoder_oriented_detr_a4", "DOTA-v1.5", "a4_host", None,
     f"{PRED}/DOTA-v1.5/a4_host/schema/pred_a4_host_val.jsonl",
     f"{PRED}/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl", "o2_rtdetr_hybrid_encoder", "formal_compatible_locked_host"),
    ("two_stage_oriented_rcnn", "DOTA-v1.5", "2", f"{PRED}/DOTA-v1.5/2/raw/result_b2.pkl",
     f"{PRED}/DOTA-v1.5/2/schema/pred_b2_val.jsonl",
     f"{PRED}/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl", "oriented_rcnn", "formal_compatible"),
    ("one_stage_rtmdet", "DOTA-v1.5", "33", f"{PRED}/DOTA-v1.5/33/raw/result_b33.pkl",
     f"{PRED}/DOTA-v1.5/33/schema/pred_b33_val.jsonl",
     f"{PRED}/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl", "rotated_rtmdet_s", "formal_compatible"),
    ("one_stage_rtmdet_m", "DOTA-v1.5", "39", f"{PRED}/DOTA-v1.5/39/raw/result_b39.pkl",
     f"{PRED}/DOTA-v1.5/39/schema/pred_b39_val.jsonl",
     f"{PRED}/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl", "rotated_rtmdet_m", "formal_compatible"),
    ("lsknet_backbone", "DOTA-v1.0", "7", f"{PRED}/DOTA-v1.0/7/raw/result_b7.pkl",
     f"{PRED}/DOTA-v1.0/7/schema/pred_b7_val.jsonl",
     f"{PRED}/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl", "oriented_rcnn_lsknet", "formal_compatible"),
    ("strip_rcnn", "DOTA-v1.0", "35", f"{PRED}/DOTA-v1.0/35/raw/result_b35.pkl",
     f"{PRED}/DOTA-v1.0/35/schema/pred_b35_val.jsonl",
     f"{PRED}/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl", "strip_rcnn", "formal_compatible"),
    ("weakly_supervised_h2rbox", "DOTA-v1.0", "70", f"{PRED}/DOTA-v1.0/70/raw/result_b70.pkl",
     f"{PRED}/DOTA-v1.0/70/schema/pred_b70_val.jsonl",
     f"{PRED}/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl", "h2rbox_v2", "weak_nonformal_metrics"),
]


def metrics_for(preds, gts):
    pset = [p for p in preds if p["score"] >= SCORE_THR]
    m = match_dataset(pset, gts)
    scores, risk, masked = [], [], 0
    cov_g, cov_m = defaultdict(int), defaultdict(int)
    for g in gts:
        cov_g[g["class_name"]] += 1
    for p_idx, g_idx, _ in m["matched_pairs"]:
        p, g = pset[p_idx], gts[g_idx]
        c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"],
                                 g["obb_w"], g["obb_h"], g["obb_theta"])
        if c["near_square"]:
            masked += 1
            continue
        e = c["angle_error_canonical_longside"]
        if math.isfinite(e):
            scores.append(p["score"]); risk.append(e); cov_m[g["class_name"]] += 1
    rc = risk_coverage_summary(np.array(scores), np.array(risk)) if scores else {}
    nr = nrc_auc(np.array(scores), np.array(risk)) if scores else {}
    per_class = {c: round(cov_m.get(c, 0) / cov_g[c], 3) for c in sorted(cov_g) if cov_g[c]}
    return {
        "n_pred": len(pset), "n_matched": m["n_matched"], "n_used": len(scores), "n_masked": masked,
        "median_orient_err_deg": round(float(np.median(risk)), 3) if risk else None,
        "Risk@70": round(rc.get("risk_at_70", float("nan")), 4) if scores else None,
        "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if scores else None,
        "AURC": round(rc.get("aurc", float("nan")), 4) if scores else None,
        "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (scores and math.isfinite(nr.get("nrc_auc", float("nan")))) else None,
        "per_class_coverage_n": len(per_class),
    }


def main():
    sval, smet, sfail = [], [], []
    for arch, ds, bid, raw, schema, gt, det, formal in CELLS:
        # convert if needed
        if not os.path.isfile(schema) and raw and os.path.isfile(raw):
            try:
                preds, st = convert_mmrotate1x_pkl(raw, ds, "val", det, bid)
                for p in preds:
                    p["not_detector_output"] = False
                os.makedirs(os.path.dirname(schema), exist_ok=True)
                write_jsonl(schema, preds)
            except Exception as e:
                sfail.append({"cell": f"{arch}/{ds}/{bid}", "stage": "convert", "error": str(e)[:120]})
                continue
        if not os.path.isfile(schema):
            sfail.append({"cell": f"{arch}/{ds}/{bid}", "stage": "convert", "error": "no schema/raw"})
            continue
        preds = read_jsonl(schema)
        v = validate_predictions(preds)
        sval.append({"archetype": arch, "dataset": ds, "baseline_id": bid, "detector": det,
                     "n_pred": len(preds), "n_schema_ok": v["n_ok"], "n_schema_bad": len(preds) - v["n_ok"],
                     "is_synthetic_false": all(not p.get("is_synthetic", False) for p in preds[:1000]),
                     "not_detector_output_false": all(not p.get("not_detector_output", False) for p in preds[:1000])})
        if not os.path.isfile(gt):
            sfail.append({"cell": f"{arch}/{ds}/{bid}", "stage": "metrics", "error": "no GT"}); continue
        gts = read_jsonl(gt)
        gimgs = {g["image_id"] for g in gts}
        preds_sub = [p for p in preds if p["image_id"] in gimgs]
        mt = metrics_for(preds_sub, gts)
        smet.append({"archetype": arch, "dataset": ds, "baseline_id": bid, "detector": det,
                     "formal_scope": formal, **mt})
        print(f"[cell] {arch}/{ds}/{bid}: n_used={mt['n_used']} med_err={mt['median_orient_err_deg']} "
              f"NRC={mt['NRC_AUC']} Risk@90={mt['Risk@90']}")

    write_csv(os.path.join(REP, "full_matrix_schema_validation.csv"), sval, list(sval[0].keys()) if sval else ["x"])
    write_csv(os.path.join(REP, "full_matrix_metrics_summary.csv"), smet, list(smet[0].keys()) if smet else ["x"])
    write_csv(os.path.join(REP, "full_matrix_failures.csv"), sfail or [{"cell": "none", "stage": "-", "error": "-"}],
              ["cell", "stage", "error"])
    L = ["# Full-Matrix Schema Validation", "", f"> cells={len(sval)}; all is_synthetic=false, not_detector_output=false.", "",
         "| archetype | dataset | baseline | detector | n_pred | schema_ok |", "|---|---|---|---|---|---|"]
    for r in sval:
        L.append(f"| {r['archetype']} | {r['dataset']} | {r['baseline_id']} | {r['detector']} | {r['n_pred']} | {r['n_schema_ok']} |")
    open(os.path.join(REP, "full_matrix_schema_validation.md"), "w").write("\n".join(L) + "\n")
    L = ["# Full-Matrix Metrics Summary", "", "> DOTA=formal-compatible(阈值未改); 非 DOTA=cross_dataset_exploratory.", "",
         "| archetype | dataset | baseline | n_used | median_orient_err° | Risk@70 | Risk@90 | AURC | NRC-AUC | scope |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in smet:
        L.append(f"| {r['archetype']} | {r['dataset']} | {r['baseline_id']} | {r['n_used']} | "
                 f"{r['median_orient_err_deg']} | {r['Risk@70']} | {r['Risk@90']} | {r['AURC']} | {r['NRC_AUC']} | {r['formal_scope']} |")
    L += ["", f"- failures: {len(sfail)} (见 full_matrix_failures.csv)"]
    open(os.path.join(REP, "full_matrix_metrics_summary.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] schema={len(sval)} metrics={len(smet)} failures={len(sfail)}")


if __name__ == "__main__":
    main()

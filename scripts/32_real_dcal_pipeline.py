#!/usr/bin/env python3
"""32_real_dcal_pipeline.py — real predictions -> schema -> D_cal/D_audit metrics
-> calibration candidate. Uses long-side canonical orientation error (angle
convention RESOLVED). Run with mr_dev1x interpreter (DetDataSample unpickle).

D5/D7 authorized. Outputs are non-formal (thresholds not frozen). No training.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orientbench.io.prediction_converters import convert_mmrotate1x_pkl  # noqa: E402
from orientbench.io.predictions import validate_predictions  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv, write_jsonl, write_json  # noqa: E402
from orientbench.metrics.angle import orientation_angle_error_deg  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRED = os.path.join(PROOT, "outputs", "predictions", "DOTA-v1.0")
REPORT_DIR = os.path.join(PROOT, "outputs", "bench_core", "reports")
GT_PATH = os.path.join(PRED, "_dcal_subset", "gt_mmrotate.jsonl")
CONVERTER_VERSION = "mmrotate1x_v1+longside_canon"

TARGETS = [
    {"baseline_id": "1", "detector_id": "oriented_rcnn_r50", "archetype": "two_stage_regression"},
    {"baseline_id": "20", "detector_id": "rotated_retinanet_psc_r50", "archetype": "angle_coder_psc"},
    {"baseline_id": "32", "detector_id": "rotated_rtmdet_s", "archetype": "one_stage_realtime"},
]
SCORE_THR = 0.30  # filter low-score preds for matching stats


def validate_schema(preds):
    issues = []
    if not preds:
        return ["empty"]
    cxs = [p["obb_cx"] for p in preds]; scs = [p["score"] for p in preds]
    if not all(math.isfinite(p["obb_cx"]) and math.isfinite(p["obb_theta"]) for p in preds):
        issues.append("non_finite_fields")
    if any(p["obb_w"] <= 0 or p["obb_h"] <= 0 for p in preds):
        issues.append("nonpositive_side")
    if min(cxs) < -50 or max(cxs) > 3000:
        issues.append(f"cx_out_of_range[{min(cxs):.0f},{max(cxs):.0f}]")
    if min(scs) < 0 or max(scs) > 1.001:
        issues.append("score_out_of_[0,1]")
    if np.std(scs) < 1e-6:
        issues.append("score_constant_suspicious")
    return issues


def split_metrics(preds, gts, image_ids):
    pset = [p for p in preds if p["image_id"] in image_ids and p["score"] >= SCORE_THR]
    gset = [g for g in gts if g["image_id"] in image_ids]
    m = match_dataset(pset, gts=gset)
    scores, risk = [], []
    cov_match = defaultdict(int); cov_gt = defaultdict(int)
    for g in gset:
        cov_gt[g["class_name"]] += 1
    for p_idx, g_idx, _iou in m["matched_pairs"]:
        p, g = pset[p_idx], gset[g_idx]
        err = orientation_angle_error_deg(p["obb_w"], p["obb_h"], p["obb_theta"],
                                          g["obb_w"], g["obb_h"], g["obb_theta"])
        if math.isfinite(err):
            scores.append(p["score"]); risk.append(err)
            cov_match[g["class_name"]] += 1
    rc = risk_coverage_summary(np.array(scores), np.array(risk)) if scores else {}
    nr = nrc_auc(np.array(scores), np.array(risk)) if scores else {}
    per_class = {c: {"gt": cov_gt[c], "matched": cov_match.get(c, 0),
                     "coverage": round(cov_match.get(c, 0) / cov_gt[c], 3) if cov_gt[c] else 0.0}
                 for c in sorted(cov_gt)}
    return {
        "n_pred": len(pset), "n_gt": len(gset), "n_matched": m["n_matched"],
        "n_unmatched_pred": len(pset) - m["n_matched"],
        "n_unmatched_gt": len(gset) - m["n_matched"],
        "median_orient_err_deg": round(float(np.median(risk)), 3) if risk else None,
        "mean_orient_err_deg": round(float(np.mean(risk)), 3) if risk else None,
        "AURC": round(rc.get("aurc", float("nan")), 4) if scores else None,
        "Risk@70": round(rc.get("risk_at_70", float("nan")), 4) if scores else None,
        "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if scores else None,
        "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (scores and math.isfinite(nr.get("nrc_auc", float("nan")))) else None,
        "per_class_coverage": per_class,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default="dcal")
    args = ap.parse_args(argv)
    os.makedirs(REPORT_DIR, exist_ok=True)
    gts = read_jsonl(GT_PATH)
    all_imgs = sorted({g["image_id"] for g in gts})
    dcal_imgs = {i for i in all_imgs if assign_split(i) == "D_cal"}
    daudit_imgs = {i for i in all_imgs if assign_split(i) == "D_audit"}

    summary_rows, fail_rows, cand = [], [], {}
    for t in TARGETS:
        bid = t["baseline_id"]
        pkl = os.path.join(PRED, bid, "raw", f"result_dcal_b{bid}.pkl")
        if not os.path.isfile(pkl):
            fail_rows.append({"baseline_id": bid, "detector_id": t["detector_id"],
                              "stage": "inference", "reason": "no result pkl"})
            continue
        try:
            preds, st = convert_mmrotate1x_pkl(pkl, "DOTA-v1.0", "val", t["detector_id"], bid)
        except Exception as e:  # noqa: BLE001
            fail_rows.append({"baseline_id": bid, "detector_id": t["detector_id"],
                              "stage": "convert", "reason": str(e)[:200]})
            continue
        for p in preds:
            p["not_detector_output"] = False
            p["converter_version"] = CONVERTER_VERSION
        issues = validate_schema(preds)
        v = validate_predictions(preds)
        schema_dir = os.path.join(PRED, bid, "schema"); os.makedirs(schema_dir, exist_ok=True)
        schema_path = os.path.join(schema_dir, f"pred_b{bid}_dcal.jsonl")
        write_jsonl(schema_path, preds)
        mc = split_metrics(preds, gts, dcal_imgs)
        ma = split_metrics(preds, gts, daudit_imgs)
        row = {
            "baseline_id": bid, "detector_id": t["detector_id"], "archetype": t["archetype"],
            "dataset": "DOTA-v1.0", "split": "val", "is_synthetic": False,
            "n_detections": st["n_detections"], "n_images": st["n_images"],
            "schema_valid": v["n_ok"], "schema_issues": ";".join(issues) or "none",
            "angle_version": "le90_longside_canonical", "angle_error_gate_status": "resolved_longside_canonical",
            "smoke_risk_validity": "valid_orientation_error_nonformal",
            "dcal_n_matched": mc["n_matched"], "dcal_median_orient_err_deg": mc["median_orient_err_deg"],
            "dcal_Risk@70": mc["Risk@70"], "dcal_Risk@90": mc["Risk@90"],
            "dcal_AURC": mc["AURC"], "dcal_NRC_AUC": mc["NRC_AUC"],
            "audit_n_matched": ma["n_matched"], "audit_median_orient_err_deg": ma["median_orient_err_deg"],
            "audit_Risk@90": ma["Risk@90"], "audit_NRC_AUC": ma["NRC_AUC"],
            "schema_path": schema_path, "not_formal_gate": True,
        }
        summary_rows.append(row)
        cand[bid] = {"detector_id": t["detector_id"], "archetype": t["archetype"],
                     "dcal": mc, "daudit": ma}
        print(f"[dcal] b{bid} {t['detector_id']}: dets={st['n_detections']} "
              f"D_cal matched={mc['n_matched']} med_err={mc['median_orient_err_deg']}deg "
              f"Risk@90={mc['Risk@90']} NRC={mc['NRC_AUC']} | issues={issues or 'none'}")

    # unresolved baselines (env registration) recorded as failures
    for bid, det, reason in [
        ("7", "oriented_rcnn_lsknet_s", "LSKNet backbone not registered in available mmrotate (needs LSKNet repo on path/install)"),
        ("14", "arsdetr_r50", "ARSDETR not registered (needs ARS-DETR fork mmrotate); DETR-like, NOT RHINO"),
        ("64", "point2rbox_v2", "weak/pseudo supervision; real inference semantics not standard test — skipped"),
    ]:
        fail_rows.append({"baseline_id": bid, "detector_id": det, "stage": "inference",
                          "reason": reason})

    write_csv(os.path.join(REPORT_DIR, "real_prediction_smoke_summary.csv"), summary_rows,
              list(summary_rows[0].keys()) if summary_rows else ["baseline_id"])
    write_csv(os.path.join(REPORT_DIR, "real_prediction_failures.csv"), fail_rows,
              ["baseline_id", "detector_id", "stage", "reason"])
    write_json(os.path.join(REPORT_DIR, "real_prediction_smoke_summary.json"),
               {"n_ok": len(summary_rows), "n_failed": len(fail_rows),
                "n_dcal_images": len(dcal_imgs), "n_audit_images": len(daudit_imgs),
                "n_gt_objects": len(gts), "angle_convention": "RESOLVED_longside_canonical",
                "label": "real_prediction_dcal", "rows": summary_rows})
    # calibration candidate yaml + report
    write_calibration_candidate(cand, len(dcal_imgs), len(daudit_imgs), args.timestamp)
    print(f"[ok] D_cal pipeline: {len(summary_rows)} baselines, "
          f"D_cal imgs={len(dcal_imgs)} D_audit imgs={len(daudit_imgs)}")
    return 0


def write_calibration_candidate(cand, n_cal, n_audit, ts):
    import yaml
    lines = {
        "project": "orientbench", "version": "v1.0-calibration-candidate",
        "proposed_by": "claude_dcal", "approval_status": "pending",
        "freeze_status": "not_frozen", "freeze_time": None,
        "angle_convention": "le90_longside_canonical (RESOLVED via mmrotate GT + long-side canonicalization)",
        "dataset": "DOTA-v1.0", "split": "val",
        "n_D_cal_images": n_cal, "n_D_audit_images": n_audit,
        "note": "基于真实 prediction 的 D_cal 观测；候选值待合作者批准 + R8 冻结；非正式 gate。",
        "observed_per_baseline": {},
        "candidate_thresholds": {
            "D2": {
                "selective_orientation_risk_at_90_deg_max": "TBD_from_D_cal (see observed Risk@90)",
                "nrc_auc_max": "TBD_from_D_cal",
            },
            "status": "draft_candidate",
        },
    }
    for bid, c in cand.items():
        lines["observed_per_baseline"][f"baseline_{bid}"] = {
            "detector_id": c["detector_id"], "archetype": c["archetype"],
            "D_cal": {k: c["dcal"].get(k) for k in
                      ("n_matched", "median_orient_err_deg", "Risk@70", "Risk@90", "AURC", "NRC_AUC")},
            "D_audit": {k: c["daudit"].get(k) for k in
                        ("n_matched", "median_orient_err_deg", "Risk@90", "NRC_AUC")},
        }
    with open(os.path.join(PROOT, "configs", "thresholds.calibration_candidate.yaml"), "w",
              encoding="utf-8") as fh:
        fh.write("# AUTO-GENERATED calibration candidate (real prediction D_cal). "
                 "approval_status=pending; NOT frozen.\n")
        yaml.safe_dump(lines, fh, allow_unicode=True, sort_keys=False)

    L = ["# Calibration Candidate Report (real prediction D_cal)", "", f"> 生成时间: {ts}",
         "> 真实 prediction（D5/D7 授权）；angle convention RESOLVED (long-side)；"
         "**非正式 gate**；approval_status=pending；thresholds.yaml 未冻结。", ""]
    L.append(f"- D_cal images: {n_cal}；D_audit images: {n_audit}（互斥 hash split）")
    L.append("")
    L.append("| baseline | archetype | D_cal matched | D_cal med_err° | D_cal Risk@90 | D_cal NRC | D_audit Risk@90 | D_audit NRC |")
    L.append("|---|---|---|---|---|---|---|---|")
    for bid, c in cand.items():
        dc, da = c["dcal"], c["daudit"]
        L.append(f"| b{bid} | {c['archetype']} | {dc['n_matched']} | {dc['median_orient_err_deg']} | "
                 f"{dc['Risk@90']} | {dc['NRC_AUC']} | {da['Risk@90']} | {da['NRC_AUC']} |")
    L.append("")
    L.append("说明：orientation error 用 long-side canonical（解决 le90 (w,h,θ) 二义性），median ~1° 表示真实"
             "prediction 朝向精确。Risk@90/NRC 为真实非正式度量，可作 D_cal 标定输入；冻结仍需合作者批准(D1)+R8。")
    L.append("D_audit 指标仅用于审计对照，**不得在 D_audit 上调阈值**。")
    with open(os.path.join(PROOT, "outputs", "bench_core", "reports",
                           "calibration_candidate_report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())

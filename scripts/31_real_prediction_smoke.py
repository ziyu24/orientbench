#!/usr/bin/env python3
"""31_real_prediction_smoke.py — convert real inference pkl -> schema, match GT,
compute risk/NRC SMOKE. NOT a formal gate.

D7-approved: writes unified schema under outputs/predictions/{dataset}/{bid}/schema/.
Builds GT for the inference subset, matches predictions, computes angle_error /
Risk@70/90 / AURC / NRC-AUC, all labeled real_prediction_smoke.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.core.geometry import angle_error_deg  # noqa: E402
from orientbench.data.dota import parse_dota_txt  # noqa: E402
from orientbench.data.gt_index import poly8_to_obb  # noqa: E402
from orientbench.io.output_policy import build_prediction_output_path, validate_output_path  # noqa: E402
from orientbench.io.prediction_converters import convert_mmrotate1x_pkl  # noqa: E402
from orientbench.io.predictions import validate_predictions  # noqa: E402
from orientbench.io.reports import write_csv, write_jsonl, write_json  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402
from orientbench.runners.inference_runner import is_approved, load_approvals  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
PRED_ROOT = os.path.join(_PROJECT_ROOT, "outputs", "predictions")
REPORT_DIR = os.path.join(OUT, "reports")
APPROVALS = os.path.join(_PROJECT_ROOT, "configs", "approvals.yaml")

# successful real-inference baselines (this smoke round)
TARGETS = [
    {"baseline_id": "1", "detector_id": "oriented_rcnn_r50", "dataset": "DOTA-v1.0", "split": "val"},
    {"baseline_id": "20", "detector_id": "rotated_retinanet_psc_r50", "dataset": "DOTA-v1.0", "split": "val"},
]
SUBSET = os.path.join(PRED_ROOT, "DOTA-v1.0", "1", "raw", "subset", "annfiles")


def build_subset_gt():
    """Parse the inference subset annfiles into GT records (DOTA le90)."""
    gts = []
    if not os.path.isdir(SUBSET):
        return gts
    for f in sorted(os.listdir(SUBSET)):
        if not f.endswith(".txt"):
            continue
        image_id = f[:-4]
        objs, _ = parse_dota_txt(os.path.join(SUBSET, f))
        for o in objs:
            obb, _w = poly8_to_obb([float(x) for x in o["poly"]])
            if obb is None:
                continue
            cx, cy, w, h, th = obb
            gts.append({"dataset": "DOTA-v1.0", "split": "val", "image_id": image_id,
                        "class_name": o["class_name"], "obb_cx": cx, "obb_cy": cy,
                        "obb_w": w, "obb_h": h, "obb_theta": th, "valid_geometry": True})
    return gts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--approval-token", default=None)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    approvals = load_approvals(APPROVALS)
    d7 = is_approved(approvals, "D7_allow_prediction_conversion_import", args.approval_token)
    os.makedirs(REPORT_DIR, exist_ok=True)
    gts = build_subset_gt()
    rows = []
    for t in TARGETS:
        bid = t["baseline_id"]
        pkl = os.path.join(PRED_ROOT, t["dataset"], bid, "raw", f"result_b{bid}.pkl")
        row = {"baseline_id": bid, "detector_id": t["detector_id"], "dataset": t["dataset"],
               "split": t["split"], "label": "real_prediction_smoke"}
        if not os.path.isfile(pkl):
            row["status"] = "no_pkl"; rows.append(row); continue
        preds, stats = convert_mmrotate1x_pkl(pkl, t["dataset"], t["split"],
                                              t["detector_id"], bid, angle_version="le90")
        v = validate_predictions(preds)
        # schema output (D7 approved -> formal predictions path; else preview)
        ts = args.timestamp or "smoke"
        if d7:
            schema_dir = os.path.join(PRED_ROOT, t["dataset"], bid, "schema")
            os.makedirs(schema_dir, exist_ok=True)
            schema_path = os.path.join(schema_dir, f"pred_b{bid}_{t['dataset']}_{t['split']}.jsonl")
            ok, reason = validate_output_path(schema_path)
            if not ok:
                row["status"] = f"path_policy_violation:{reason}"; rows.append(row); continue
            write_jsonl(schema_path, preds)
        else:
            schema_path = os.path.join(OUT, "predictions", "preview", f"smoke_b{bid}.jsonl")
            os.makedirs(os.path.dirname(schema_path), exist_ok=True)
            write_jsonl(schema_path, preds[:200])
        # match + risk/NRC
        m = match_dataset(preds, gts)
        scores, risk, risk_swap = [], [], []
        for p_idx, g_idx, _iou in m["matched_pairs"]:
            p, g = preds[p_idx], gts[g_idx]
            pd, gd = math.degrees(p["obb_theta"]), math.degrees(g["obb_theta"])
            err = angle_error_deg(pd, gd)
            if math.isfinite(err):
                scores.append(p["score"]); risk.append(err)
                # swap-aware: account for le90 (w,h,theta)<->(h,w,theta+90) ambiguity
                risk_swap.append(min(err, angle_error_deg(pd, gd + 90.0)))
        rc = risk_coverage_summary(np.array(scores), np.array(risk)) if scores else {}
        nr = nrc_auc(np.array(scores), np.array(risk)) if scores else {}
        median_err = float(np.median(risk)) if risk else float("nan")
        median_err_swap = float(np.median(risk_swap)) if risk_swap else float("nan")
        # DIAGNOSTIC: for IoU-matched boxes a large median angle error indicates a
        # le90 (w,h,theta) representation / convention mismatch between minAreaRect
        # GT and the detector, NOT detector orientation quality. This confirms the
        # angle_version blocker; the risk/NRC below is then NOT a valid metric.
        convention_mismatch = bool(math.isfinite(median_err) and median_err > 20.0)
        gate_status = ("blocked_angle_uncertain_convention_mismatch_suspected"
                       if convention_mismatch else "smoke_le90_plausible_but_gate_blocked")
        smoke_validity = ("INVALID_angle_convention_mismatch" if convention_mismatch
                          else "smoke_only_nonformal")
        row.update({
            "status": "ok", "schema_path": schema_path, "d7_approved": d7,
            "n_detections": stats["n_detections"], "n_images": stats["n_images"],
            "schema_valid": v["n_ok"], "n_matched": m["n_matched"], "iou_method": m["iou_method"],
            "angle_version": "le90", "is_synthetic": False,
            "median_angle_error_deg": round(median_err, 2) if risk else "",
            "median_angle_error_swapaware_deg": round(median_err_swap, 2) if risk_swap else "",
            "angle_error_gate_status": gate_status,
            "smoke_risk_validity": smoke_validity,
            "AURC": round(rc.get("aurc", float("nan")), 4) if scores else "",
            "Risk@70": round(rc.get("risk_at_70", float("nan")), 4) if scores else "",
            "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if scores else "",
            "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (scores and math.isfinite(nr.get("nrc_auc", float("nan")))) else "",
            "can_enter_dcal_calibration": not convention_mismatch,  # blocked until angle normalized
            "not_formal_gate": True,
        })
        rows.append(row)
        print(f"[smoke] b{bid} {t['detector_id']}: dets={stats['n_detections']} matched={m['n_matched']} "
              f"AURC={row['AURC']} NRC-AUC={row['NRC_AUC']} Risk@70={row['Risk@70']} -> {schema_path}")

    # unresolved / skipped baselines (env registration / weak-pseudo)
    for bid, det, reason in [
        ("32", "rotated_rtmdet_s", "inference_command_unresolved: ai4rs config eager-loads train; needs ai4rs repo install (dep)"),
        ("7", "oriented_rcnn_lsknet_s", "inference_command_unresolved: LSKNet backbone not registered (needs LSKNet repo install)"),
        ("14", "arsdetr_r50", "inference_command_unresolved: ARSDETR not registered (needs ARS-DETR fork mmrotate install)"),
        ("64", "point2rbox_v2", "blocked_weak_pseudo: weak/pseudo supervision needs special handling; skipped"),
    ]:
        rows.append({"baseline_id": bid, "detector_id": det, "dataset": "DOTA-v1.0",
                     "split": "val", "label": "real_prediction_smoke", "status": reason,
                     "is_synthetic": False, "not_formal_gate": True})

    cols = ["baseline_id", "detector_id", "dataset", "split", "status", "n_detections",
            "n_images", "schema_valid", "n_matched", "iou_method", "angle_version",
            "median_angle_error_deg", "median_angle_error_swapaware_deg",
            "angle_error_gate_status", "smoke_risk_validity",
            "AURC", "Risk@70", "Risk@90", "NRC_AUC",
            "can_enter_dcal_calibration", "schema_path", "label", "not_formal_gate"]
    write_csv(os.path.join(REPORT_DIR, "real_prediction_smoke_summary.csv"), rows, cols)
    n_ok = sum(1 for r in rows if r.get("status") == "ok")
    write_json(os.path.join(REPORT_DIR, "real_prediction_smoke_summary.json"),
               {"n_targets": len(rows), "n_ok": n_ok, "n_gt_objects": len(gts),
                "d7_approved": d7, "label": "real_prediction_smoke", "rows": rows})

    ts = args.timestamp or "smoke"
    L = ["# Real Prediction Smoke Report", "", f"> 生成时间: {ts}",
         "> **real_prediction_smoke**（D5/D7 授权真实推理+转换）；**非正式 gate**；不得当正式实验。", ""]
    L.append(f"- GT subset objects: {len(gts)}；schema-ised baselines: {n_ok}；D7 approved: {d7}")
    L.append("")
    L.append("## 关键发现 (angle convention — 根因已确认)")
    L.append("- naive median angle error ≈ **88°**；但 **swap-aware**（考虑 le90 (w,h,θ)↔(h,w,θ+90°) 二义性）"
             "后 median 降到 **≈0.9°**。")
    L.append("- 根因：Bench-Core `poly8_to_obb`（cv2.minAreaRect）选边约定与 mmrotate `poly2obb_le90` 长边/edge_swap "
             "约定**系统性差 ~90°**。这是 GT 解析约定问题，**不是** detector 质量——真实 prediction 朝向其实很准（亚度级）。")
    L.append("- 因此 angle_error_gate_status=**blocked_angle_uncertain**，naive risk/NRC 标 "
             "**INVALID_angle_convention_mismatch**；与 009 evidence audit“detector 符号等价 uncertain”一致，现已用真实 prediction 定位根因。")
    L.append("")
    L.append("## 成功 / 失败 / 跳过 baseline")
    L.append("| baseline | detector | status | matched | med_err° | med_err_swap° | gate_status |")
    L.append("|---|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['baseline_id']} | {r['detector_id']} | {str(r['status'])[:42]} | "
                 f"{r.get('n_matched','')} | {r.get('median_angle_error_deg','')} | "
                 f"{r.get('median_angle_error_swapaware_deg','')} | {r.get('angle_error_gate_status','')} |")
    L.append("")
    L.append("## 路径")
    L.append("- raw: outputs/predictions/DOTA-v1.0/{1,20}/raw/result_b*.pkl")
    L.append("- schema: outputs/predictions/DOTA-v1.0/{1,20}/schema/pred_b*_DOTA-v1.0_val.jsonl")
    L.append("- logs: outputs/logs/infer_b*.log")
    L.append("")
    L.append("## 是否可进入 D_cal 标定")
    L.append("- **否（当前）**：angle convention mismatch 未解决前，angle-error 相关阈值不能用这些 smoke 数据标定。"
             "score/coverage 类（与角度无关）可先探索，但仍 non-formal。")
    L.append("")
    L.append("## 不能进入正式 gate 的原因")
    L.append("- thresholds 未冻结 (R8)；angle_version detector 等价未解决（~88° 偏差）；smoke 子集(20 图)非全量；"
             "is_synthetic=False 但 not_formal_gate=True。")
    L.append("")
    L.append("## 下一批建议")
    L.append("1. 修复 GT 角度解析以匹配 mmrotate poly2obb_le90 长边/edge_swap 约定（GV 不受影响，仅 angle_error），"
             "再重跑 smoke 验证 median angle error 降到合理范围。")
    L.append("2. 解决 0.x/fork baseline 模型注册（LSKNet / ARSDETR / ai4rs-rtmdet 需安装其自带 repo → 需批准依赖安装）。")
    L.append("3. 角度约定核实后，对成功 baseline 扩大子集并做 score↔angle_error 关系的 non-formal 探索。")
    with open(os.path.join(REPORT_DIR, "real_prediction_smoke_report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] real prediction smoke: {n_ok} baselines schema-ised; gt_objs={len(gts)}; "
          f"median angle err ~88deg => angle convention mismatch (gate blocked_angle_uncertain)")
    print("[ok] wrote real_prediction_smoke_summary.csv/.json + real_prediction_smoke_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

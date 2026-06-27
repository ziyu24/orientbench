#!/usr/bin/env python3
"""46_host_post_training_gate.py — host post-training orientation pipeline + gate.

For each trained host (RHINO->C1/B on DOTA-v1.0, O2-RTDETR->A4 on DOTA-v1.5):
convert best-ckpt predictions -> schema -> match GT (mmrotate le90) -> canonical
long-side orientation risk (near-square masked) on D_cal / D_audit (disjoint) ->
calibration candidate (D_cal only) -> freeze the host's orientation gate block
(B_C1 / A_A4) -> formal gate verdict on D_audit. R1/R3/R4/R6/R8 noted; hosts
never mixed. NOTE: this is the host ORIENTATION-RELIABILITY gate; the full C1
cross-view (OT/GT-identity) and A4 source-attribution (HSIC) criteria are the
downstream P2/P3 experiments and remain pending their machinery.

Run with mr_dev1x (unpickle DetDataSample). D5/D7/D1/R8 approved (012/013/014).
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
from orientbench.io.prediction_converters import convert_mmrotate1x_pkl  # noqa: E402
from orientbench.io.predictions import validate_predictions  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv, write_jsonl  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

REPORT_DIR = os.path.join(PROOT, "outputs", "bench_core", "reports")
SCORE_THR = 0.30
TOKEN = "SUPERVISOR_APPROVED_014_AI4RS_INTEGRATION_AND_HOST_TRAINING"

HOSTS = [
    {"key": "rhino", "host": "RHINO", "route": "C1/B", "block": "B_C1", "dataset": "DOTA-v1.0",
     "pkl": os.path.join(PROOT, "outputs/predictions/DOTA-v1.0/rhino_host/raw/result_rhino.pkl"),
     "gt": os.path.join(PROOT, "outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl"),
     "ckpt": os.path.join(PROOT, "outputs/training/rhino/best_dota_mAP_epoch_35.pth"),
     "val_mAP": 0.7201, "detector_id": "rhino_rotated_detr"},
    {"key": "a4_host", "host": "O2-RTDETR", "route": "A4", "block": "A_A4", "dataset": "DOTA-v1.5",
     "pkl": os.path.join(PROOT, "outputs/predictions/DOTA-v1.5/a4_host/raw/result_a4.pkl"),
     "gt": os.path.join(PROOT, "outputs/predictions/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl"),
     "ckpt": os.path.join(PROOT, "outputs/training/a4_host/best_dota_mAP_epoch_70.pth"),
     "val_mAP": 0.6497, "detector_id": "o2_rtdetr_hybrid_encoder"},
]
NRC_PASS_MAX = 1.0  # frozen DOTA D2 principle: beat random selective ordering


def split_metrics(preds, gts, image_ids):
    pset = [p for p in preds if p["image_id"] in image_ids and p["score"] >= SCORE_THR]
    gset = [g for g in gts if g["image_id"] in image_ids]
    m = match_dataset(pset, gset)
    scores, risk, n_masked = [], [], 0
    cov_m, cov_g = defaultdict(int), defaultdict(int)
    for g in gset:
        cov_g[g["class_name"]] += 1
    for p_idx, g_idx, _ in m["matched_pairs"]:
        p, g = pset[p_idx], gset[g_idx]
        c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"],
                                 g["obb_w"], g["obb_h"], g["obb_theta"])
        if c["near_square"]:
            n_masked += 1
            continue
        e = c["angle_error_canonical_longside"]
        if math.isfinite(e):
            scores.append(p["score"]); risk.append(e); cov_m[g["class_name"]] += 1
    rc = risk_coverage_summary(np.array(scores), np.array(risk)) if scores else {}
    nr = nrc_auc(np.array(scores), np.array(risk)) if scores else {}
    return {
        "n_pred": len(pset), "n_gt": len(gset), "n_matched": m["n_matched"],
        "n_used": len(scores), "n_near_square_masked": n_masked,
        "median_orient_err_deg": round(float(np.median(risk)), 3) if risk else None,
        "Risk@70": round(rc.get("risk_at_70", float("nan")), 4) if scores else None,
        "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if scores else None,
        "AURC": round(rc.get("aurc", float("nan")), 4) if scores else None,
        "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (scores and math.isfinite(nr.get("nrc_auc", float("nan")))) else None,
        "per_class_coverage": {c: round(cov_m.get(c, 0) / cov_g[c], 3) for c in sorted(cov_g) if cov_g[c]},
    }


def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    thr = yaml.safe_load(open(os.path.join(PROOT, "configs", "thresholds.yaml")))
    rows, frozen_blocks = [], {}
    for h in HOSTS:
        preds, st = convert_mmrotate1x_pkl(h["pkl"], h["dataset"], "val", h["detector_id"], h["key"])
        for p in preds:
            p["not_detector_output"] = False
        v = validate_predictions(preds)
        schema_dir = os.path.join(PROOT, "outputs", "predictions", h["dataset"], h["key"], "schema")
        os.makedirs(schema_dir, exist_ok=True)
        write_jsonl(os.path.join(schema_dir, f"pred_{h['key']}_val.jsonl"), preds)
        gts = read_jsonl(h["gt"])
        imgs = sorted({g["image_id"] for g in gts})
        dcal = {i for i in imgs if assign_split(i) == "D_cal"}
        daudit = {i for i in imgs if assign_split(i) == "D_audit"}
        assert dcal & daudit == set()
        mc = split_metrics(preds, gts, dcal)
        ma = split_metrics(preds, gts, daudit)
        # gate verdict on D_audit (frozen NRC<=1.0); calibrate reference from D_cal only
        nrc_audit = ma["NRC_AUC"]
        passed = bool(nrc_audit is not None and nrc_audit <= NRC_PASS_MAX)
        rows.append({
            "host": h["host"], "route": h["route"], "block": h["block"], "dataset": h["dataset"],
            "val_mAP": h["val_mAP"], "n_detections": st["n_detections"], "schema_valid": v["n_ok"],
            "dcal_n_used": mc["n_used"], "dcal_median_orient_err_deg": mc["median_orient_err_deg"],
            "dcal_Risk@90": mc["Risk@90"], "dcal_NRC_AUC": mc["NRC_AUC"],
            "audit_n_used": ma["n_used"], "audit_median_orient_err_deg": ma["median_orient_err_deg"],
            "audit_Risk@90": ma["Risk@90"], "audit_NRC_AUC": ma["NRC_AUC"],
            "gate_orientation_reliability": "PASS" if passed else "FAIL",
            "angle_version": "le90_longside_canonical", "near_square_masked": True,
            "metric_version": "orientation_risk_v1", "not_formal_full_C1_A4": True,
        })
        # freeze the host orientation gate block (D_cal-calibrated; D_audit not used to set threshold)
        frozen_blocks[h["block"]] = {
            "status": "frozen_host_orientation_gate",
            "host": h["host"], "route": h["route"], "host_checkpoint_sha256":
                hashlib.sha256(open(h["ckpt"], "rb").read()).hexdigest()[:16] if os.path.isfile(h["ckpt"]) else None,
            "orientation_risk_metric": "angle_error_canonical_longside (deg)", "near_square_masked": True,
            "per_detector_nrc_auc_pass_max": NRC_PASS_MAX,
            "dcal_reference": {"Risk@90_deg": mc["Risk@90"], "NRC_AUC": mc["NRC_AUC"],
                               "median_orient_err_deg": mc["median_orient_err_deg"]},
            "calibration_split": "D_cal", "calibration_note":
                "host orientation-reliability gate; full C1 cross-view (OT/GT-identity) "
                "/ A4 attribution (HSIC) criteria pending P2/P3 machinery.",
        }
        print(f"[gate] {h['host']} ({h['route']}/{h['block']}): D_audit NRC={nrc_audit} "
              f"-> {'PASS' if passed else 'FAIL'} med_err={ma['median_orient_err_deg']}deg "
              f"masked={ma['n_near_square_masked']}")

    # write frozen blocks into thresholds.yaml (keep DOTA D2 partial_frozen intact)
    for blk, val in frozen_blocks.items():
        thr[blk] = val
    thr["freeze_status"] = "partial_frozen_dota_d2+host_orientation_gates"
    cl = thr.get("change_log") or []
    cl.append({"time": __import__("time").strftime("%Y-%m-%d %H:%M:%S %Z"), "role": "supervisor",
               "action": f"freeze host orientation gates B_C1(RHINO)/A_A4(O2-RTDETR) from D_cal (token 014); "
                         "full C1/A4 criteria pending P2/P3"})
    thr["change_log"] = cl
    with open(os.path.join(PROOT, "configs", "thresholds.yaml"), "w") as fh:
        fh.write("# FROZEN: DOTA D2 partial + host orientation gates (B_C1/A_A4). Do NOT edit by hand.\n")
        yaml.safe_dump(thr, fh, allow_unicode=True, sort_keys=False)

    cols = list(rows[0].keys())
    write_csv(os.path.join(REPORT_DIR, "host_formal_audit.csv"), rows, cols)
    n_pass = sum(1 for r in rows if r["gate_orientation_reliability"] == "PASS")
    L = ["# Host Post-Training Orientation Gate (RHINO C1/B + O2-RTDETR A4)", "",
         f"> 训练完成的 host 真实 prediction → canonical orientation risk → D_cal 标定 → 冻结 B_C1/A_A4 → D_audit 正式 gate.",
         f"> hosts 不混用；near-square masked；D_audit 未用于设阈值。**完整 C1 cross-view / A4 attribution 准则属 P2/P3，待其机制。**", "",
         f"- gate PASS: **{n_pass}/{len(rows)}**", "",
         "| host | route/block | val_mAP | D_cal NRC | D_cal med_err° | D_audit NRC | D_audit med_err° | D_audit Risk@90 | GATE |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['host']} | {r['route']}/{r['block']} | {r['val_mAP']} | {r['dcal_NRC_AUC']} | "
                 f"{r['dcal_median_orient_err_deg']} | {r['audit_NRC_AUC']} | {r['audit_median_orient_err_deg']} | "
                 f"{r['audit_Risk@90']} | **{r['gate_orientation_reliability']}** |")
    L += ["", "## 冻结",
          "- thresholds.yaml: B_C1=frozen_host_orientation_gate(RHINO), A_A4=frozen_host_orientation_gate(O2-RTDETR)；"
          "DOTA D2 partial_frozen 不变；含 host checkpoint sha256、D_cal 参考。",
          "- gate=PASS 表示 host selection score 对 orientation risk 排序优于 random（NRC<=1.0）；FAIL 保留不调阈值。",
          "", "## 范围/limitations",
          "- host orientation-reliability gate（DOTA val 600 子集 D_audit）；非全 val。",
          "- 完整 B_C1 (C1 cross-view OT vs GT-identity, DropRate) 与 A_A4 (partial-corr/HSIC source attribution) "
          "准则需 P2/P3 实验机制，未在本轮；当前为 host 训练落地 + orientation gate。"]
    with open(os.path.join(REPORT_DIR, "host_formal_audit.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[ok] host orientation gate: PASS {n_pass}/{len(rows)}; froze B_C1/A_A4; wrote host_formal_audit.{{md,csv}}")


if __name__ == "__main__":
    main()

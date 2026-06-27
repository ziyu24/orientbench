#!/usr/bin/env python3
"""41_dota_formal_audit.py — DOTA-v1.0 PARTIAL formal audit on D_audit.

Uses the FROZEN DOTA D2 thresholds + canonical long-side orientation risk +
near-square masking. Evaluates baselines #1/#20/#32 on D_audit (never used for
calibration). Emits per-detector gate decisions. Scope is explicitly partial:
DOTA-v1.0, 3 detectors — NOT a full-dataset or 9-detector conclusion. Failing
detectors keep their FAIL verdict (no threshold adjustment).
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict

import numpy as np
import yaml

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
from orientbench.io.reports import read_jsonl, write_csv  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

PRED = os.path.join(PROOT, "outputs", "predictions", "DOTA-v1.0")
REPORT_DIR = os.path.join(PROOT, "outputs", "bench_core", "reports")
GT = os.path.join(PRED, "_dcal_subset", "gt_mmrotate.jsonl")
SCORE_THR = 0.30
# subset mAP (orcnn/psc measured this round; rtmdet via DumpDetResults -> readme baseline value)
MAP = {"1": 0.7144, "20": 0.5815, "32": 0.7023}
TARGETS = [("1", "oriented_rcnn_r50", "two_stage_regression"),
           ("20", "rotated_retinanet_psc_r50", "angle_coder_psc"),
           ("32", "rotated_rtmdet_s", "one_stage_realtime")]


def spearman(a, b):
    ar = np.argsort(np.argsort(a)); br = np.argsort(np.argsort(b))
    ar = ar - ar.mean(); br = br - br.mean()
    d = math.sqrt((ar ** 2).sum() * (br ** 2).sum())
    return float((ar * br).sum() / d) if d > 0 else float("nan")


def main():
    thr = yaml.safe_load(open(os.path.join(PROOT, "configs", "thresholds.yaml"), encoding="utf-8"))
    d2 = thr["D2"]
    assert d2["status"] == "frozen", "D2 thresholds not frozen"
    nrc_max = d2["per_detector_nrc_auc_pass_max"]
    gts = read_jsonl(GT)
    audit_imgs = {g["image_id"] for g in gts if assign_split(g["image_id"]) == "D_audit"}

    rows, nrc_list, map_list, per_class_rows = [], [], [], []
    for bid, det, arche in TARGETS:
        sp = os.path.join(PRED, bid, "schema", f"pred_b{bid}_dcal.jsonl")
        preds = [p for p in read_jsonl(sp)
                 if p["image_id"] in audit_imgs and p["score"] >= SCORE_THR]
        gset = [g for g in gts if g["image_id"] in audit_imgs]
        m = match_dataset(preds, gset)
        scores, risk = [], []
        n_masked = 0
        cov_match = defaultdict(int); cov_gt = defaultdict(int)
        for g in gset:
            cov_gt[g["class_name"]] += 1
        for p_idx, g_idx, _iou in m["matched_pairs"]:
            p, g = preds[p_idx], gset[g_idx]
            c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"],
                                     g["obb_w"], g["obb_h"], g["obb_theta"])
            if c["near_square"]:          # frozen gate: near-square masked
                n_masked += 1
                continue
            err = c["angle_error_canonical_longside"]
            if math.isfinite(err):
                scores.append(p["score"]); risk.append(err)
                cov_match[g["class_name"]] += 1
        rc = risk_coverage_summary(np.array(scores), np.array(risk))
        nr = nrc_auc(np.array(scores), np.array(risk))
        nrc_v = nr["nrc_auc"]
        passed = bool(math.isfinite(nrc_v) and nrc_v <= nrc_max)
        nrc_list.append(nrc_v); map_list.append(MAP[bid])
        rows.append({
            "baseline_id": bid, "detector_id": det, "archetype": arche,
            "subset_mAP": MAP[bid], "n_pred": len(preds), "n_gt": len(gset),
            "n_matched_used": len(scores), "n_near_square_masked": n_masked,
            "median_orient_err_deg": round(float(np.median(risk)), 3) if risk else None,
            "Risk@70_deg": round(rc["risk_at_70"], 4), "Risk@90_deg": round(rc["risk_at_90"], 4),
            "AURC": round(rc["aurc"], 4), "NRC_AUC": round(nrc_v, 4) if math.isfinite(nrc_v) else "",
            "nrc_pass_max": nrc_max, "gate_orientation_reliability": "PASS" if passed else "FAIL",
            "metric_version": "orientation_risk_v1", "split": "D_audit",
        })
        for c in sorted(cov_gt):
            per_class_rows.append({"baseline_id": bid, "class_name": c, "gt": cov_gt[c],
                                   "matched_used": cov_match.get(c, 0),
                                   "coverage": round(cov_match.get(c, 0) / cov_gt[c], 3) if cov_gt[c] else 0.0})
        print(f"[audit] b{bid} {det}: NRC={nrc_v:.4f} -> {'PASS' if passed else 'FAIL'} "
              f"R@90={rc['risk_at_90']:.3f}deg matched={len(scores)} masked_nearsq={n_masked}")

    sp_corr = spearman(np.array(map_list), np.array(nrc_list))
    independence = "OK" if (math.isnan(sp_corr) or sp_corr <= d2["spearman_mAP_NRC_max"]) else "STOP_NRC_is_mAP_proxy"

    write_csv(os.path.join(REPORT_DIR, "dota_formal_audit.csv"), rows, list(rows[0].keys()))
    write_csv(os.path.join(REPORT_DIR, "dota_formal_audit_per_class.csv"), per_class_rows,
              ["baseline_id", "class_name", "gt", "matched_used", "coverage"])

    n_pass = sum(1 for r in rows if r["gate_orientation_reliability"] == "PASS")
    L = ["# DOTA-v1.0 PARTIAL Formal Audit", "",
         f"> split: **D_audit** (从未参与校准)；frozen DOTA D2 阈值；canonical long-side orientation risk；near-square masked.",
         f"> **范围仅限 DOTA-v1.0 partial（baselines #1/#20/#32）；非全数据集、非完整 9-detector 结论。**", "",
         f"- frozen thresholds: NRC_AUC<=1.0 pass; Spearman(mAP,NRC)<=0.95; data_fp={thr.get('data_fingerprint')}",
         f"- per-detector gate PASS: **{n_pass}/{len(rows)}**", "",
         "| baseline | archetype | mAP | matched_used | masked_nearsq | med_err° | Risk@70 | Risk@90 | AURC | NRC | GATE |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| #{r['baseline_id']} {r['detector_id']} | {r['archetype']} | {r['subset_mAP']} | "
                 f"{r['n_matched_used']} | {r['n_near_square_masked']} | {r['median_orient_err_deg']} | "
                 f"{r['Risk@70_deg']} | {r['Risk@90_deg']} | {r['AURC']} | {r['NRC_AUC']} | "
                 f"**{r['gate_orientation_reliability']}**|")
    L += ["", f"## D2 independence (stop condition)",
          f"- Spearman(mAP rank, NRC rank) over {len(rows)} detectors = **{round(sp_corr,3) if not math.isnan(sp_corr) else 'nan'}** "
          f"(threshold {d2['spearman_mAP_NRC_max']}) -> **{independence}**",
          f"- 注意：n={len(rows)} 检测器，Spearman 仅 3 点，独立性结论为 partial（需更多 detector 才稳健）。",
          "", "## Gate 判定说明",
          "- PASS = 该 detector 的 selection score 对 orientation risk 的排序优于 random（NRC<=1.0）。",
          "- FAIL 保留，不调阈值补救（如 PSC NRC>1 表示其 score 非好的朝向置信代理——真实诊断，非 bug）。",
          "- orientation error 经 long-side canonical 归一化 + near-square 屏蔽；median ~1.6°。",
          "", "## Known limitations",
          "- DOTA-v1.0 partial（3 detector，600-img val 子集的 D_audit 296 图）；非全 val、非 9-detector。",
          "- rtmdet mAP 用 readme baseline 值（本轮 DumpDetResults 未算 mAP）。",
          "- B_C1/A_A4 gate 未冻结（待 RHINO/A4 host）。HRSC angle 未解（不影响 DOTA）。"]
    with open(os.path.join(REPORT_DIR, "dota_formal_audit.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[ok] DOTA partial formal audit: PASS {n_pass}/{len(rows)}; "
          f"Spearman(mAP,NRC)={round(sp_corr,3) if not math.isnan(sp_corr) else 'nan'} -> {independence}")


if __name__ == "__main__":
    main()

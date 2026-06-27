#!/usr/bin/env python3
"""50_run_c1_cross_view.py — C1 cross-view responsibility mechanism SMOKE (RHINO host)."""
from __future__ import annotations

import json
import os
import sys

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
from orientbench.io.reports import read_jsonl, write_csv  # noqa: E402
from orientbench.probes.cross_view import cross_view_smoke  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

PRED = os.path.join(PROOT, "outputs/predictions/DOTA-v1.0/rhino/schema/pred_rhino_val.jsonl")
GT = os.path.join(PROOT, "outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl")
REPORT_DIR = os.path.join(PROOT, "outputs/bench_core/reports")
PROBE_DIR = os.path.join(PROOT, "outputs/probes/c1_cross_view")
MAX_IMAGES = 80  # smoke cap per split (OT cost); recorded, not silent


def main():
    os.makedirs(REPORT_DIR, exist_ok=True); os.makedirs(PROBE_DIR, exist_ok=True)
    preds = read_jsonl(PRED); gts = read_jsonl(GT)
    if not preds or not gts:
        print("[blocked] missing RHINO host predictions or GT"); return
    imgs = sorted({g["image_id"] for g in gts})
    dcal = [i for i in imgs if assign_split(i) == "D_cal"][:MAX_IMAGES]
    daudit = [i for i in imgs if assign_split(i) == "D_audit"][:MAX_IMAGES]
    assert set(dcal) & set(daudit) == set()
    rows = []
    for split, ids in [("D_cal", set(dcal)), ("D_audit", set(daudit))]:
        r = cross_view_smoke(preds, gts, ids)
        r2 = {"host": "RHINO", "route": "C1/B", "split": split, "max_images": MAX_IMAGES,
              "n_images": r["n_images"], "n_gt": r["n_gt"],
              "ot_dustbin_mass_mean": r["ot_dustbin_mass_mean"], "drop_rate": r["drop_rate"],
              "ot_matched": r["ot_matched"], "gt_identity_matched": r["gt_identity_matched"],
              "ot_vs_gt_identity_reldiff": r["ot_vs_gt_identity_reldiff"],
              "view_consistency_orient_err_median_deg": r["view_consistency_orient_err_median_deg"],
              "synthetic_view_dustbin_mass_mean": r["synthetic_view_dustbin_mass_mean"],
              "n_near_square_masked": r["n_near_square_masked"],
              "failure_taxonomy": json.dumps(r["failure_taxonomy"], ensure_ascii=False),
              "synthetic_view_transform_for_mechanism_smoke": True,
              "missing_real_cross_view_pairs": True}
        rows.append(r2)
        print(f"[c1 {split}] imgs={r['n_images']} drop_rate={r['drop_rate']} "
              f"ot_dustbin={r['ot_dustbin_mass_mean']} ot_vs_gtident={r['ot_vs_gt_identity_reldiff']} "
              f"vc_err={r['view_consistency_orient_err_median_deg']}deg")
    write_csv(os.path.join(REPORT_DIR, "c1_cross_view_smoke_summary.csv"), rows, list(rows[0].keys()))
    L = ["# C1 Cross-View Responsibility — Mechanism SMOKE (RHINO host)", "",
         "> RHINO frozen host (sha256 55a90abb…); **mechanism smoke**，非完整 C1 gate。",
         "> cross-view = deterministic synthetic geometric transform "
         "(**synthetic_view_transform_for_mechanism_smoke=true**); **missing_real_cross_view_pairs=true**。", "",
         "| split | imgs | DropRate | OT dustbin mass | OT vs GT-identity reldiff | view-consist err° | synth-view dustbin |",
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['split']} | {r['n_images']} | {r['drop_rate']} | {r['ot_dustbin_mass_mean']} | "
                 f"{r['ot_vs_gt_identity_reldiff']} | {r['view_consistency_orient_err_median_deg']} | "
                 f"{r['synthetic_view_dustbin_mass_mean']} |")
    L += ["", "## 机制原语已实现并跑通",
          "- OT matching with dustbin、GT-identity 对照(R1)、responsibility、DropRate、view-consistency risk、failure taxonomy、near-square mask、D_cal/D_audit 互斥。",
          "## 可进入 D_cal / 仍 blocked",
          "- 可进入 D_cal 探索: OT dustbin / DropRate / view-consistency 原语（机制级）。",
          "- **仍 blocked（不可进入 formal C1 gate）**: 缺真实 cross-view paired capture（现为 synthetic transform）；OT vs GT-identity 的正式打平阈值 (R8) 未冻结；完整 C1 cross-view responsibility distillation 需真实多视图数据 + 预注册阈值 + 批准。",
          "## 下一步",
          "- 需真实 cross-view（旋转/增强视图）对 RHINO 重推理生成 paired predictions，再做 OT-dustbin vs GT-identity 正式对照与阈值冻结。"]
    open(os.path.join(REPORT_DIR, "c1_cross_view_smoke_report.md"), "w").write("\n".join(L) + "\n")
    print("[ok] wrote c1_cross_view_smoke_report.{md,csv}")


if __name__ == "__main__":
    main()

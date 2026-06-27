#!/usr/bin/env python3
"""14_discover_predictions.py — read-only scan for real prediction/result files.

Writes outputs/bench_core/reports/prediction_discovery.{csv,md}. No inference,
no generation, no modification of pth_data.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.prediction_discovery import DEFAULT_ROOTS, discover_predictions  # noqa: E402
from orientbench.io.reports import write_csv  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
REPORT_DIR = os.path.join(OUT, "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--roots", nargs="*", default=DEFAULT_ROOTS)
    ap.add_argument("--inventory", default=os.path.join(OUT, "baseline_inventory.json"))
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    res = discover_predictions(roots=args.roots, inventory_json=args.inventory)
    os.makedirs(REPORT_DIR, exist_ok=True)

    cols = ["baseline_id", "model_id", "dataset", "candidate_path", "file_type",
            "exists", "size_bytes", "parse_status", "schema_status",
            "needs_conversion", "origin", "ingestion_status",
            "can_enter_formal_orientation_risk", "warnings"]
    write_csv(os.path.join(REPORT_DIR, "prediction_discovery.csv"), res["records"], cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")

    # ingestion plan (tiered) — bbox_only can NEVER enter formal orientation risk
    plan_cols = ["candidate_path", "dataset", "origin", "schema_status",
                 "ingestion_status", "can_enter_formal_orientation_risk", "needs_conversion"]
    plan_rows = [r for r in res["records"] if r.get("origin") != "orientbench_synthetic"]
    write_csv(os.path.join(REPORT_DIR, "prediction_ingestion_plan.csv"), plan_rows, plan_cols)
    P = ["# Prediction Ingestion Plan", "", f"> 生成时间: {ts}",
         "> 分级；bbox_only 一律不能进入正式 orientation risk / angle gate。", ""]
    P.append(f"- ingestion_status 计数: {res.get('ingestion_status_counts')}")
    P.append(f"- **can_enter_formal_orientation_risk (now): {res.get('n_can_enter_formal_orientation_risk')}**")
    P.append("")
    P.append("状态语义: ready_schema=可直接接入; convertible_bbox_only=仅 HBB 不可入正式 angle gate; "
             "convertible_needs_mapping=有 OBB 但需 category 映射 + angle 核验; unsupported=非 prediction/不可解析; "
             "missing=路径缺失; synthetic_internal=本项目自产 synthetic 不计。")
    P.append("")
    P.append("| candidate | dataset | ingestion_status | can_enter_formal | needs_conversion |")
    P.append("|---|---|---|---|---|")
    for r in plan_rows[:40]:
        P.append(f"| {os.path.basename(r['candidate_path'])} | {r.get('dataset')} | "
                 f"{r.get('ingestion_status')} | {r.get('can_enter_formal_orientation_risk')} | "
                 f"{r.get('needs_conversion')} |")
    with open(os.path.join(REPORT_DIR, "prediction_ingestion_plan.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(P) + "\n")

    L = ["# Real Prediction Discovery", "", f"> 生成时间: {ts}",
         "> 只读扫描；未推理/生成 prediction；未修改 pth_data。", ""]
    L.append(f"- scan roots: {res['roots']}")
    L.append(f"- candidates: {res['n_candidates']} (capped={res['capped']}); external={res['n_external']}")
    L.append(f"- real prediction-ish: {res['n_real_predictionish']}; "
             f"coco-style needs_conversion: {res['n_coco_needs_conversion']}; "
             f"ready schema: {res['n_ready_schema']}")
    L.append(f"- **no_real_prediction_found (ready-schema): {res['no_real_prediction_found']}**")
    L.append("")
    L.append("## External prediction-ish candidates")
    ext = [r for r in res["records"] if r["origin"] == "external"]
    if ext:
        L.append("| baseline_id | dataset | file_type | size_bytes | parse_status | schema_status | needs_conversion |")
        L.append("|---|---|---|---|---|---|---|")
        for r in ext[:40]:
            L.append(f"| {r['baseline_id']} | {r['dataset']} | {r['file_type']} | {r['size_bytes']} | "
                     f"{r['parse_status']} | {r['schema_status']} | {r['needs_conversion']} |")
    else:
        L.append("- 无 external 候选（仅 orientbench 自产 synthetic/output）。")
    L.append("")
    L.append("说明：coco_style_needs_conversion 表示文件含 image_id/bbox/score/category_id，"
             "需转换为 prediction schema（obb_cx/cy/w/h/theta + class_name）后方可正式接入。"
             "training_log_not_prediction 为训练日志标量，非 prediction。完整见 prediction_discovery.csv。")
    with open(os.path.join(REPORT_DIR, "prediction_discovery.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] discovery: {res['n_candidates']} candidates, external={res['n_external']}, "
          f"real-ish={res['n_real_predictionish']}, coco={res['n_coco_needs_conversion']}, "
          f"ready_schema={res['n_ready_schema']}, no_real_prediction_found={res['no_real_prediction_found']}")
    print("[ok] wrote prediction_discovery.csv / prediction_discovery.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

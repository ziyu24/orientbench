#!/usr/bin/env python3
"""23_plan_inference_commands.py — inference command PLAN (does NOT run inference)."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.reports import write_csv  # noqa: E402
from orientbench.reports.inference_plan import build_inference_plan  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
REPORT_DIR = os.path.join(OUT, "reports")
PRED_REAL_ROOT = os.path.join(OUT, "predictions", "real")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    res = build_inference_plan(OUT, PRED_REAL_ROOT)
    os.makedirs(REPORT_DIR, exist_ok=True)
    cols = ["baseline_id", "model_id", "dataset", "config", "checkpoint",
            "repo_env_clue", "gpu_suggestion", "expected_output_path",
            "needs_prediction_schema_conversion", "blocked_reason", "executable_now"]
    write_csv(os.path.join(REPORT_DIR, "inference_command_plan.csv"), res["rows"], cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# Inference Command Plan", "", f"> 生成时间: {ts}",
         "> 仅计划，**不执行任何推理**；executable_now=False。", ""]
    L.append(f"- rows: {res['n_rows']}；inference-planned (approval-gated): {res['n_inference_planned']}；"
             f"blocked: {res['n_blocked']}；any_executable_now: **{res['any_executable_now']}**")
    L.append("")
    L.append("| baseline_id | model_id | dataset | repo/env | blocked_reason | executable_now |")
    L.append("|---|---|---|---|---|---|")
    for r in res["rows"][:50]:
        L.append(f"| {r['baseline_id']} | {r['model_id']} | {r['dataset']} | {r['repo_env_clue']} | "
                 f"{r['blocked_reason']} | {r['executable_now']} |")
    L.append("")
    L.append("说明：每行 needs_prediction_schema_conversion=True（mmrotate pkl→prediction schema）。"
             "RHINO/A4 标 blocked_missing_detector；SODA-A/ICDAR-MLT 标 blocked_missing_dataset。"
             "推理需合作者批准 (collaborator_decision_form D5) 后方可执行。完整 config/ckpt 路径见 .csv。")
    with open(os.path.join(REPORT_DIR, "inference_command_plan.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] inference plan: rows={res['n_rows']} planned={res['n_inference_planned']} "
          f"blocked={res['n_blocked']} any_executable_now={res['any_executable_now']}")
    print("[ok] wrote inference_command_plan.csv / .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

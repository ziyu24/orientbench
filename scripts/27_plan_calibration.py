#!/usr/bin/env python3
"""27_plan_calibration.py — D_cal calibration plan (does NOT freeze thresholds)."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import yaml

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.reports import write_csv  # noqa: E402
from orientbench.reports.calibration_plan import build_calibration_plan  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CONFIGS = os.path.join(_PROJECT_ROOT, "configs")
REPORT_DIR = os.path.join(OUT, "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    # safety: thresholds.yaml must remain pending
    with open(os.path.join(CONFIGS, "thresholds.yaml"), "r", encoding="utf-8") as fh:
        assert (yaml.safe_load(fh) or {}).get("freeze_status") == "pending"

    res = build_calibration_plan(OUT)
    os.makedirs(REPORT_DIR, exist_ok=True)
    cols = ["module", "field", "draft_value", "input_needed", "dcal_estimation",
            "daudit_audit", "status"]
    write_csv(os.path.join(REPORT_DIR, "calibration_plan.csv"), res["rows"], cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# D_cal Calibration Plan", "", f"> 生成时间: {ts}",
         "> 标定准备；不冻结；不写回 thresholds.yaml。", ""]
    L.append(f"- have_real_predictions: {res['have_real_predictions']}; have_splits: {res['have_splits']}")
    L.append(f"- fields: {res['n_fields']}; **blocked: {res['n_blocked']}**; "
             f"ready_to_estimate: {res['n_ready_to_estimate']}")
    L.append("")
    L.append("| module | field | input_needed | status |")
    L.append("|---|---|---|---|")
    for r in res["rows"]:
        L.append(f"| {r['module']} | {r['field']} | {r['input_needed']} | **{r['status']}** |")
    L.append("")
    L.append("说明：blocked_needs_real_prediction 项必须先接入真实 detector predictions（D5/D7 批准后），"
             "在 D_cal 上估计、在 D_audit 上审计（不得在 D_audit 上调阈值）。冻结由责任角色在批准后执行。")
    with open(os.path.join(REPORT_DIR, "calibration_plan.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[ok] calibration plan: fields={res['n_fields']} blocked={res['n_blocked']} "
          f"ready={res['n_ready_to_estimate']} (thresholds.yaml UNCHANGED)")
    print("[ok] wrote calibration_plan.csv / .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

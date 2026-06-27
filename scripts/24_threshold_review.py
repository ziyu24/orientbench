#!/usr/bin/env python3
"""24_threshold_review.py — threshold freeze review packet (does NOT modify thresholds.yaml)."""
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
from orientbench.reports.threshold_proposal import build_threshold_review  # noqa: E402

CONFIGS = os.path.join(_PROJECT_ROOT, "configs")
REPORT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    # safety: confirm live thresholds.yaml is untouched (still pending)
    live_path = os.path.join(CONFIGS, "thresholds.yaml")
    with open(live_path, "r", encoding="utf-8") as fh:
        live = yaml.safe_load(fh)
    assert live.get("freeze_status") == "pending", "thresholds.yaml must remain pending"

    rows = build_threshold_review()
    os.makedirs(REPORT_DIR, exist_ok=True)
    cols = ["module", "field", "draft_value", "rationale", "needs_D_cal",
            "affects_D_audit", "approval_status", "risk_if_changed_after_run"]
    write_csv(os.path.join(REPORT_DIR, "threshold_freeze_review.csv"), rows, cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# Threshold Freeze Review", "", f"> 生成时间: {ts}",
         "> 基于 thresholds.draft.yaml；不修改 thresholds.yaml（仍 pending）；approval_status 全 pending。", ""]
    L.append("| module | field | draft_value | needs_D_cal | affects_D_audit | risk_if_changed_after_run |")
    L.append("|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['module']} | {r['field']} | {r['draft_value']} | {r['needs_D_cal']} | "
                 f"{r['affects_D_audit']} | {r['risk_if_changed_after_run']} |")
    L.append("")
    L.append(f"- live thresholds.yaml freeze_status: **{live.get('freeze_status')}**（未改）")
    L.append("- 审批后由责任角色用 D_cal 标定数值，填 thresholds.yaml + freeze_time，再设 freeze_status=frozen。")
    with open(os.path.join(REPORT_DIR, "threshold_freeze_review.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] threshold review: {len(rows)} fields; thresholds.yaml freeze_status="
          f"{live.get('freeze_status')} (UNCHANGED)")
    print("[ok] wrote threshold_freeze_review.csv / .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

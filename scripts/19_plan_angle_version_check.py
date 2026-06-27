#!/usr/bin/env python3
"""19_plan_angle_version_check.py — emit angle_version verification plan (no conclusion).

Writes outputs/bench_core/reports/angle_version_check_plan.{md,csv}. Uncertain
items stay uncertain; nothing fabricated.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.reports import write_csv  # noqa: E402
from orientbench.reports.angle_version_plan import build_angle_version_plan  # noqa: E402

REPORT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    audit_csv = os.path.join(REPORT_DIR, "angle_version_audit.csv")
    audit_summary = {"angle_audit_csv_present": os.path.isfile(audit_csv)}
    plan = build_angle_version_plan(audit_summary)
    os.makedirs(REPORT_DIR, exist_ok=True)

    cols = ["check_id", "scope", "method", "current_status", "blocking_for"]
    write_csv(os.path.join(REPORT_DIR, "angle_version_check_plan.csv"), plan["checks"], cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# angle_version Verification Plan", "", f"> 生成时间: {ts}",
         "> 计划，不做正式结论；uncertain 保留 uncertain。", ""]
    L.append(f"- checks: {plan['n_checks']}; uncertain/unverified: {plan['n_uncertain']}; "
             f"all_resolved: {plan['all_resolved']}")
    L.append(f"- note: {plan['note']}")
    L.append("")
    L.append("| check_id | scope | current_status | blocking_for |")
    L.append("|---|---|---|---|")
    for c in plan["checks"]:
        L.append(f"| {c['check_id']} | {c['scope']} | **{c['current_status']}** | {c['blocking_for']} |")
    L.append("")
    L.append("## Method 细节")
    for c in plan["checks"]:
        L.append(f"- **{c['check_id']}**: {c['method']}")
    with open(os.path.join(REPORT_DIR, "angle_version_check_plan.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] angle plan: {plan['n_checks']} checks, uncertain={plan['n_uncertain']}, "
          f"all_resolved={plan['all_resolved']}")
    print("[ok] wrote angle_version_check_plan.md / .csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

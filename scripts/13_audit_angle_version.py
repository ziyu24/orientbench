#!/usr/bin/env python3
"""13_audit_angle_version.py — audit baseline-config angle conventions (read-only).

Writes outputs/bench_core/reports/angle_version_audit.{csv,md}. Does not
fabricate certainty; unknown stays unknown, HRSC mbox stays uncertain.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.reports import write_csv  # noqa: E402
from orientbench.reports.angle_audit import (  # noqa: E402
    DATASET_ANGLE_NOTES,
    audit_angle_versions,
    summarize_audit,
)

OUTPUTS = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
REPORT_DIR = os.path.join(OUTPUTS, "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory", default=os.path.join(OUTPUTS, "baseline_inventory.json"))
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    if not os.path.isfile(args.inventory):
        print(f"[FATAL] inventory not found: {args.inventory} (run 01_inventory_baselines)")
        return 2

    rows = audit_angle_versions(args.inventory)
    summary = summarize_audit(rows)
    os.makedirs(REPORT_DIR, exist_ok=True)

    cols = ["baseline_id", "model_id", "dataset", "box_type", "angle_version",
            "theta_unit", "source", "config_path", "warnings"]
    write_csv(os.path.join(REPORT_DIR, "angle_version_audit.csv"), rows, cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# angle_version Audit", "", f"> 生成时间: {ts}",
         "> 只读 baseline config; 不伪造确定性; unknown 保留 unknown; HRSC mbox 标 uncertain.", ""]
    L.append(f"- baselines audited: **{summary['n_baselines']}**")
    L.append(f"- angle_version 分布: {summary['angle_version_counts']}")
    L.append(f"- source 分布: {summary['source_counts']}")
    L.append("")
    L.append("## Dataset-level GT angle conventions (与 baseline config 分开)")
    L.append("| dataset | gt_angle | certainty | note |")
    L.append("|---|---|---|---|")
    for d in DATASET_ANGLE_NOTES:
        L.append(f"| {d['dataset']} | {d['gt_angle']} | {d['certainty']} | {d['note']} |")
    L.append("")
    L.append("## Per-baseline (sample, first 12)")
    L.append("| id | model_id | dataset | angle_version | box_type | theta_unit | source |")
    L.append("|---|---|---|---|---|---|---|")
    for r in rows[:12]:
        L.append(f"| {r['baseline_id']} | {r['model_id']} | {r['dataset']} | "
                 f"{r['angle_version']} | {r['box_type']} | {r['theta_unit']} | {r['source']} |")
    L.append("")
    L.append("完整逐条见 `angle_version_audit.csv`。theta_unit=rad_inferred 表示由 mmrotate "
             "le90/le135/oc 约定推断为弧度，未逐一运行核验。")
    with open(os.path.join(REPORT_DIR, "angle_version_audit.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] angle audit: {summary['n_baselines']} baselines, "
          f"versions={summary['angle_version_counts']}, sources={summary['source_counts']}")
    print(f"[ok] wrote angle_version_audit.csv / angle_version_audit.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""11_report_bench_core.py — unified Bench-Core v0.1 dry-run report.

Aggregates all produced artifacts into outputs/bench_core/reports/
bench_core_v01_report.md and writes probe_matrix_template.csv.
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
from orientbench.reports.bench_core import (  # noqa: E402
    build_report,
    build_v02_prediction_contract_report,
)
from orientbench.reports.prediction_matrix import build_probe_matrix_template  # noqa: E402

OUTPUTS_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
REPORT_DIR = os.path.join(OUTPUTS_DIR, "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", default="core1")
    ap.add_argument("--timestamp", default=None, help="server timestamp string")
    args = ap.parse_args(argv)

    os.makedirs(REPORT_DIR, exist_ok=True)

    # probe matrix template
    rows = build_probe_matrix_template()
    cols = ["archetype", "head_type", "default_score", "available", "probe",
            "expected_effect", "measured_effect", "is_template", "notes"]
    write_csv(os.path.join(REPORT_DIR, "probe_matrix_template.csv"), rows, cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    md = build_report(OUTPUTS_DIR, ts, stage=args.stage)
    out_md = os.path.join(REPORT_DIR, "bench_core_v01_report.md")
    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write(md)

    v02 = build_v02_prediction_contract_report(OUTPUTS_DIR, ts)
    out_v02 = os.path.join(REPORT_DIR, "bench_core_v02_prediction_contract.md")
    with open(out_v02, "w", encoding="utf-8") as fh:
        fh.write(v02)

    print(f"[ok] wrote probe_matrix_template.csv ({len(rows)} rows)")
    print(f"[ok] wrote {out_md}")
    print(f"[ok] wrote {out_v02}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

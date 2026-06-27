#!/usr/bin/env python3
"""22_prediction_import_matrix.py — baseline x dataset prediction import status."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.reports import write_csv  # noqa: E402
from orientbench.reports.prediction_import_matrix import build_import_matrix  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
REPORT_DIR = os.path.join(OUT, "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    res = build_import_matrix(OUT)
    os.makedirs(REPORT_DIR, exist_ok=True)
    cols = ["baseline_id", "model_id", "dataset", "normalized_dataset",
            "dataset_present", "valid", "status", "reason"]
    write_csv(os.path.join(REPORT_DIR, "prediction_import_matrix.csv"), res["rows"], cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# Prediction Import Matrix", "", f"> 生成时间: {ts}",
         "> baseline_id × dataset 状态；不推理；不声称正式 gate。", ""]
    L.append(f"- rows: {res['n_rows']}；status 计数: {res['status_counts']}")
    L.append(f"- **ready_schema (importable now): {res['n_ready_schema']}**")
    L.append("")
    L.append("状态语义: ready_schema=可直接导入; convertible_nonformal=可转换但非正式 gate; "
             "needs_inference=有 ckpt 待推理(需批准); blocked_missing_dataset; "
             "blocked_missing_detector(RHINO/A4); unsupported; not_applicable(invalid baseline)。")
    L.append("")
    L.append("| baseline_id | model_id | dataset | status | reason |")
    L.append("|---|---|---|---|---|")
    for r in res["rows"][:50]:
        L.append(f"| {r['baseline_id']} | {r['model_id']} | {r['normalized_dataset']} | "
                 f"**{r['status']}** | {r['reason']} |")
    with open(os.path.join(REPORT_DIR, "prediction_import_matrix.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] import matrix: rows={res['n_rows']} counts={res['status_counts']} "
          f"ready_schema={res['n_ready_schema']}")
    print("[ok] wrote prediction_import_matrix.csv / .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

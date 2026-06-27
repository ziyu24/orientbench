#!/usr/bin/env python3
"""26_select_baselines.py — baseline selection shortlist (RHINO blocked, not substituted)."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.reports import write_csv  # noqa: E402
from orientbench.reports.baseline_shortlist import build_shortlist  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
REPORT_DIR = os.path.join(OUT, "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)
    res = build_shortlist(OUT)
    os.makedirs(REPORT_DIR, exist_ok=True)
    cols = ["archetype", "status", "baseline_id", "model_id", "dataset",
            "config", "checkpoint", "why_selected", "risks"]
    write_csv(os.path.join(REPORT_DIR, "baseline_shortlist.csv"), res["rows"], cols)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# Baseline Selection Shortlist", "", f"> 生成时间: {ts}",
         "> 优先接入 prediction 的最小集合；RHINO 单列 blocked，**不用 ARS-DETR 替代**。", ""]
    L.append(f"- selected: {res['n_selected']} / rows: {res['n_rows']}")
    L.append("")
    L.append("| archetype | status | baseline_id | model_id | dataset | why_selected | risks |")
    L.append("|---|---|---|---|---|---|---|")
    for r in res["rows"]:
        L.append(f"| {r['archetype']} | **{r['status']}** | {r.get('baseline_id')} | "
                 f"{r.get('model_id')} | {r.get('dataset')} | {r['why_selected']} | {r['risks']} |")
    with open(os.path.join(REPORT_DIR, "baseline_shortlist.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[ok] shortlist: selected={res['n_selected']} rows={res['n_rows']} "
          "(RHINO blocked_missing, not substituted)")
    print("[ok] wrote baseline_shortlist.csv / .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

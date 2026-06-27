#!/usr/bin/env python3
"""16_readiness_check.py — threshold-freeze / evaluation readiness (CHECK ONLY).

Writes outputs/bench_core/reports/readiness_check.{md,json}. Never freezes
thresholds; never promotes pending -> ready.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.reports import write_json  # noqa: E402
from orientbench.reports.readiness import build_host_decision_packet, build_readiness  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CONFIGS = os.path.join(_PROJECT_ROOT, "configs")
REPORT_DIR = os.path.join(OUT, "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    res = build_readiness(OUT, CONFIGS)
    os.makedirs(REPORT_DIR, exist_ok=True)
    write_json(os.path.join(REPORT_DIR, "readiness_check.json"), res)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# Threshold-Freeze / Evaluation Readiness Check", "", f"> 生成时间: {ts}",
         "> CHECK ONLY — 不冻结阈值; pending 不得改 ready; 无正式 gate 结论。", ""]
    L.append(f"- **overall_readiness: {res['overall_readiness']}**  "
             f"(ready={res['n_ready']} pending={res['n_pending']} blocked={res['n_blocked']})")
    L.append(f"- formal_gate_allowed: **{res['formal_gate_allowed']}**")
    L.append(f"- blockers: {res['blockers']}")
    L.append("")
    L.append("| item | status | detail |")
    L.append("|---|---|---|")
    for i in res["items"]:
        L.append(f"| {i['item']} | **{i['status']}** | {i['detail']} |")
    with open(os.path.join(REPORT_DIR, "readiness_check.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    with open(os.path.join(REPORT_DIR, "host_decision_packet.md"), "w", encoding="utf-8") as fh:
        fh.write(build_host_decision_packet(ts))
    print("[ok] wrote host_decision_packet.md")

    print(f"[ok] readiness: overall={res['overall_readiness']} "
          f"ready={res['n_ready']} pending={res['n_pending']} blocked={res['n_blocked']} "
          f"formal_gate_allowed={res['formal_gate_allowed']}")
    print("[ok] wrote readiness_check.md / readiness_check.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

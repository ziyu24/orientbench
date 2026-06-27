#!/usr/bin/env python3
"""17_training_readiness.py — training readiness (CHECK ONLY, does NOT train).

Writes outputs/bench_core/reports/training_readiness.{md,json}. Expected
conclusion: training_allowed=false.
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
from orientbench.reports.training_readiness import build_training_readiness  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CONFIGS = os.path.join(_PROJECT_ROOT, "configs")
REPORT_DIR = os.path.join(OUT, "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    res = build_training_readiness(OUT, CONFIGS)
    os.makedirs(REPORT_DIR, exist_ok=True)
    write_json(os.path.join(REPORT_DIR, "training_readiness.json"), res)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# Training Readiness Check", "", f"> 生成时间: {ts}",
         "> CHECK ONLY — 不启动训练; 明确何时才能训练。", ""]
    L.append(f"- **training_allowed: {res['training_allowed']}** / can_train_now: {res['can_train_now']} "
             f"(expected: {res['expected']})")
    L.append(f"- reasons: {res['reasons']}")
    L.append(f"- blockers: {res['blockers']}")
    L.append("")
    for key, title in [("remaining_before_training", "Remaining before training"),
                       ("human_decisions_required", "Human decisions required"),
                       ("files_needed", "Files needed"),
                       ("commands_allowed_after_approval", "Commands allowed AFTER approval"),
                       ("stop_conditions_for_first_epoch", "First-epoch stop conditions")]:
        L.append(f"## {title}")
        for x in res.get(key, []):
            L.append(f"- {x}")
        L.append("")
    L.append("## Checklist items")
    L.append("| item | status | detail |")
    L.append("|---|---|---|")
    for i in res["items"]:
        L.append(f"| {i['item']} | **{i['status']}** | {i['detail']} |")
    with open(os.path.join(REPORT_DIR, "training_readiness.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] training_readiness: training_allowed={res['training_allowed']} "
          f"(expected {res['expected']}); reasons={res['reasons']}")
    print("[ok] wrote training_readiness.md / training_readiness.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

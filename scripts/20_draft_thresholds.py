#!/usr/bin/env python3
"""20_draft_thresholds.py — write a threshold-freeze PROPOSAL draft (no freeze).

Writes configs/thresholds.draft.yaml and
outputs/bench_core/reports/threshold_freeze_proposal.md. Does NOT modify
configs/thresholds.yaml (freeze_status stays pending).
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import yaml

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.reports.threshold_proposal import build_threshold_draft  # noqa: E402

CONFIGS = os.path.join(_PROJECT_ROOT, "configs")
REPORT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    draft = build_threshold_draft()

    # safety: never write into the live thresholds.yaml; only the .draft file
    draft_path = os.path.join(CONFIGS, "thresholds.draft.yaml")
    with open(draft_path, "w", encoding="utf-8") as fh:
        fh.write("# AUTO-GENERATED DRAFT — proposed_by=claude_draft, approval_status=pending\n")
        fh.write("# 不是冻结值; 不要据此做正式 gate; 审批后由责任角色写入 thresholds.yaml.\n")
        yaml.safe_dump(draft, fh, allow_unicode=True, sort_keys=False)

    os.makedirs(REPORT_DIR, exist_ok=True)
    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# Threshold Freeze Proposal (DRAFT)", "", f"> 生成时间: {ts}",
         f"> proposed_by={draft['proposed_by']} approval_status={draft['approval_status']} "
         f"freeze_status={draft['freeze_status']}",
         "> 草案；不修改 thresholds.yaml；不冻结；待合作者审批。", ""]
    for block in ("B_C1", "A_A4", "D2"):
        L.append(f"## {block} (draft)")
        for k, v in draft[block].items():
            L.append(f"- {k}: {v}")
        L.append("")
    L.append("## Rationale")
    for k, v in draft["rationale"].items():
        L.append(f"- {k}: {v}")
    L.append("")
    L.append("## 审批流程")
    L.append("1. 各责任角色用 D_cal 数据标定占位数值；2. 填入 thresholds.yaml 并设 freeze_time + responsible_role；"
             "3. 设 freeze_status=frozen 后方可做正式 gate（本脚本不执行此步）。")
    with open(os.path.join(REPORT_DIR, "threshold_freeze_proposal.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] wrote {draft_path} (DRAFT, not frozen)")
    print(f"[ok] wrote threshold_freeze_proposal.md; thresholds.yaml UNCHANGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

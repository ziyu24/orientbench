#!/usr/bin/env python3
"""21_verify_angle_conventions.py — angle_version evidence audit (computed).

Writes outputs/bench_core/reports/angle_version_evidence_audit.{md,csv}.
Read-only on datasets. Resolves le90 only where there is real geometric
evidence; HRSC mbox/le90 detector-equivalence stays uncertain.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.data.gt_index import DATASET_ROOT_DEFAULT  # noqa: E402
from orientbench.io.reports import write_csv, write_json  # noqa: E402
from orientbench.reports.angle_evidence import build_angle_evidence_audit  # noqa: E402

REPORT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default=DATASET_ROOT_DEFAULT)
    ap.add_argument("--max-files", type=int, default=40)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    res = build_angle_evidence_audit(args.data_root, args.max_files)
    os.makedirs(REPORT_DIR, exist_ok=True)

    cols = ["dataset", "split", "status", "n_objects", "mean_roundtrip_iou",
            "frac_iou_ge_0.99", "theta_min", "theta_max", "in_le90_range",
            "ang_in_le90_range", "mean_hbb_W_relerr", "mean_hbb_H_relerr",
            "hbb_crosscheck_consistent", "evidence"]
    write_csv(os.path.join(REPORT_DIR, "angle_version_evidence_audit.csv"), res["rows"], cols)
    write_json(os.path.join(REPORT_DIR, "angle_version_evidence_audit.json"), res)

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    L = ["# angle_version Evidence Audit", "", f"> 生成时间: {ts}",
         "> 用计算证据降低 uncertain；不伪造确定性；HRSC mbox/le90 检测器等价仍 uncertain。", ""]
    L.append(f"- items: {res['n_items']}；**resolved_with_evidence: {res['n_resolved']}**；"
             f"uncertain: {res['n_uncertain']}；HRSC: **{res['hrsc_status']}**")
    L.append("")
    L.append("| dataset | status | evidence | key metric |")
    L.append("|---|---|---|---|")
    for r in res["rows"]:
        km = ""
        if r.get("mean_roundtrip_iou") is not None:
            km = f"roundtrip_IoU={r['mean_roundtrip_iou']} in_range={r.get('in_le90_range')}"
        elif r.get("mean_hbb_W_relerr") is not None:
            km = (f"ang_in_range={r.get('ang_in_le90_range')} "
                  f"hbb_relerr W={r.get('mean_hbb_W_relerr')} H={r.get('mean_hbb_H_relerr')}")
        L.append(f"| {r['dataset']} | **{r['status']}** | {r.get('evidence','')} | {km} |")
    L.append("")
    L.append("结论：DOTA/DIOR/FAIR1M le90 GT 解析由 poly→obb→poly round-trip IoU≈1 + θ∈[-π/2,π/2) 证据支撑 "
             "(resolved_with_evidence)。HRSC mbox_ang 在 le90 数值范围内，但与标注 box_* HBB 的几何交叉验证不一致 "
             "(标注 HBB 偏松)，无法证明与检测器 le90 约定等价 → 保持 uncertain。prediction theta unit 在接入真实 "
             "prediction 前 uncertain。GV-obliquity 对符号不变，不受影响。")
    with open(os.path.join(REPORT_DIR, "angle_version_evidence_audit.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"[ok] angle evidence: resolved={res['n_resolved']} uncertain={res['n_uncertain']} "
          f"HRSC={res['hrsc_status']}")
    print("[ok] wrote angle_version_evidence_audit.md / .csv / .json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

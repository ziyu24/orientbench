#!/usr/bin/env python3
"""30_run_inference_guarded.py — guarded inference DRY-RUN (never runs a detector).

Default: emits a dry-run plan + guard report for shortlist baselines. With
--approval-token AND --execute it still returns blocked_by_supervisor (cc must
not start detector inference this round).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import yaml

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.reports import write_json  # noqa: E402
from orientbench.reports.baseline_shortlist import build_shortlist  # noqa: E402
from orientbench.runners.inference_runner import run_guarded  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CONFIGS = os.path.join(_PROJECT_ROOT, "configs")
REPORT_DIR = os.path.join(OUT, "reports")
APPROVALS = os.path.join(CONFIGS, "approvals.yaml")


def _inv_record(bid):
    p = os.path.join(OUT, "baseline_inventory.json")
    with open(p, "r", encoding="utf-8") as fh:
        inv = json.load(fh)
    for r in inv["records"]:
        if str(r.get("id")) == str(bid):
            return r
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-id", default=None)
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--split", default="train")
    ap.add_argument("--approval-token", default=None)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    with open(os.path.join(CONFIGS, "thresholds.yaml"), "r", encoding="utf-8") as fh:
        thr_pending = (yaml.safe_load(fh) or {}).get("freeze_status") == "pending"

    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d_%H%M%S")
    targets = []
    if args.baseline_id:
        r = _inv_record(args.baseline_id)
        if r:
            targets.append((r, args.dataset or r.get("dataset"), args.split))
    else:
        sl = build_shortlist(OUT)
        for s in sl["rows"]:
            if s["status"] == "selected":
                r = _inv_record(s["baseline_id"])
                if r:
                    targets.append((r, r.get("dataset"), "train"))

    results = []
    for rec, ds, sp in targets:
        res = run_guarded(rec, ds, sp, ts, APPROVALS,
                          approval_token=args.approval_token, execute=args.execute,
                          thresholds_pending=thr_pending)
        results.append(res)
        print(f"[{res['status']}] b{res['baseline_id']} {res['model_id']} {ds} "
              f"guards_ok={res['guards']['all_ok']} detector_invoked={res['detector_invoked']}")

    os.makedirs(REPORT_DIR, exist_ok=True)
    write_json(os.path.join(REPORT_DIR, "inference_guarded_plan.json"),
               {"timestamp": ts, "execute_requested": bool(args.execute),
                "approval_token_present": bool(args.approval_token),
                "n_targets": len(results),
                "any_detector_invoked": any(r["detector_invoked"] for r in results),
                "results": results})
    print(f"[ok] guarded runner: {len(results)} targets, "
          f"any_detector_invoked=False, wrote inference_guarded_plan.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

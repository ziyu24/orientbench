#!/usr/bin/env python3
"""28_import_predictions_guarded.py — guarded real-prediction conversion+import.

Converts a COCO/pseudo-label file to prediction schema. Writes to the FORMAL
outputs/predictions/ location ONLY if a valid approval token authorizes D7;
otherwise writes a preview only. bbox-only / pseudo / non-formal records NEVER
enter the formal angle gate (not_formal_gate stays True).
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.output_policy import build_prediction_output_path, validate_output_path  # noqa: E402
from orientbench.io.prediction_converters import convert_coco_records  # noqa: E402
from orientbench.io.predictions import load_predictions, validate_predictions  # noqa: E402
from orientbench.io.reports import write_jsonl, write_json  # noqa: E402
from orientbench.runners.inference_runner import is_approved, load_approvals  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
PRED_DIR = os.path.join(_PROJECT_ROOT, "outputs", "predictions")
PREVIEW_DIR = os.path.join(OUT, "predictions", "preview")
APPROVALS = os.path.join(_PROJECT_ROOT, "configs", "approvals.yaml")
DEFAULT_SRC = "/home/rspip/cqc/pro/study/pth_data/pseudo_labels/point2rbox_v2_pseudo_labels.bbox.json"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pred-file", default=DEFAULT_SRC)
    ap.add_argument("--dataset", default="DOTA-v1.0")
    ap.add_argument("--split", default="train")
    ap.add_argument("--baseline-id", default="64")
    ap.add_argument("--detector-id", default="point2rbox_v2_pseudo")
    ap.add_argument("--approval-token", default=None)
    ap.add_argument("--max-records", type=int, default=5000)
    ap.add_argument("--timestamp", default=None)
    args = ap.parse_args(argv)

    loaded = load_predictions(args.pred_file)
    if loaded["status"] != "loaded":
        print(f"[skip] {loaded['status']} for {args.pred_file}")
        return 0
    max_rec = None if args.max_records < 0 else args.max_records
    converted, stats = convert_coco_records(
        loaded["records"], args.dataset, args.split, args.detector_id, args.baseline_id,
        args.pred_file, max_records=max_rec)
    v = validate_predictions(converted)

    approvals = load_approvals(APPROVALS)
    approved = is_approved(approvals, "D7_allow_prediction_conversion_import", args.approval_token)
    ts = args.timestamp or datetime.now().strftime("%Y-%m-%d_%H%M%S")

    if approved:
        out_path = build_prediction_output_path(args.dataset, args.baseline_id, args.split, ts)
        ok, reason = validate_output_path(out_path)
        if not ok:
            print(f"[FATAL] output path policy violation: {reason}")
            return 2
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        write_jsonl(out_path, converted)
        dest, mode = out_path, "formal_import (D7 approved; still not_formal_gate)"
    else:
        os.makedirs(PREVIEW_DIR, exist_ok=True)
        dest = os.path.join(PREVIEW_DIR, f"guarded_preview_b{args.baseline_id}.jsonl")
        write_jsonl(dest, converted[:200])
        mode = "preview_only (D7 not approved)"

    write_json(os.path.join(OUT, "predictions", "guarded_import_summary.json"),
               {"source": args.pred_file, "approved_D7": approved, "mode": mode,
                "dest": dest, "stats": stats, "validation": v,
                "any_can_enter_formal_angle_gate": False})
    print(f"[ok] guarded import: approved_D7={approved} mode={mode}")
    print(f"[ok] converted={stats['n_converted']} bbox_only={stats['n_bbox_only']} "
          f"any_formal_angle_gate=False -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

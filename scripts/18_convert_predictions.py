#!/usr/bin/env python3
"""18_convert_predictions.py — convert COCO/pseudo-label files to prediction schema.

Read-only on the source. Writes converted output to predictions/converted/
(does NOT overwrite formal prediction outputs). HBB bbox is flagged bbox_only /
not_orientation_prediction; nothing is presented as a formal OBB gate input.
"""
from __future__ import annotations

import argparse
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.prediction_converters import convert_coco_records  # noqa: E402
from orientbench.io.predictions import load_predictions, validate_predictions  # noqa: E402
from orientbench.io.reports import write_jsonl, write_json  # noqa: E402

PRED_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "predictions")
DEFAULT_SRC = "/home/rspip/cqc/pro/study/pth_data/pseudo_labels/point2rbox_v2_pseudo_labels.bbox.json"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pred-file", default=DEFAULT_SRC, help="source coco/pseudo-label file")
    ap.add_argument("--dataset", default="DOTA-v1.0")
    ap.add_argument("--split", default="train")
    ap.add_argument("--detector-id", default="point2rbox_v2_pseudo")
    ap.add_argument("--baseline-id", default="64")
    ap.add_argument("--out-dir", default=os.path.join(PRED_DIR, "converted"))
    ap.add_argument("--max-records", type=int, default=20000,
                    help="cap converted records (-1 = all). Recorded, not silent.")
    args = ap.parse_args(argv)

    loaded = load_predictions(args.pred_file)
    if loaded["status"] != "loaded":
        print(f"[skip] {loaded['status']} for {args.pred_file} (no conversion)")
        os.makedirs(args.out_dir, exist_ok=True)
        write_json(os.path.join(args.out_dir, "conversion_summary.json"),
                   {"source": args.pred_file, "status": loaded["status"]})
        return 0

    max_rec = None if args.max_records is not None and args.max_records < 0 else args.max_records
    converted, stats = convert_coco_records(
        loaded["records"], args.dataset, args.split, args.detector_id, args.baseline_id,
        args.pred_file, max_records=max_rec)
    v = validate_predictions(converted)

    os.makedirs(args.out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.pred_file))[0]
    out_path = os.path.join(args.out_dir, f"converted_{stem}.jsonl")
    write_jsonl(out_path, converted)
    summary = {
        "source": args.pred_file, "format": loaded["format"], "dataset": args.dataset,
        "split": args.split, "detector_id": args.detector_id, "baseline_id": args.baseline_id,
        "max_records": max_rec, "converted_path": out_path, "stats": stats,
        "schema_validation": v,
        "note": "not_formal_gate=True for all; pseudo-label/unverified; "
                "bbox_only records NOT orientation predictions",
    }
    write_json(os.path.join(args.out_dir, f"conversion_summary_{stem}.json"), summary)

    print(f"[ok] converted {stats['n_converted']}/{stats['n_source_records']} "
          f"(truncated={stats['truncated']}) kinds={stats['bbox_kind_counts']} "
          f"bbox_only={stats['n_bbox_only']} oriented={stats['n_oriented']}")
    print(f"[ok] schema validate: ok={v['n_ok']} bad={v['n_bad']} "
          f"(ok counts full 17-field schema; flags extra)")
    print(f"[ok] any_can_enter_formal_angle_gate={stats['any_can_enter_formal_angle_gate']}")
    print(f"[ok] wrote {out_path} (formal outputs NOT overwritten)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

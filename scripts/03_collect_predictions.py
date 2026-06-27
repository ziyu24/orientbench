#!/usr/bin/env python3
"""03_collect_predictions.py — prediction ingestion (SYNTHETIC dry-run / real load).

Default mode 'synthetic': derive predictions from the GT index (controlled
score + angle perturbation), flagged is_synthetic / not_detector_output. With
--pred-file, auto-detect format and load real predictions (validate only); if
the file is absent it records 'no_prediction_available' and falls back to
synthetic so the pipeline still runs. NEVER runs a detector.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.predictions import (  # noqa: E402
    PREDICTION_SCHEMA,
    generate_synthetic_predictions,
    load_predictions,
    validate_predictions,
)
from orientbench.io.reports import read_jsonl, write_jsonl, write_json  # noqa: E402

GT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "gt_index")
PRED_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "predictions")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["synthetic", "real"], default="synthetic")
    ap.add_argument("--detector", "--detector-id", dest="detector", default="synthetic_gv_proxy",
                    help="detector_id label (NOT a real detector in synthetic mode)")
    ap.add_argument("--baseline-id", default=None, help="baseline_id for real ingestion")
    ap.add_argument("--dataset", default=None, help="dataset tag for real ingestion")
    ap.add_argument("--split", default=None, help="split tag for real ingestion")
    ap.add_argument("--views", nargs="*", default=["original"],
                    help="informational view tags (original/rotated/padding_only/...)")
    ap.add_argument("--pred-file", default=None, help="real prediction file (auto-detect format)")
    ap.add_argument("--dry-run-validate-only", action="store_true",
                    help="validate + preview only; do NOT overwrite formal outputs")
    ap.add_argument("--gt-dir", default=GT_DIR)
    ap.add_argument("--out-dir", default=PRED_DIR)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    os.makedirs(args.out_dir, exist_ok=True)
    summary = {"mode": args.mode, "detector": args.detector, "views": args.views, "files": []}

    # real ingestion path (validate only / preview)
    if args.mode == "real" or args.pred_file:
        loaded = load_predictions(args.pred_file)
        summary["real_ingestion"] = {
            "pred_file": args.pred_file, "baseline_id": args.baseline_id,
            "dataset": args.dataset, "split": args.split,
            "status": loaded["status"], "format": loaded["format"],
            "n_records": len(loaded["records"]),
            "dry_run_validate_only": bool(args.dry_run_validate_only),
            "warnings": loaded["warnings"][:10],
        }
        if loaded["status"] == "loaded":
            v = validate_predictions(loaded["records"])
            summary["real_ingestion"]["validation"] = v
            preview_dir = os.path.join(args.out_dir, "preview")
            os.makedirs(preview_dir, exist_ok=True)
            preview_path = os.path.join(preview_dir, "pred_real_preview.jsonl")
            write_jsonl(preview_path, loaded["records"][:200])  # preview only, capped
            summary["real_ingestion"]["preview_path"] = preview_path
            print(f"[real] {args.pred_file}: format={loaded['format']} "
                  f"records={len(loaded['records'])} ok={v['n_ok']} bad={v['n_bad']} "
                  f"-> preview {preview_path} (formal outputs NOT overwritten)")
            write_json(os.path.join(args.out_dir, "predictions_summary.json"), summary)
            return 0
        # no real prediction available
        summary["real_ingestion"]["no_real_prediction_found"] = True
        print(f"[real] {loaded['status']} for {args.pred_file} (no_real_prediction_found)"
              + ("" if args.dry_run_validate_only else " -> falling back to synthetic"))
        if args.dry_run_validate_only:
            write_json(os.path.join(args.out_dir, "predictions_summary.json"), summary)
            return 0

    # synthetic mode
    files = sorted(glob.glob(os.path.join(args.gt_dir, "*.jsonl")))
    for f in files:
        gts = read_jsonl(f)
        if not gts:
            continue
        preds = generate_synthetic_predictions(gts, seed=args.seed, detector_id=args.detector)
        v = validate_predictions(preds)
        stem = os.path.basename(f).replace(".jsonl", "")
        out = os.path.join(args.out_dir, f"pred_{stem}.jsonl")
        write_jsonl(out, preds)
        summary["files"].append({"gt_file": os.path.basename(f), "pred_file": out,
                                 "n_preds": len(preds), "validation": v})
        print(f"[synthetic] {stem}: {len(preds)} preds (is_synthetic/not_detector_output), "
              f"valid={v['n_ok']}/{v['n_total']}")

    summary["schema"] = PREDICTION_SCHEMA
    write_json(os.path.join(args.out_dir, "predictions_summary.json"), summary)
    print(f"[ok] wrote {len(summary['files'])} synthetic prediction files to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

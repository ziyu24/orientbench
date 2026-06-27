#!/usr/bin/env python3
"""02_prepare_gt_index.py — build a light GT index for one (dataset, split).

Read-only on datasets. Writes a JSONL GT index + a CSV to
outputs/bench_core/gt_index/. Defaults to a light sanity sample (--max-files);
not a full-scale recomputation.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.data.gt_index import (  # noqa: E402
    DATASET_ROOT_DEFAULT,
    GT_SCHEMA,
    build_gt_index,
)

DEFAULT_OUT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "gt_index")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", required=True, help="e.g. dota10 / dota15 / dior / hrsc / fair1m")
    ap.add_argument("--data-root", default=DATASET_ROOT_DEFAULT)
    ap.add_argument("--split", default="train")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--max-files", type=int, default=50,
                    help="sample at most N annotation files (light sanity). -1 = all")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)

    max_files = None if args.max_files is not None and args.max_files < 0 else args.max_files

    res = build_gt_index(
        dataset=args.dataset, data_root=args.data_root, split=args.split,
        max_files=max_files, strict=args.strict,
    )

    if not res["supported"]:
        print(f"[unsupported] {args.dataset}: {res['warnings'][:2]}")
        return 0

    os.makedirs(args.out_dir, exist_ok=True)
    key = res["dataset_key"]
    stem = f"{key}_{args.split}"
    jsonl_path = os.path.join(args.out_dir, stem + ".jsonl")
    csv_path = os.path.join(args.out_dir, stem + ".csv")
    meta_path = os.path.join(args.out_dir, stem + ".meta.json")

    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for rec in res["records"]:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=GT_SCHEMA, extrasaction="ignore")
        w.writeheader()
        for rec in res["records"]:
            row = dict(rec)
            row["warnings"] = " | ".join(rec.get("warnings") or [])
            w.writerow(row)

    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump({
            "dataset": res["dataset"], "dataset_key": key, "split": args.split,
            "data_root": args.data_root, "max_files": max_files,
            "stats": res["stats"], "n_warnings": len(res["warnings"]),
            "warnings_sample": res["warnings"][:20],
        }, fh, ensure_ascii=False, indent=2)

    s = res["stats"]
    print(f"[ok] {res['dataset']} / {args.split}: files_ok={s.get('n_files_ok')} "
          f"objects={s.get('n_objects')} valid_geom={s.get('n_valid_geometry')} "
          f"invalid_geom={s.get('n_invalid_geometry')} warnings={len(res['warnings'])}")
    print(f"[ok] wrote {jsonl_path}")
    print(f"[ok] wrote {csv_path}")
    print(f"[ok] wrote {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

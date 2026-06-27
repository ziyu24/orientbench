#!/usr/bin/env python3
"""15_build_audit_splits.py — build deterministic D_cal / D_audit splits.

Reads GT index jsonl(s), assigns each image to D_cal or D_audit by md5 hash,
verifies mutual exclusivity, and writes per-dataset split CSVs + meta JSON to
outputs/bench_core/splits/.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.data.splits import build_audit_split  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv, write_json  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
GT_DIR = os.path.join(OUT, "gt_index")
SPLIT_DIR = os.path.join(OUT, "splits")

SPLIT_COLS = ["dataset", "split", "image_id", "object_count",
              "bucket_summary_if_available", "assigned_split", "hash_key"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gt-dir", default=GT_DIR)
    ap.add_argument("--cal-fraction", type=float, default=0.5)
    ap.add_argument("--salt", default="orientbench_v1")
    args = ap.parse_args(argv)

    os.makedirs(SPLIT_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(args.gt_dir, "*.jsonl")))
    all_ok = True
    summaries = []
    for f in files:
        recs = read_jsonl(f)
        if not recs:
            continue
        res = build_audit_split(recs, cal_fraction=args.cal_fraction, salt=args.salt)
        stem = os.path.basename(f).replace(".jsonl", "")
        write_csv(os.path.join(SPLIT_DIR, f"D_cal_{stem}.csv"), res["cal_rows"], SPLIT_COLS)
        write_csv(os.path.join(SPLIT_DIR, f"D_audit_{stem}.csv"), res["audit_rows"], SPLIT_COLS)
        write_json(os.path.join(SPLIT_DIR, f"split_meta_{stem}.json"), res["meta"])
        m = res["meta"]
        all_ok = all_ok and m["mutually_exclusive"]
        summaries.append({"stem": stem, **m})
        print(f"[ok] split {stem}: n_images={m['n_images']} cal={m['n_cal']} audit={m['n_audit']} "
              f"intersection={m['intersection_size']} mutually_exclusive={m['mutually_exclusive']}")

    write_json(os.path.join(SPLIT_DIR, "splits_summary.json"),
               {"cal_fraction": args.cal_fraction, "salt": args.salt,
                "all_mutually_exclusive": all_ok, "datasets": summaries})
    print(f"[ok] all_mutually_exclusive={all_ok}; wrote D_cal/D_audit CSVs + split_meta to {SPLIT_DIR}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

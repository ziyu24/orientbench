#!/usr/bin/env python3
"""05_make_buckets.py — Bench-Core-1 stress buckets + GV baseline (DRY-RUN).

Reads source records (outputs/bench_core/cache/sources_*.jsonl), computes
class-conditional dry-run percentile thresholds, assigns stress buckets, and
writes:
    outputs/bench_core/buckets/bucket_assignments_<key>_<split>.csv
    outputs/bench_core/reports/stress_bucket_summary.csv
    outputs/bench_core/reports/gv_obliquity_baseline.csv   (from GT index)

All bucket membership carries pending_threshold_freeze (R8). No gate decisions.
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import sys
from collections import defaultdict

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.buckets.stress_buckets import ALL_BUCKETS, assign_buckets, near_square_bucket  # noqa: E402
from orientbench.buckets.thresholds import compute_bucket_thresholds  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv, write_json  # noqa: E402
from orientbench.metrics.statistics import summarize  # noqa: E402

CACHE_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "cache")
GT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "gt_index")
BUCKET_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "buckets")
REPORT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "reports")

ASSIGN_COLS = ["dataset", "split", "image_id", "class_name", "obb_w", "obb_h",
               "obb_theta", "gv_ratio", "D_nbr", "R_nbr", "A_align", "E_layout",
               "V_layout", "V_bg", "E_bg", "aspect_ratio"] + ALL_BUCKETS + ["pending_threshold_freeze"]


def make_buckets_for_file(path):
    records = read_jsonl(path)
    if not records:
        return None
    thr = compute_bucket_thresholds(records)
    counts = {b: 0 for b in ALL_BUCKETS}
    rows = []
    for r in records:
        res = assign_buckets(r, thr)
        row = {k: r.get(k) for k in ("dataset", "split", "image_id", "class_name",
                                     "obb_w", "obb_h", "obb_theta", "gv_ratio",
                                     "D_nbr", "R_nbr", "A_align", "E_layout",
                                     "V_layout", "V_bg", "E_bg")}
        row["aspect_ratio"] = res["aspect_ratio"]
        for b in ALL_BUCKETS:
            v = res["buckets"][b]
            row[b] = int(v)
            counts[b] += int(v)
        row["pending_threshold_freeze"] = True
        rows.append(row)
    stem = os.path.basename(path).replace("sources_", "").replace(".jsonl", "")
    out_csv = os.path.join(BUCKET_DIR, f"bucket_assignments_{stem}.csv")
    write_csv(out_csv, rows, ASSIGN_COLS)
    return {"stem": stem, "n": len(records), "counts": counts,
            "dataset": records[0].get("dataset"), "split": records[0].get("split"),
            "thresholds": thr}


def gv_baseline_from_gt():
    """Aggregate GV-obliquity per dataset/split/class from GT index files."""
    rows = []
    files = sorted(glob.glob(os.path.join(GT_DIR, "*.jsonl")))
    for f in files:
        recs = read_jsonl(f)
        if not recs:
            continue
        from orientbench.metrics.gv import gv_obliquity
        groups = defaultdict(list)
        for r in recs:
            groups[(r["dataset"], r["split"], r.get("class_name", "unknown"))].append(r)
        for (ds, sp, cls), items in sorted(groups.items()):
            gv = []
            obb_needed = []
            ns = valid = invalid = 0
            for r in items:
                if not r.get("valid_geometry", False):
                    invalid += 1
                    continue
                g = gv_obliquity(r["obb_w"], r["obb_h"], r["obb_theta"])
                if math.isfinite(g["gv_ratio"]):
                    gv.append(g["gv_ratio"])
                    obb_needed.append(g["gv_obb_needed"])
                    valid += 1
                    if near_square_bucket(r["obb_w"], r["obb_h"])["is_member"]:
                        ns += 1
                else:
                    invalid += 1
            s = summarize(gv)
            rows.append({
                "dataset": ds, "split": sp, "class_name": cls, "count": len(items),
                "gv_mean": round(s["mean"], 5) if math.isfinite(s["mean"]) else "",
                "gv_median": round(s["median"], 5) if math.isfinite(s["median"]) else "",
                "gv_p10": round(s["p10"], 5) if math.isfinite(s["p10"]) else "",
                "gv_p90": round(s["p90"], 5) if math.isfinite(s["p90"]) else "",
                "obb_needed_mean": round(sum(obb_needed) / len(obb_needed), 5) if obb_needed else "",
                "near_square_count": ns, "valid_count": valid, "invalid_count": invalid,
            })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", default="core1")
    ap.add_argument("--cache-dir", default=CACHE_DIR)
    args = ap.parse_args(argv)

    os.makedirs(BUCKET_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    files = sorted(glob.glob(os.path.join(args.cache_dir, "sources_*.jsonl")))
    summary_rows = []
    threshold_dump = {}
    for f in files:
        res = make_buckets_for_file(f)
        if res is None:
            continue
        threshold_dump[res["stem"]] = res["thresholds"]
        row = {"dataset": res["dataset"], "split": res["split"], "n_objects": res["n"],
               "pending_threshold_freeze": True}
        row.update(res["counts"])
        summary_rows.append(row)
        print(f"[ok] buckets {res['stem']}: n={res['n']} " +
              " ".join(f"{b}={res['counts'][b]}" for b in ALL_BUCKETS))

    summary_cols = ["dataset", "split", "n_objects"] + ALL_BUCKETS + ["pending_threshold_freeze"]
    write_csv(os.path.join(REPORT_DIR, "stress_bucket_summary.csv"), summary_rows, summary_cols)
    write_json(os.path.join(BUCKET_DIR, "bucket_thresholds_dryrun.json"), threshold_dump)

    gv_rows = gv_baseline_from_gt()
    gv_cols = ["dataset", "split", "class_name", "count", "gv_mean", "gv_median",
               "gv_p10", "gv_p90", "obb_needed_mean", "near_square_count",
               "valid_count", "invalid_count"]
    write_csv(os.path.join(REPORT_DIR, "gv_obliquity_baseline.csv"), gv_rows, gv_cols)
    print(f"[ok] wrote stress_bucket_summary.csv ({len(summary_rows)} rows), "
          f"gv_obliquity_baseline.csv ({len(gv_rows)} class rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

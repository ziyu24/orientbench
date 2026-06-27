#!/usr/bin/env python3
"""06_compute_selection_scores.py — default selection score DRY-RUN.

Produces dry-run default selection scores from GT/GV (no detector predictions).
Writes per-object scores and a per-dataset/class summary report.

Explicitly: NOT detector prediction, NOT formal calibration, NOT official.
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

from orientbench.io.reports import read_jsonl, write_csv, write_jsonl  # noqa: E402
from orientbench.metrics.selection_score import (  # noqa: E402
    dryrun_scores_for_record,
    head_type_definitions,
)
from orientbench.metrics.statistics import summarize  # noqa: E402

GT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "gt_index")
CACHE_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "cache")
REPORT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "reports")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", default="core1")
    ap.add_argument("--gt-dir", default=GT_DIR)
    args = ap.parse_args(argv)

    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    files = sorted(glob.glob(os.path.join(args.gt_dir, "*.jsonl")))
    summary = []
    head_defs = head_type_definitions()
    for f in files:
        recs = read_jsonl(f)
        if not recs:
            continue
        scored = []
        by_cls = defaultdict(list)
        for r in recs:
            sc = dryrun_scores_for_record(r)
            out = {"dataset": r["dataset"], "split": r["split"], "image_id": r["image_id"],
                   "class_name": r.get("class_name", "unknown"), **sc}
            scored.append(out)
            if math.isfinite(sc["default_selection_score"]):
                by_cls[(r["dataset"], r["split"], r.get("class_name", "unknown"))].append(
                    sc["default_selection_score"])
        stem = os.path.basename(f).replace(".jsonl", "")
        write_jsonl(os.path.join(CACHE_DIR, f"scores_{stem}.jsonl"), scored)
        for (ds, sp, cls), vals in sorted(by_cls.items()):
            s = summarize(vals)
            summary.append({
                "dataset": ds, "split": sp, "class_name": cls, "n": s["n"],
                "score_definition": "calibrated_gv_obliquity_proxy",
                "score_mean": round(s["mean"], 5), "score_median": round(s["median"], 5),
                "score_p10": round(s["p10"], 5), "score_p90": round(s["p90"], 5),
                "score_mode": "dry_run",
                "not_detector_prediction": True, "not_formal_calibration": True,
                "not_official_result": True,
            })
        print(f"[ok] scores {stem}: {len(scored)} objects, {len(by_cls)} classes")

    cols = ["dataset", "split", "class_name", "n", "score_definition", "score_mean",
            "score_median", "score_p10", "score_p90", "score_mode",
            "not_detector_prediction", "not_formal_calibration", "not_official_result"]
    # prepend head-type definition rows as a documentation header block
    for ht, definition in head_defs.items():
        summary.insert(0, {"dataset": "_HEAD_TYPE_DEF_", "split": "", "class_name": ht,
                           "score_definition": definition, "score_mode": "definition",
                           "not_detector_prediction": True, "not_formal_calibration": True,
                           "not_official_result": True})
    write_csv(os.path.join(REPORT_DIR, "default_selection_score_report.csv"), summary, cols)
    print(f"[ok] wrote default_selection_score_report.csv ({len(summary)} rows incl head-type defs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""07_eval_risk_coverage.py — risk-coverage / NRC-AUC (DRY-RUN SANITY).

Preferred path (when predictions exist): match predictions to GT, use the
prediction score as selection_score and the matched angle error (deg) as
orientation_risk. With SYNTHETIC predictions this is still a sanity harness —
it does NOT measure any real detector. Fallback path (no predictions): legacy
synthetic-risk demo from dry-run selection scores.

Writes outputs/bench_core/reports/nrc_auc_summary.csv.
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import sys

import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.core.geometry import angle_error_deg  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CACHE_DIR = os.path.join(OUT, "cache")
PRED_DIR = os.path.join(OUT, "predictions")
GT_DIR = os.path.join(OUT, "gt_index")
REPORT_DIR = os.path.join(OUT, "reports")


def _synthetic_risk(scores: np.ndarray, seed: int = 0) -> np.ndarray:
    rng = np.random.RandomState(seed)
    base = (1.0 - np.clip(scores, 0.0, 1.0)) * 45.0
    return np.clip(base + rng.randn(scores.size) * 8.0, 0.0, 90.0)


def _eval(scores, risk, ds, sp, n_matched, n_preds, mode, approx, iou_method):
    scores = np.asarray(scores, dtype=float)
    risk = np.asarray(risk, dtype=float)
    if scores.size == 0:
        return None
    rc = risk_coverage_summary(scores, risk)
    nr = nrc_auc(scores, risk)
    return {
        "dataset": ds, "split": sp, "n": rc["n"], "n_matched": n_matched, "n_preds": n_preds,
        "AURC": round(rc["aurc"], 5), "Risk@70": round(rc["risk_at_70"], 5),
        "Risk@90": round(rc["risk_at_90"], 5),
        "NRC_AUC": round(nr["nrc_auc"], 5) if math.isfinite(nr["nrc_auc"]) else "",
        "oracle_AURC": round(nr["aurc_oracle"], 5), "random_AURC": round(nr["aurc_random"], 5),
        "degenerate_flag": nr["degenerate"], "risk_mode": mode,
        "iou_method": iou_method, "approximate_iou": approx,
        "not_detector_performance": True,
    }


def run_prediction_path():
    rows = []
    pred_files = sorted(glob.glob(os.path.join(PRED_DIR, "pred_*.jsonl")))
    for pf in pred_files:
        stem = os.path.basename(pf).replace("pred_", "").replace(".jsonl", "")
        gt_file = os.path.join(GT_DIR, stem + ".jsonl")
        preds = read_jsonl(pf)
        gts = read_jsonl(gt_file)
        if not preds or not gts:
            continue
        m = match_dataset(preds, gts)
        scores, risk = [], []
        for p_idx, g_idx, _iou in m["matched_pairs"]:
            p, g = preds[p_idx], gts[g_idx]
            err = angle_error_deg(math.degrees(p["obb_theta"]), math.degrees(g["obb_theta"]))
            if math.isfinite(err) and isinstance(p.get("score"), (int, float)):
                scores.append(p["score"])
                risk.append(err)
        row = _eval(scores, risk, preds[0]["dataset"], preds[0]["split"],
                    m["n_matched"], m["n_preds"], "synthetic_prediction_angle_error",
                    m["approximate_iou"], m["iou_method"])
        if row:
            rows.append(row)
            print(f"[pred] {row['dataset']}/{row['split']}: matched={m['n_matched']}/{m['n_preds']} "
                  f"AURC={row['AURC']} NRC-AUC={row['NRC_AUC']} Risk@70={row['Risk@70']} "
                  f"iou={m['iou_method']}")
    return rows


def run_synthetic_demo_path():
    rows = []
    for f in sorted(glob.glob(os.path.join(CACHE_DIR, "scores_*.jsonl"))):
        recs = read_jsonl(f)
        scores = np.array([r["default_selection_score"] for r in recs
                           if isinstance(r.get("default_selection_score"), (int, float))
                           and math.isfinite(r["default_selection_score"])], dtype=float)
        if scores.size == 0:
            continue
        risk = _synthetic_risk(scores, seed=0)
        row = _eval(scores, risk, recs[0]["dataset"], recs[0]["split"], 0, scores.size,
                    "synthetic_risk_demo", False, "n/a")
        if row:
            rows.append(row)
            print(f"[demo] {row['dataset']}/{row['split']}: AURC={row['AURC']} NRC-AUC={row['NRC_AUC']}")
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", default="sanity")
    ap.add_argument("--source", choices=["auto", "prediction", "demo"], default="auto")
    args = ap.parse_args(argv)
    os.makedirs(REPORT_DIR, exist_ok=True)

    has_preds = bool(glob.glob(os.path.join(PRED_DIR, "pred_*.jsonl")))
    if args.source == "prediction" or (args.source == "auto" and has_preds):
        rows = run_prediction_path()
        mode = "prediction"
    else:
        rows = run_synthetic_demo_path()
        mode = "demo"

    cols = ["dataset", "split", "n", "n_matched", "n_preds", "AURC", "Risk@70", "Risk@90",
            "NRC_AUC", "oracle_AURC", "random_AURC", "degenerate_flag", "risk_mode",
            "iou_method", "approximate_iou", "not_detector_performance"]
    write_csv(os.path.join(REPORT_DIR, "nrc_auc_summary.csv"), rows, cols)
    print(f"[ok] wrote nrc_auc_summary.csv ({len(rows)} rows, source={mode}) — "
          f"SYNTHETIC, sanity only, not detector performance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

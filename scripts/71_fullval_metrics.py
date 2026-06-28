#!/usr/bin/env python3
"""71_fullval_metrics.py — convert full-val raw->schema (SCRATCH) + metrics + project manifest (024).

Storage rule: raw pkl + schema jsonl live in SCRATCH; PROJECT keeps per-cell
manifest.json (sha256, counts, scratch paths, schema field list, validation
summary) + metrics_summary.csv. NEVER copies large files into the project. Run
with mr_dev1x.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import pickle
import sys
from collections import defaultdict

import numpy as np

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
from orientbench.io.predictions import validate_predictions  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402

SCRATCH = "/dev/shm/cqc/orientbench"
REP = os.path.join(P, "outputs", "bench_core", "reports")
SCORE_THR = 0.30
SCHEMA_FIELDS = ["image_id", "class_name", "obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta",
                 "score", "is_synthetic", "not_detector_output", "detector_id", "baseline_id",
                 "dataset", "split", "angle_version", "source_path", "converter_version",
                 "warnings", "scratch_path", "sha256"]

# (dataset, bid, adapter_for_classes, detector)
CELLS = [
    ("DIOR-R", "3", "configs/_adapters/fv_b3_DIOR-R.py", "oriented_rcnn"),
    ("FAIR1M-v1.0", "5", "configs/_adapters/fv_b5_FAIR1M.py", "oriented_rcnn"),
    ("SODA-A", "4", "configs/_adapters/fv_b4_SODA.py", "oriented_rcnn"),
]


def get_classes(cfg):
    from mmengine.config import Config
    c = Config.fromfile(os.path.join(P, cfg))
    d = c.get("test_dataloader", {}).get("dataset", {})
    mi = d.get("metainfo") or c.get("metainfo") or {}
    return list(mi["classes"]) if mi.get("classes") else None


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    rows, manifests = [], []
    for ds, bid, cfg, det in CELLS:
        pkl = f"{SCRATCH}/predictions/{ds}/{bid}/raw/result_b{bid}.pkl"
        gtp = f"{SCRATCH}/predictions/{ds}/{ds}_fullval_gt.jsonl"
        if not (os.path.isfile(pkl) and os.path.isfile(gtp)):
            rows.append({"dataset": ds, "baseline_id": bid, "status": "missing_pkl_or_gt"}); continue
        try:
            classes = get_classes(cfg)
        except Exception:
            classes = None
        data = pickle.load(open(pkl, "rb"))
        schema_path = f"{SCRATCH}/predictions/{ds}/{bid}/schema/pred_b{bid}_fullval.jsonl"
        os.makedirs(os.path.dirname(schema_path), exist_ok=True)
        n_pred = 0
        sample = None
        with open(schema_path, "w") as sf:
            for rec in data:
                img = rec.get("img_id") if isinstance(rec, dict) else getattr(rec, "img_id", None)
                pi = rec.get("pred_instances") if isinstance(rec, dict) else getattr(rec, "pred_instances", None)
                if pi is None:
                    continue
                bb = pi["bboxes"] if isinstance(pi, dict) else pi.bboxes
                sc = pi["scores"] if isinstance(pi, dict) else pi.scores
                lb = pi["labels"] if isinstance(pi, dict) else pi.labels
                bb = np.asarray(bb.cpu() if hasattr(bb, "cpu") else bb)
                sc = np.asarray(sc.cpu() if hasattr(sc, "cpu") else sc)
                lb = np.asarray(lb.cpu() if hasattr(lb, "cpu") else lb)
                for b, s, l in zip(bb, sc, lb):
                    cx, cy, w, h, th = [float(x) for x in b[:5]]
                    rec_d = {"image_id": str(img), "class_name": classes[int(l)] if classes and int(l) < len(classes) else str(int(l)),
                             "obb_cx": cx, "obb_cy": cy, "obb_w": w, "obb_h": h, "obb_theta": th, "score": float(s),
                             "is_synthetic": False, "not_detector_output": False, "detector_id": det, "baseline_id": bid,
                             "dataset": ds, "split": "fullval", "angle_version": "le90", "source_path": pkl,
                             "converter_version": "fv_v1", "warnings": "", "scratch_path": schema_path}
                    sf.write(json.dumps(rec_d) + "\n"); n_pred += 1
                    if sample is None:
                        sample = rec_d
        # metrics (stream-read schema + gt)
        preds = [json.loads(l) for l in open(schema_path)]
        gts = [json.loads(l) for l in open(gtp)]
        v = validate_predictions(preds[:5000])
        pset = [p for p in preds if p["score"] >= SCORE_THR]
        m = match_dataset(pset, gts)
        scr, rk, masked = [], [], 0
        for p_idx, g_idx, _ in m["matched_pairs"]:
            p, g = pset[p_idx], gts[g_idx]
            c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"], g["obb_w"], g["obb_h"], g["obb_theta"])
            if c["near_square"]:
                masked += 1; continue
            e = c["angle_error_canonical_longside"]
            if math.isfinite(e):
                scr.append(p["score"]); rk.append(e)
        rc = risk_coverage_summary(np.array(scr), np.array(rk)) if scr else {}
        nr = nrc_auc(np.array(scr), np.array(rk)) if scr else {}
        mt = {"dataset": ds, "baseline_id": bid, "detector": det, "split": "fullval", "n_pred": len(pset),
              "n_matched": m["n_matched"], "n_used": len(scr), "n_masked": masked,
              "median_orient_err_deg": round(float(np.median(rk)), 3) if rk else None,
              "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if scr else None,
              "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (scr and math.isfinite(nr.get("nrc_auc", float("nan")))) else None,
              "formal_scope": "cross_dataset_exploratory", "fullval": True}
        rows.append(mt)
        # project manifest (no large file in project)
        man = {"dataset": ds, "baseline_id": bid, "detector": det, "split": "fullval", "fullval": True,
               "raw_pkl_scratch": pkl, "raw_pkl_sha256": sha_file(pkl), "raw_pkl_bytes": os.path.getsize(pkl),
               "schema_scratch": schema_path, "schema_sha256": sha_file(schema_path),
               "schema_bytes": os.path.getsize(schema_path), "n_predictions": n_pred,
               "schema_fields": SCHEMA_FIELDS, "schema_valid_ok": v["n_ok"], "schema_valid_total": min(5000, len(preds)),
               "is_synthetic": False, "not_detector_output": False, "gt_scratch": gtp,
               "sample_prediction": sample, "metrics": {k: mt[k] for k in ("n_used", "median_orient_err_deg", "NRC_AUC", "Risk@90")}}
        proj_dir = os.path.join(P, "outputs", "predictions", ds, bid)
        os.makedirs(proj_dir, exist_ok=True)
        json.dump(man, open(os.path.join(proj_dir, "manifest.json"), "w"), indent=2, ensure_ascii=False)
        with open(os.path.join(proj_dir, "schema_validation.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["n_predictions", "schema_valid_ok", "schema_bytes", "schema_sha256"])
            w.writerow([n_pred, v["n_ok"], man["schema_bytes"], man["schema_sha256"][:16]])
        with open(os.path.join(proj_dir, "metrics_summary.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(mt.keys())); w.writeheader(); w.writerow(mt)
        manifests.append(man)
        print(f"[fullval {ds} #{bid}] n_pred={n_pred} n_used={mt['n_used']} NRC={mt['NRC_AUC']} "
              f"med_err={mt['median_orient_err_deg']} schema={man['schema_bytes']//1024}KB(scratch)")

    cols = ["dataset", "baseline_id", "detector", "split", "n_pred", "n_used", "median_orient_err_deg",
            "Risk@90", "NRC_AUC", "formal_scope", "fullval"]
    with open(os.path.join(REP, "metrics_024.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    with open(os.path.join(REP, "schema_validation_024.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["dataset", "baseline_id", "n_predictions", "schema_valid_ok", "schema_sha256", "scratch_path"])
        for mn in manifests:
            w.writerow([mn["dataset"], mn["baseline_id"], mn["n_predictions"], mn["schema_valid_ok"],
                        mn["schema_sha256"][:16], mn["schema_scratch"]])
    L = ["# Full-Val Metrics 024 (cross-dataset exploratory)", "",
         "> raw+schema in SCRATCH; project keeps manifest/sha256/metrics. ALL exploratory; thresholds unchanged.", "",
         "| dataset | baseline | detector | n_pred | n_used | median_orient_err° | Risk@90 | NRC-AUC | fullval |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "n_used" in r:
            L.append(f"| {r['dataset']} | {r['baseline_id']} | {r['detector']} | {r['n_pred']} | {r['n_used']} | "
                     f"{r['median_orient_err_deg']} | {r['Risk@90']} | {r['NRC_AUC']} | {r['fullval']} |")
    open(os.path.join(REP, "metrics_024.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] full-val metrics: {len([r for r in rows if 'n_used' in r])} cells")


if __name__ == "__main__":
    main()

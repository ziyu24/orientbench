#!/usr/bin/env python3
"""72_fullval_metrics_all.py — convert+metrics for ALL cross-dataset full-val cells (025).

Handles orcnn/psc/rtmdet (classes from pth_data baseline config) and LSKNet
(classes from pth_data baseline config too; model ran via ai4rs config + num_classes
override). raw+schema in SCRATCH; project keeps manifest/sha256/metrics. Run mr_dev1x.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import pickle
import sys

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
INV = json.load(open(os.path.join(P, "outputs/bench_core/baseline_inventory.json")))["records"]

# (dataset, bid, detector)  -- classes pulled from pth_data baseline config
CELLS = [
    ("DIOR-R", "22", "rotated_retinanet_psc"), ("DIOR-R", "61", "rotated_rtmdet_s"),
    ("DIOR-R", "10", "oriented_rcnn_lsknet"),
    ("FAIR1M-v1.0", "24", "rotated_retinanet_psc"), ("FAIR1M-v1.0", "12", "oriented_rcnn_lsknet"),
    ("SODA-A", "23", "rotated_retinanet_psc"), ("SODA-A", "11", "oriented_rcnn_lsknet"),
]


def baseline_classes(bid):
    cfg = next(r["config_abs"] for r in INV if str(r["id"]) == str(bid))
    from mmengine.config import Config
    try:
        c = Config.fromfile(cfg)
    except Exception:
        return None
    for path in ("test_dataloader", "train_dataloader", "val_dataloader"):
        d = c.get(path, {}).get("dataset", {})
        mi = d.get("metainfo") or {}
        if mi.get("classes"):
            return list(mi["classes"])
    for k in ("classes", "CLASSES"):
        if c.get(k):
            return list(c[k])
    return None


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def main():
    rows = []
    for ds, bid, det in CELLS:
        pkl = f"{SCRATCH}/predictions/{ds}/{bid}/raw/result_b{bid}.pkl"
        gtp = f"{SCRATCH}/predictions/{ds}/{ds}_fullval_gt.jsonl"
        if not (os.path.isfile(pkl) and os.path.isfile(gtp)):
            rows.append({"dataset": ds, "baseline_id": bid, "detector": det, "status": "missing_pkl_or_gt"})
            continue
        classes = baseline_classes(bid)
        if not classes:
            classes = baseline_classes({"DIOR-R": "3", "FAIR1M-v1.0": "5", "SODA-A": "4"}.get(ds))
        data = pickle.load(open(pkl, "rb"))
        schema = f"{SCRATCH}/predictions/{ds}/{bid}/schema/pred_b{bid}_fullval.jsonl"
        os.makedirs(os.path.dirname(schema), exist_ok=True)
        n = 0
        with open(schema, "w") as sf:
            for rec in data:
                img = rec.get("img_id") if isinstance(rec, dict) else getattr(rec, "img_id", None)
                pi = rec.get("pred_instances") if isinstance(rec, dict) else getattr(rec, "pred_instances", None)
                if pi is None:
                    continue
                bb = np.asarray((pi["bboxes"] if isinstance(pi, dict) else pi.bboxes).cpu() if hasattr((pi["bboxes"] if isinstance(pi, dict) else pi.bboxes), "cpu") else (pi["bboxes"] if isinstance(pi, dict) else pi.bboxes))
                sc = np.asarray((pi["scores"] if isinstance(pi, dict) else pi.scores).cpu() if hasattr((pi["scores"] if isinstance(pi, dict) else pi.scores), "cpu") else (pi["scores"] if isinstance(pi, dict) else pi.scores))
                lb = np.asarray((pi["labels"] if isinstance(pi, dict) else pi.labels).cpu() if hasattr((pi["labels"] if isinstance(pi, dict) else pi.labels), "cpu") else (pi["labels"] if isinstance(pi, dict) else pi.labels))
                for b, s, l in zip(bb, sc, lb):
                    cx, cy, w, h, th = [float(x) for x in b[:5]]
                    sf.write(json.dumps({"image_id": str(img), "class_name": classes[int(l)] if classes and int(l) < len(classes) else str(int(l)),
                                         "obb_cx": cx, "obb_cy": cy, "obb_w": w, "obb_h": h, "obb_theta": th, "score": float(s),
                                         "is_synthetic": False, "not_detector_output": False, "detector_id": det, "baseline_id": bid,
                                         "dataset": ds, "split": "fullval", "angle_version": "le90", "source_path": pkl,
                                         "converter_version": "fv_all_v1", "warnings": "", "scratch_path": schema}) + "\n")
                    n += 1
        preds = [json.loads(x) for x in open(schema)]
        gts = [json.loads(x) for x in open(gtp)]
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
        row = {"dataset": ds, "baseline_id": bid, "detector": det, "split": "fullval", "n_pred": len(pset),
               "n_used": len(scr), "n_masked": masked, "median_orient_err_deg": round(float(np.median(rk)), 3) if rk else None,
               "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if scr else None,
               "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (scr and math.isfinite(nr.get("nrc_auc", float("nan")))) else None,
               "formal_scope": "cross_dataset_exploratory", "fullval": True}
        rows.append(row)
        proj = os.path.join(P, "outputs", "predictions", ds, bid)
        os.makedirs(proj, exist_ok=True)
        json.dump({"dataset": ds, "baseline_id": bid, "detector": det, "split": "fullval", "fullval": True,
                   "raw_pkl_scratch": pkl, "raw_pkl_sha256": sha_file(pkl), "schema_scratch": schema,
                   "schema_sha256": sha_file(schema), "schema_bytes": os.path.getsize(schema), "n_predictions": n,
                   "schema_valid_ok": v["n_ok"], "is_synthetic": False, "not_detector_output": False,
                   "classes_n": len(classes) if classes else None, "metrics": {k: row[k] for k in ("n_used", "NRC_AUC", "median_orient_err_deg")}},
                  open(os.path.join(proj, "manifest.json"), "w"), indent=2)
        print(f"[{ds} #{bid} {det}] n_pred={len(pset)} n_used={len(scr)} NRC={row['NRC_AUC']} med_err={row['median_orient_err_deg']} cls={len(classes) if classes else '?'}")

    cols = ["dataset", "baseline_id", "detector", "split", "n_pred", "n_used", "median_orient_err_deg",
            "Risk@90", "NRC_AUC", "formal_scope", "fullval"]
    with open(os.path.join(REP, "metrics_025.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    L = ["# Metrics 025 (cross-dataset full-val: psc/rtmdet/LSKNet)", "",
         "> raw+schema in SCRATCH; project manifests. ALL exploratory; thresholds unchanged.", "",
         "| dataset | baseline | detector | n_pred | n_used | med_err° | Risk@90 | NRC-AUC |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "n_used" in r:
            L.append(f"| {r['dataset']} | {r['baseline_id']} | {r['detector']} | {r['n_pred']} | {r['n_used']} | "
                     f"{r['median_orient_err_deg']} | {r['Risk@90']} | {r['NRC_AUC']} |")
    open(os.path.join(REP, "metrics_025.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] 025 metrics: {len([r for r in rows if 'n_used' in r])} cells")


if __name__ == "__main__":
    main()

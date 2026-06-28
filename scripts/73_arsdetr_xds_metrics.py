#!/usr/bin/env python3
"""73_arsdetr_xds_metrics.py — convert ARS-DETR 0.1.0 cross-dataset output + metrics (028).

ARS-DETR 0.1.0 --out = list[per-image][per-class] ndarray[N,6] (cx,cy,w,h,ang,score),
image order = sorted annfiles. Maps to GT via farm stems; classes from the same
dataset's orcnn baseline config. raw+schema in SCRATCH; project keeps manifest.
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
# (dataset, arsdetr_bid, class_source_orcnn_bid)
CELLS = [("DIOR-R", "16", "3"), ("FAIR1M-v1.0", "18", "5"), ("SODA-A", "17", "4")]


def get_classes(bid):
    from mmengine.config import Config
    cfg = next(r["config_abs"] for r in INV if str(r["id"]) == str(bid))
    c = Config.fromfile(cfg)
    d = c.get("test_dataloader", {}).get("dataset", {})
    mi = d.get("metainfo") or {}
    return list(mi["classes"]) if mi.get("classes") else None


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def main():
    rows = []
    for ds, bid, csrc in CELLS:
        pkl = f"{SCRATCH}/predictions/{ds}/{bid}/raw/result_b{bid}.pkl"
        gtp = f"{SCRATCH}/predictions/{ds}/{ds}_fullval_gt.jsonl"
        if not (os.path.isfile(pkl) and os.path.isfile(gtp)):
            rows.append({"dataset": ds, "baseline_id": bid, "detector": "ars_detr", "status": "missing"})
            continue
        classes = get_classes(csrc)
        stems = sorted(os.path.splitext(f)[0] for f in os.listdir(f"{SCRATCH}/predictions/{ds}/_root/annfiles") if f.endswith(".txt"))
        data = pickle.load(open(pkl, "rb"))
        schema = f"{SCRATCH}/predictions/{ds}/{bid}/schema/pred_b{bid}.jsonl"
        os.makedirs(os.path.dirname(schema), exist_ok=True)
        n = 0
        with open(schema, "w") as sf:
            for i, per_img in enumerate(data):
                if i >= len(stems):
                    break
                img = stems[i]
                for ci, arr in enumerate(per_img):
                    arr = np.asarray(arr)
                    for row in arr:
                        cx, cy, w, h, ang, sc = [float(x) for x in row[:6]]
                        sf.write(json.dumps({"image_id": img, "class_name": classes[ci] if classes and ci < len(classes) else str(ci),
                                             "obb_cx": cx, "obb_cy": cy, "obb_w": w, "obb_h": h, "obb_theta": ang, "score": sc,
                                             "is_synthetic": False, "not_detector_output": False, "detector_id": "ars_detr",
                                             "baseline_id": bid, "dataset": ds, "split": "fullval", "angle_version": "le90",
                                             "source_path": pkl, "converter_version": "arsdetr010_xds_v1", "warnings": "",
                                             "scratch_path": schema}) + "\n")
                        n += 1
        preds = [json.loads(x) for x in open(schema)]
        gts = [json.loads(x) for x in open(gtp)]
        v = validate_predictions(preds[:5000])
        pset = [p for p in preds if p["score"] >= SCORE_THR]
        m = match_dataset(pset, gts)
        scr, rk, mask = [], [], 0
        for pi, gi, _ in m["matched_pairs"]:
            p, g = pset[pi], gts[gi]
            c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"], g["obb_w"], g["obb_h"], g["obb_theta"])
            if c["near_square"]:
                mask += 1; continue
            e = c["angle_error_canonical_longside"]
            if math.isfinite(e):
                scr.append(p["score"]); rk.append(e)
        rc = risk_coverage_summary(np.array(scr), np.array(rk)) if scr else {}
        nr = nrc_auc(np.array(scr), np.array(rk)) if scr else {}
        row = {"dataset": ds, "baseline_id": bid, "detector": "ars_detr", "n_pred": len(pset), "n_used": len(scr),
               "median_orient_err_deg": round(float(np.median(rk)), 3) if rk else None,
               "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if scr else None,
               "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (scr and math.isfinite(nr.get("nrc_auc", float("nan")))) else None,
               "formal_scope": "cross_dataset_exploratory", "independent_archetype": True, "not_RHINO_replacement": True}
        rows.append(row)
        proj = os.path.join(P, "outputs", "predictions", ds, bid)
        os.makedirs(proj, exist_ok=True)
        json.dump({**row, "raw_pkl_scratch": pkl, "raw_pkl_sha256": sha_file(pkl), "schema_scratch": schema,
                   "schema_sha256": sha_file(schema), "n_predictions": n, "schema_valid_ok": v["n_ok"],
                   "env": "arsdetr (mmrotate 0.1.0)"}, open(os.path.join(proj, "manifest.json"), "w"), indent=2)
        print(f"[ARS-DETR {ds} #{bid}] n_pred={len(pset)} n_used={len(scr)} NRC={row['NRC_AUC']} med_err={row['median_orient_err_deg']} cls={len(classes) if classes else '?'}")
    cols = ["dataset", "baseline_id", "detector", "n_pred", "n_used", "median_orient_err_deg", "Risk@90", "NRC_AUC", "formal_scope"]
    with open(os.path.join(REP, "arsdetr_xds_metrics_028.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"[ok] ARS-DETR xds metrics: {len([r for r in rows if 'n_used' in r])} cells")


if __name__ == "__main__":
    main()

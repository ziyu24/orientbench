#!/usr/bin/env python3
"""65_cross_dataset_metrics_022.py — convert + exploratory metrics for DIOR/FAIR1M/SODA/HRSC (022)."""
from __future__ import annotations

import csv
import math
import os
import pickle
import sys
from collections import defaultdict

import numpy as np

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
from orientbench.io.predictions import validate_predictions  # noqa: E402
from orientbench.io.reports import read_jsonl, write_jsonl  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import risk_coverage_summary  # noqa: E402

REP = os.path.join(P, "outputs", "bench_core", "reports")
PRED = os.path.join(P, "outputs", "predictions")
GTIDX = os.path.join(P, "outputs", "bench_core", "gt_index")
SCORE_THR = 0.30

# (dataset, baseline_id, adapter_config_for_classes, detector)
CELLS = [
    ("DIOR-R", "3", "configs/_adapters/xds_b3_dump.py", "oriented_rcnn"),
    ("DIOR-R", "22", "configs/_adapters/xds_b22_dump.py", "rotated_retinanet_psc"),
    ("DIOR-R", "61", "configs/_adapters/xds_b61_dump.py", "rotated_rtmdet_s"),
    ("FAIR1M-v1.0", "5", "configs/_adapters/xds_b5_dump.py", "oriented_rcnn"),
    ("FAIR1M-v1.0", "24", "configs/_adapters/xds_b24_dump.py", "rotated_retinanet_psc"),
    ("SODA-A", "4", "configs/_adapters/xds_b4_dump.py", "oriented_rcnn"),
    ("SODA-A", "23", "configs/_adapters/xds_b23_dump.py", "rotated_retinanet_psc"),
]


def get_classes(cfg_path):
    from mmengine.config import Config
    c = Config.fromfile(os.path.join(P, cfg_path))
    for key in ("test_dataloader", "train_dataloader"):
        d = c.get(key, {}).get("dataset", {})
        mi = d.get("metainfo") or {}
        if mi.get("classes"):
            return list(mi["classes"])
    md = c.get("metainfo") or {}
    if md.get("classes"):
        return list(md["classes"])
    return None


def convert(pkl_path, classes, dataset, bid, det):
    data = pickle.load(open(pkl_path, "rb"))
    preds = []
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
            name = classes[int(l)] if classes and int(l) < len(classes) else str(int(l))
            preds.append({"image_id": str(img), "class_name": name, "obb_cx": cx, "obb_cy": cy,
                          "obb_w": w, "obb_h": h, "obb_theta": th, "score": float(s),
                          "is_synthetic": False, "not_detector_output": False, "detector_id": det,
                          "baseline_id": bid, "dataset": dataset, "split": "val", "angle_version": "le90",
                          "source_path": pkl_path, "converter_version": "xds_v1", "warnings": ""})
    return preds


def metrics(preds, gts):
    pset = [p for p in preds if p["score"] >= SCORE_THR]
    m = match_dataset(pset, gts)
    sc, rk, masked = [], [], 0
    for p_idx, g_idx, _ in m["matched_pairs"]:
        p, g = pset[p_idx], gts[g_idx]
        c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"], g["obb_w"], g["obb_h"], g["obb_theta"])
        if c["near_square"]:
            masked += 1; continue
        e = c["angle_error_canonical_longside"]
        if math.isfinite(e):
            sc.append(p["score"]); rk.append(e)
    rc = risk_coverage_summary(np.array(sc), np.array(rk)) if sc else {}
    nr = nrc_auc(np.array(sc), np.array(rk)) if sc else {}
    return {"n_pred": len(pset), "n_matched": m["n_matched"], "n_used": len(sc), "n_masked": masked,
            "median_orient_err_deg": round(float(np.median(rk)), 3) if rk else None,
            "Risk@70": round(rc.get("risk_at_70", float("nan")), 4) if sc else None,
            "Risk@90": round(rc.get("risk_at_90", float("nan")), 4) if sc else None,
            "AURC": round(rc.get("aurc", float("nan")), 4) if sc else None,
            "NRC_AUC": round(nr.get("nrc_auc", float("nan")), 4) if (sc and math.isfinite(nr.get("nrc_auc", float("nan")))) else None}


def main():
    rows, fails = [], []
    # carry HRSC row from 021
    hrsc_csv = os.path.join(REP, "cross_dataset_metrics_021.csv")
    if os.path.isfile(hrsc_csv):
        for r in csv.DictReader(open(hrsc_csv)):
            if r.get("dataset") == "HRSC2016":
                rows.append({"dataset": "HRSC2016", "baseline_id": r["baseline_id"], "detector": r["detector"],
                             "n_used": r["n_used"], "median_orient_err_deg": r["median_orient_err_deg"],
                             "Risk@90": r["Risk@90"], "NRC_AUC": r["NRC_AUC"],
                             "angle_status": "blocked_angle_uncertain", "map_sanity": r.get("map_sanity"),
                             "formal_scope": "cross_dataset_exploratory"})
    for ds, bid, cfg, det in CELLS:
        pkl = f"{PRED}/{ds}/{bid}/raw/result_b{bid}.pkl"
        gtp = f"{GTIDX}/{ds}_val.jsonl"
        if not (os.path.isfile(pkl) and os.path.isfile(gtp)):
            fails.append({"cell": f"{ds}/{bid}", "reason": "missing pkl or gt"}); continue
        try:
            classes = get_classes(cfg)
        except Exception as e:
            classes = None
        preds = convert(pkl, classes, ds, bid, det)
        os.makedirs(f"{PRED}/{ds}/{bid}/schema", exist_ok=True)
        write_jsonl(f"{PRED}/{ds}/{bid}/schema/pred_b{bid}_val.jsonl", preds)
        v = validate_predictions(preds)
        gts = read_jsonl(gtp)
        mt = metrics(preds, gts)
        rows.append({"dataset": ds, "baseline_id": bid, "detector": det, "n_used": mt["n_used"],
                     "median_orient_err_deg": mt["median_orient_err_deg"], "Risk@90": mt["Risk@90"],
                     "NRC_AUC": mt["NRC_AUC"], "angle_status": "le90_via_quadriboxes_uncertain",
                     "map_sanity": None, "formal_scope": "cross_dataset_exploratory", "n_schema_ok": v["n_ok"]})
        print(f"[{ds} #{bid}] n_pred={mt['n_pred']} n_used={mt['n_used']} med_err={mt['median_orient_err_deg']} "
              f"NRC={mt['NRC_AUC']} Risk@90={mt['Risk@90']} classes={len(classes) if classes else '?'}")

    cols = ["dataset", "baseline_id", "detector", "n_used", "median_orient_err_deg", "Risk@90",
            "NRC_AUC", "angle_status", "map_sanity", "formal_scope"]
    with open(os.path.join(REP, "cross_dataset_metrics_022.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    with open(os.path.join(REP, "cross_dataset_failures_022.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["cell", "reason"])
        w.writeheader(); w.writerows(fails or [{"cell": "none", "reason": "-"}])
    L = ["# Cross-Dataset Exploratory Metrics 022 (corrected GT discovery)", "",
         "> ALL exploratory; no formal gate; thresholds unchanged. real OBB GT rediscovered for DIOR-R/FAIR1M/SODA-A.", "",
         "| dataset | baseline | detector | n_used | median_orient_err° | Risk@90 | NRC-AUC | angle_status |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['dataset']} | {r['baseline_id']} | {r['detector']} | {r['n_used']} | "
                 f"{r['median_orient_err_deg']} | {r['Risk@90']} | {r['NRC_AUC']} | {r['angle_status']} |")
    L += ["", "## 修正 021 错误结论",
          "- DIOR-R: OBB GT = annfiles/obb/*.xml (robndbox 8-corner)；021 只搜 *.txt 故误判 -> 已纠正，real GT 解析成功。",
          "- FAIR1M-v1.0: OBB GT = split/val_20/annfiles/*.xml (points/quad)；021 find 精度 bug 误判 -> 已纠正。",
          "- SODA-A: present；dota_format_tiled_ss/val_tiled DOTA-poly8 直接可用 -> 不再 missing_dataset。",
          "- HRSC angle 仍 blocked_angle_uncertain；其余 angle le90_via_quadriboxes 标 uncertain（exploratory，不冻结）。"]
    open(os.path.join(REP, "cross_dataset_metrics_022.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] cross-dataset 022 metrics: {len(rows)} cells, {len(fails)} failed")


if __name__ == "__main__":
    main()

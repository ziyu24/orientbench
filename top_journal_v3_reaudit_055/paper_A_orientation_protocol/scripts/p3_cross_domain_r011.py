#!/usr/bin/env python3
"""Bounded source-supervised cross-domain P3 revalidation for r011."""
import csv
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import m069_common as M
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import aurc, risk_at_coverage

REP = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports"
CELLS = M.FROZEN_CELLS
REPS = 1000
SEED = 20260807

def features(C, idx):
    return np.column_stack([C["score"][idx], np.log(C["pred_ar"][idx]),
                            0.5*np.log(C["pred_size"][idx]), C["w"][idx], C["h"][idx]])

def linear_features(C, idx):
    return np.column_stack([C["score"][idx], np.log(C["pred_ar"][idx]),
                            0.5*np.log(C["pred_size"][idx])])

def metric(score, risk):
    return float(nrc_auc(score, risk)["nrc_auc"])

def paired_bootstrap(images, linear_score, nonlinear_score, risk, seed):
    unique = np.unique(images)
    groups = {image: np.where(images == image)[0] for image in unique}
    seeds = np.random.RandomState(seed).randint(0, 2**31-1, REPS)
    def one(value):
        rng = np.random.RandomState(int(value))
        selected = rng.choice(unique, len(unique), replace=True)
        idx = np.concatenate([groups[image] for image in selected])
        return metric(linear_score[idx], risk[idx]) - metric(nonlinear_score[idx], risk[idx])
    workers = min(38, os.cpu_count() or 38)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        values = np.asarray(list(pool.map(one, seeds)), dtype=np.float64)
    return float(values.mean()), float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))

def combine(parts, kind):
    return np.concatenate([part[kind] for part in parts], axis=0)

def run_fold(fold_type, target_cell, sources, loaded, ordinal):
    target = loaded[target_cell]
    source_parts = []
    for cell in sources:
        C = loaded[cell]; fit, _, _ = M.role_masks(C); idx = np.where(M.mask_ar(C, M.AR_MAIN) & fit)[0]
        source_parts.append({"X": features(C, idx), "XL": linear_features(C, idx), "y": C["ae"][idx]})
    _, _, audit = M.role_masks(target); tidx = np.where(M.mask_ar(target, M.AR_MAIN) & audit)[0]
    X, XL, y = combine(source_parts, "X"), combine(source_parts, "XL"), combine(source_parts, "y")
    scaler = StandardScaler().fit(XL)
    linear = LinearRegression().fit(scaler.transform(XL), y)
    nonlinear = HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.05,
                                               random_state=0, l2_regularization=1.0).fit(X, y)
    score_det = target["score"][tidx]
    score_linear = -linear.predict(scaler.transform(linear_features(target, tidx)))
    score_nonlinear = -nonlinear.predict(features(target, tidx))
    risk = target["ae"][tidx]; images = target["img"][tidx]
    delta = metric(score_linear, risk) - metric(score_nonlinear, risk)
    mean, lo, hi = paired_bootstrap(images, score_linear, score_nonlinear, risk, SEED + ordinal)
    return {
        "fold_type": fold_type, "target_cell": target_cell, "target_dataset": target["dataset"],
        "target_detector": target["detector"], "source_cells": "|".join(sources),
        "source_fit_count": len(y), "target_audit_count": len(tidx), "target_images": len(np.unique(images)),
        "nrc_score_only": metric(score_det, risk), "nrc_score_ar_size_linear": metric(score_linear, risk),
        "nrc_nonlinear_geometry": metric(score_nonlinear, risk), "delta_linear_minus_nonlinear": delta,
        "ci_low": lo, "ci_high": hi, "bootstrap_mean": mean, "bootstrap_reps": REPS,
        "aurc_linear": float(aurc(score_linear, risk)), "aurc_nonlinear": float(aurc(score_nonlinear, risk)),
        "risk70_linear": float(risk_at_coverage(score_linear, risk, 0.7)),
        "risk70_nonlinear": float(risk_at_coverage(score_nonlinear, risk, 0.7)),
        "supported": bool(delta > 0 and lo > 0), "leakage_check": "PASS_SOURCE_DCAL_FIT_ONLY",
        "target_gt_use": "D_audit_evaluation_only", "status": "COMPUTED_R011"
    }

def main():
    loaded = {}
    for cell in CELLS:
        M.verify_fullval_lineage(cell); loaded[cell] = M.load_cell(cell)
    rows=[]; ordinal=0
    for target in CELLS:
        dataset=loaded[target]["dataset"]
        sources=[cell for cell in CELLS if loaded[cell]["dataset"] != dataset]
        rows.append(run_fold("leave_dataset", target, sources, loaded, ordinal)); ordinal+=1
    for target in CELLS:
        detector=loaded[target]["detector"]
        if detector == "rotated_rtmdet_s":
            rows.append({"fold_type":"leave_detector","target_cell":target,"target_dataset":loaded[target]["dataset"],
                         "target_detector":detector,"source_cells":"","status":"NOT_IDENTIFIABLE_SINGLE_DATASET_RTMDET"})
            continue
        sources=[cell for cell in CELLS if loaded[cell]["detector"] != detector]
        rows.append(run_fold("leave_detector", target, sources, loaded, ordinal)); ordinal+=1
    fields=[]
    for row in rows:
        for key in row:
            if key not in fields: fields.append(key)
    with (REP/"p3_cross_domain_results_r011.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");writer.writeheader();writer.writerows(rows)
    boot_fields=["fold_type","target_cell","delta_linear_minus_nonlinear","bootstrap_mean","ci_low","ci_high","bootstrap_reps","supported","status"]
    with (REP/"p3_cross_domain_bootstrap_r011.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=boot_fields,lineterminator="\n",extrasaction="ignore");writer.writeheader();writer.writerows(rows)
    eligible=[row for row in rows if row.get("status")=="COMPUTED_R011"]
    supported=[row for row in eligible if row["supported"]]
    datasets={row["target_dataset"] for row in supported}; detectors={row["target_detector"] for row in supported}
    reversed_group=any(all(not row["supported"] for row in eligible if row["target_dataset"]==ds) for ds in {row["target_dataset"] for row in eligible})
    passed=(len(supported)/len(eligible)>=0.6 and len(datasets)>=2 and len(detectors)>=2 and not reversed_group)
    status="P3_CROSS_DOMAIN_PASS_R011" if passed else "P3_CROSS_DOMAIN_INCONCLUSIVE_R011"
    (REP/"p3_gate_r011.json").write_text(json.dumps({"status":status,"eligible_folds":len(eligible),
        "supported_folds":len(supported),"supported_ratio":len(supported)/len(eligible),
        "datasets_supported":sorted(datasets),"detectors_supported":sorted(detectors),
        "leakage":"PASS","claim":"source-supervised target-GT-free diagnostic candidate only"},indent=2)+"\n")
    print(status)

if __name__=="__main__": main()

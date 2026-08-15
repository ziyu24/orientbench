#!/usr/bin/env python3
"""Implementation A for r036 evidence-increment and source-only calibration gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import resource
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814/inputs/qsetod_rows.parquet"
SEED = 20260814
CONFIGS = [
    ("HOdet_A_to_B", "A", "B"), ("HOdet_A_to_C", "A", "C"),
    ("HOdet_BC_to_A", "BC", "A"), ("HOdata_ABC_to_D", "ABC", "D"),
    ("HOdata_ABC_to_E", "ABC", "E"), ("HOdata_ABC_to_F", "ABC", "F"),
    ("HOdata_ABC_to_G", "ABC", "G"), ("HOdata_ABC_to_H", "ABC", "H"),
]
NUM_G = ["log_pred_ar", "log_area"]
NUM_E = ["log_pred_ar", "log_area", "u_axis", "missing_fraction", "iou_loss", "detection_score"]
G_BOOT = None


def design(frame: pd.DataFrame, classes: list[str], evidence: bool) -> np.ndarray:
    numeric = frame[NUM_E if evidence else NUM_G].to_numpy(np.float64)
    onehot = np.zeros((len(frame), len(classes)), dtype=np.float64)
    mapping = {name: i for i, name in enumerate(classes)}
    for row, name in enumerate(frame.class_name.astype(str)):
        idx = mapping.get(name)
        if idx is not None:
            onehot[row, idx] = 1.0
    return np.column_stack([numeric, onehot])


def model(loss: str) -> HistGradientBoostingRegressor:
    kw = dict(max_iter=200, max_leaf_nodes=15, learning_rate=0.05, random_state=SEED, early_stopping=False)
    if loss == "quantile":
        kw.update(loss="quantile", quantile=0.75)
    else:
        kw.update(loss="squared_error")
    return HistGradientBoostingRegressor(**kw)


def fit_source(source: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    classes = sorted(source.class_name.astype(str).unique())
    y = source.angle_error.to_numpy(float)
    oof = source[["row_id", "unit", "dataset", "cluster", "fold", "class_name", "log_pred_ar"]].copy()
    oof["geom_mean"] = np.nan; oof["evidence_mean"] = np.nan; oof["geom_q75"] = np.nan; oof["evidence_q75"] = np.nan
    for fold in range(5):
        train = source.loc[source.fold.ne(fold)]
        valid = source.loc[source.fold.eq(fold)]
        if train.empty or valid.empty:
            raise RuntimeError(f"empty cross-fit fold {fold}")
        train_y = train.angle_error.to_numpy(float)
        for loss, suffix in (("mean", "mean"), ("quantile", "q75")):
            for evidence, prefix in ((False, "geom"), (True, "evidence")):
                fitted = model(loss).fit(design(train, classes, evidence), train_y)
                oof.loc[valid.index, f"{prefix}_{suffix}"] = fitted.predict(design(valid, classes, evidence))
    if oof[["geom_mean", "evidence_mean", "geom_q75", "evidence_q75"]].isna().any().any():
        raise RuntimeError("OOF predictions incomplete")
    full = {"classes": classes}
    for loss, suffix in (("mean", "mean"), ("quantile", "q75")):
        for evidence, prefix in ((False, "geom"), (True, "evidence")):
            full[f"{prefix}_{suffix}"] = model(loss).fit(design(source, classes, evidence), y)
    return full, oof


def edges(values: np.ndarray) -> np.ndarray:
    result = np.unique(np.quantile(values, np.linspace(0, 1, 6), method="linear"))
    if len(result) < 2:
        result = np.array([-np.inf, np.inf])
    result[0] = -np.inf; result[-1] = np.inf
    return result


def assign(values: np.ndarray, boundary: np.ndarray) -> np.ndarray:
    return np.searchsorted(boundary[1:-1], values, side="right").astype(np.int16)


def common_support(source: pd.DataFrame, target: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    ar_edges, size_edges = edges(source.log_pred_ar.to_numpy(float)), edges(source.log_area.to_numpy(float))
    shared_classes = sorted(set(source.class_name).intersection(target.class_name))
    src = source.loc[source.class_name.isin(shared_classes)].copy(); tgt = target.loc[target.class_name.isin(shared_classes)].copy()
    for frame in (src, tgt):
        frame["ar_bin"] = assign(frame.log_pred_ar.to_numpy(float), ar_edges)
        frame["size_bin"] = assign(frame.log_area.to_numpy(float), size_edges)
        frame["support_cell"] = frame.class_name.astype(str) + "|" + frame.ar_bin.astype(str) + "|" + frame.size_bin.astype(str)
    cells = set(src.support_cell).intersection(tgt.support_cell)
    selected = tgt.loc[tgt.support_cell.isin(cells)].copy()
    meta = {"source_rows": len(source), "target_rows": len(target), "shared_classes": len(shared_classes), "common_cells": len(cells), "common_support_rows": len(selected), "common_support_fraction": len(selected) / len(target), "ar_edges": ar_edges.tolist(), "size_edges": size_edges.tolist()}
    if selected.empty:
        raise RuntimeError("empty common support")
    return selected, meta


def pinball(y: np.ndarray, q: np.ndarray, tau: float = .75) -> np.ndarray:
    d = y - q
    return np.maximum(tau * d, (tau - 1) * d)


def augrc(predicted_error: np.ndarray, y: np.ndarray, weights: np.ndarray | None = None) -> float:
    order = np.argsort(predicted_error, kind="stable")
    risk = np.clip(y[order] / 90.0, 0, 1)
    w = np.ones(len(order), float) if weights is None else weights[order].astype(float)
    total = w.sum()
    if total <= 0:
        return float("nan")
    cw = np.cumsum(w); cr = np.cumsum(w * risk)
    return float(np.sum((np.r_[0., cr[:-1] / total] + cr / total) * (w / total) / 2))


def point_metrics(frame: pd.DataFrame) -> dict:
    y = frame.angle_error.to_numpy(float); g = frame.geom_mean.to_numpy(float); e = frame.evidence_mean.to_numpy(float)
    gq = frame.geom_q75.to_numpy(float); eq = frame.evidence_q75.to_numpy(float)
    rg = float(spearmanr(g, y).statistic); re = float(spearmanr(e, y).statistic)
    qg = float(pinball(y, gq).mean()); qe = float(pinball(y, eq).mean())
    ag = augrc(g, y); ae = augrc(e, y)
    return {"spearman_geom": rg, "spearman_evidence": re, "spearman_gain": re-rg, "q75_loss_geom": qg, "q75_loss_evidence": qe, "q75_loss_gain": qg-qe, "AUGRC_geom": ag, "AUGRC_evidence": ae, "AUGRC_gain": ag-ae, "epsilon_AUGRC": max(.0005, .02 * max(abs(ag), abs(ae)))}


def pack_boot(frame: pd.DataFrame, multiplicities: np.ndarray) -> dict:
    clusters = sorted(frame.cluster.astype(str).unique()); cidx = {c:i for i,c in enumerate(clusters)}
    ci = frame.cluster.astype(str).map(cidx).to_numpy(np.int32)
    y = frame.angle_error.to_numpy(float); g = frame.geom_mean.to_numpy(float); e = frame.evidence_mean.to_numpy(float)
    gq = frame.geom_q75.to_numpy(float); eq = frame.evidence_q75.to_numpy(float)
    ry = rankdata(y, method="average"); rg = rankdata(g, method="average"); re = rankdata(e, method="average")
    sufficient = []
    for rx in (rg, re):
        sufficient.append(np.asarray([[np.sum(rx[ci == k]), np.sum(ry[ci == k]), np.sum(rx[ci == k]**2), np.sum(ry[ci == k]**2), np.sum(rx[ci == k]*ry[ci == k]), np.count_nonzero(ci == k)] for k in range(len(clusters))], float))
    qdiff = pinball(y, gq) - pinball(y, eq)
    qsum = np.bincount(ci, weights=qdiff, minlength=len(clusters)); count = np.bincount(ci, minlength=len(clusters)).astype(float)
    return {"ci": ci, "y": y, "g": g, "e": e, "suff": sufficient, "qsum": qsum, "count": count, "mult": multiplicities}


def corr_from_sufficient(stats: np.ndarray, mult: np.ndarray) -> float:
    sums = mult @ stats
    sx, sy, sxx, syy, sxy, n = sums
    cov = sxy - sx*sy/n; vx = sxx - sx*sx/n; vy = syy - sy*sy/n
    return float(cov / math.sqrt(max(vx*vy, 1e-30)))


def init_boot(pack):
    global G_BOOT
    G_BOOT = pack


def boot_chunk(bounds):
    first, last = bounds; out = np.empty((last-first, 3), float)
    for offset, rep in enumerate(range(first, last)):
        mult = G_BOOT["mult"][rep].astype(float)
        row_w = mult[G_BOOT["ci"]]
        rho_g = corr_from_sufficient(G_BOOT["suff"][0], mult)
        rho_e = corr_from_sufficient(G_BOOT["suff"][1], mult)
        qgain = float((mult @ G_BOOT["qsum"]) / (mult @ G_BOOT["count"]))
        again = augrc(G_BOOT["g"], G_BOOT["y"], row_w) - augrc(G_BOOT["e"], G_BOOT["y"], row_w)
        out[offset] = rho_e-rho_g, qgain, again
    return first, out


def conformal(source: pd.DataFrame, target: pd.DataFrame, config: str) -> list[dict]:
    ar_edges = edges(source.log_pred_ar.to_numpy(float)); source = source.copy(); target = target.copy()
    source["ar_bin"] = assign(source.log_pred_ar.to_numpy(float), ar_edges); target["ar_bin"] = assign(target.log_pred_ar.to_numpy(float), ar_edges)
    source["bucket"] = source.class_name.astype(str) + "|" + source.ar_bin.astype(str)
    target["bucket"] = target.class_name.astype(str) + "|" + target.ar_bin.astype(str)
    scores = source.angle_error.to_numpy(float) / np.maximum(source.geom_q75.to_numpy(float), 1.0)
    source["nonconformity"] = scores
    groups = {name: part.nonconformity.to_numpy(float) for name, part in source.groupby("bucket") if len(part) >= 50}
    result = []
    for alpha in (.1, .2):
        def quantile(values):
            level = min(1.0, math.ceil((len(values)+1)*(1-alpha))/len(values))
            return float(np.quantile(values, level, method="higher"))
        global_q = quantile(scores); thresholds = {name: quantile(values) for name, values in groups.items()}
        q = target.bucket.map(thresholds).fillna(global_q).to_numpy(float)
        half = q * np.maximum(target.geom_q75.to_numpy(float), 1.0)
        width = np.minimum(2*half, 180.0); covered = target.angle_error.to_numpy(float) <= half
        bucket_cov = pd.DataFrame({"bucket": target.bucket, "covered": covered}).groupby("bucket").covered.mean()
        result.append({"config": config, "target_unit": str(target.unit.iloc[0]), "alpha": alpha, "nominal_coverage": 1-alpha, "rows": len(target), "source_rows": len(source), "mondrian_non_sparse_buckets": len(groups), "global_threshold": global_q, "overall_coverage": float(covered.mean()), "coverage_deviation": float(covered.mean()-(1-alpha)), "worst_bucket_coverage": float(bucket_cov.min()), "median_width_deg": float(np.median(width)), "normalized_median_width": float(np.median(width)/180), "near_full_gt150_rate": float(np.mean(width>150)), "fallback_rate": float(np.mean(~target.bucket.isin(groups))), "kill": bool(abs(covered.mean()-(1-alpha)) > .05 or np.median(width) > 120)})
    return result


def leakage_probe(source: pd.DataFrame, source_key: str) -> list[dict]:
    evidence = source[["u_axis", "missing_fraction", "iou_loss"]].to_numpy(float)
    classes = sorted(source.class_name.unique()); class_design = design(source, classes, False)[:, 2:]
    targets = {"log_pred_ar": source.log_pred_ar.to_numpy(float), "log_area": source.log_area.to_numpy(float), "class_onehot": class_design}
    rows=[]
    for name, y in targets.items():
        pred = np.empty_like(y)
        for fold in range(5):
            tr = source.fold.ne(fold).to_numpy(); va = ~tr
            pred[va] = Ridge(alpha=1.0).fit(evidence[tr], y[tr]).predict(evidence[va])
        rows.append({"source_units": source_key, "target_z": name, "rows": len(source), "cross_fitted_R2": float(r2_score(y, pred, multioutput="variance_weighted"))})
    return rows


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--replicates", type=int, default=10000); parser.add_argument("--workers", type=int, default=96)
    args=parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True); started=time.time()
    rows=pd.read_parquet(INPUT); sources={}; oofs=[]; leakage=[]
    for source_key in ("A","BC","ABC"):
        source=rows.loc[rows.unit.isin(list(source_key))].copy().reset_index(drop=True)
        fitted,oof=fit_source(source); sources[source_key]=(source,fitted,oof); oof["source_units"]=source_key; oofs.append(oof); leakage.extend(leakage_probe(source,source_key))
    pd.concat(oofs,ignore_index=True).to_parquet(args.output/"source_oof_predictions.parquet",index=False,compression="zstd")
    pd.DataFrame(leakage).to_csv(args.output/"leakage_linear_probe.csv",index=False)

    result_rows=[]; prediction_parts=[]; conformal_rows=[]; multiplicities={}; support_rows=[]; replicate_parts=[]
    for config_number,(config,source_key,target_unit) in enumerate(CONFIGS):
        source,fitted,oof=sources[source_key]; target=rows.loc[rows.unit.eq(target_unit)].copy().reset_index(drop=True)
        classes=fitted["classes"]
        for evidence,prefix in ((False,"geom"),(True,"evidence")):
            for suffix in ("mean","q75"):
                target[f"{prefix}_{suffix}"]=fitted[f"{prefix}_{suffix}"].predict(design(target,classes,evidence))
        selected,meta=common_support(source,target); meta.update(config=config,source_units=source_key,target_unit=target_unit); support_rows.append(meta)
        point=point_metrics(selected)
        clusters=sorted(selected.cluster.astype(str).unique()); rng=np.random.RandomState(SEED+config_number)
        mult=np.empty((args.replicates,len(clusters)),np.int16)
        for rep in range(args.replicates): mult[rep]=np.bincount(rng.randint(0,len(clusters),len(clusters)),minlength=len(clusters))
        multiplicities[config]=mult
        package=pack_boot(selected,mult); block=np.empty((args.replicates,3),float)
        width=math.ceil(args.replicates/args.workers); jobs=[(i,min(i+width,args.replicates)) for i in range(0,args.replicates,width)]
        with mp.get_context("fork").Pool(args.workers,initializer=init_boot,initargs=(package,)) as pool:
            for first,values in pool.imap_unordered(boot_chunk,jobs): block[first:first+len(values)]=values
        names=["spearman_gain","q75_loss_gain","AUGRC_gain"]
        ci={}
        for j,name in enumerate(names): ci[name+"_ci_low"]=float(np.quantile(block[:,j],.025)); ci[name+"_ci_high"]=float(np.quantile(block[:,j],.975))
        all_ci_positive=all(ci[name+"_ci_low"]>0 for name in names)
        below_both=point["spearman_gain"]<.03 and point["AUGRC_gain"]<point["epsilon_AUGRC"]
        witness=bool(all_ci_positive and not below_both)
        result_rows.append({"config":config,"source_units":source_key,"target_unit":target_unit,"target_dataset":str(target.dataset.iloc[0]),"common_support_rows":len(selected),**point,**ci,"all_increment_ci_positive":all_ci_positive,"below_both_preregistered_floors":below_both,"evidence_witness":witness})
        replicate_parts.append(pd.DataFrame({"config":config,"replicate":np.arange(args.replicates),"spearman_gain":block[:,0],"q75_loss_gain":block[:,1],"AUGRC_gain":block[:,2]}))
        selected=selected.copy(); selected["config"]=config; prediction_parts.append(selected[["config","row_id","unit","dataset","cluster","class_name","ar_bin","size_bin","support_cell","angle_error","geom_mean","evidence_mean","geom_q75","evidence_q75"]])
        merged_oof=source.merge(oof[["row_id","geom_q75"]],on="row_id",validate="one_to_one")
        conformal_rows.extend(conformal(merged_oof,target,config))
    np.savez_compressed(args.output/"bootstrap_multiplicities.npz",**multiplicities)
    pd.concat(prediction_parts,ignore_index=True).to_parquet(args.output/"target_predictions_common_support.parquet",index=False,compression="zstd")
    pd.concat(replicate_parts,ignore_index=True).to_parquet(args.output/"bootstrap_replicates.parquet",index=False,compression="zstd")
    pd.DataFrame(support_rows).to_json(args.output/"common_support.jsonl",orient="records",lines=True)
    results=pd.DataFrame(result_rows); results.to_csv(args.output/"t2_evidence_increment.csv",index=False)
    ctable=pd.DataFrame(conformal_rows); ctable.to_csv(args.output/"t4_source_only_calibration.csv",index=False)
    kill_e=bool((~results.evidence_witness).all()); kill_c=bool(ctable.kill.any())
    state="QSETOD_KILLED_ON_PAPER" if kill_e else "QSETOD_EVIDENCE_ONLY" if kill_c else "QSETOD_PROCEED_CANDIDATE"
    judgment={"schema":"r036_judgment_partial_v1","KILL_E":kill_e,"KILL_C":kill_c,"evidence_witnesses":int(results.evidence_witness.sum()),"heldout_configurations":len(results),"candidate_state_before_PRUNE_M":state,"replicates":args.replicates,"seed":SEED,"elapsed_seconds":time.time()-started,"max_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (args.output/"judgment_partial.json").write_text(json.dumps(judgment,indent=2,sort_keys=True)+"\n")
    protocol={"schema":"r036_protocol_v1","seed":SEED,"replicates":args.replicates,"cross_folds":5,"fold_unit":"dataset/mother-image cluster","models":{"family":"HistGradientBoostingRegressor","max_iter":200,"max_leaf_nodes":15,"learning_rate":.05,"mean_loss":"squared_error","quantile_loss":"pinball tau=0.75"},"geometry_features":["log_pred_ar","log_area","class_onehot"],"evidence_features_added":["u_axis","missing_fraction","iou_loss","detection_score"],"common_support":"source-defined AR and size quintiles x normalized semantic class; cells nonempty in source and target","bootstrap_spearman":"cluster multiplicity reweighting of fixed observed-sample midranks","AUGRC_risk":"clip(angle_error/90,0,1)","epsilon_AUGRC":"max(0.0005,0.02*max(abs(AUGRC_geom),abs(AUGRC_evidence)))","evidence_witness":"all three increment CI lows >0 and not(spearman_gain<0.03 and AUGRC_gain<epsilon)","KILL_E":"all held-out configurations have no evidence_witness","mondrian":"class x source-defined predicted-AR quintile; source count <50 falls back to global","validator_output_forcing":False,"target_label_fit_guard":"only source-unit frames passed to fit/calibration; target angle labels consumed after frozen predictions for evaluation"}
    (args.output/"protocol.json").write_text(json.dumps(protocol,indent=2,sort_keys=True)+"\n")
    print(json.dumps(judgment,sort_keys=True))


if __name__=="__main__": main()

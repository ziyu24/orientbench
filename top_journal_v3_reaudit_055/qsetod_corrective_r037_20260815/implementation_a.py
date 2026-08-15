#!/usr/bin/env python3
"""Independent implementation A for r037 (fit and sealed evaluation phases)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor

SEED = 20260814
CONFIGS = [
    ("HOdet_A_to_B", "A", "B"), ("HOdet_A_to_C", "A", "C"),
    ("HOdet_BC_to_A", "BC", "A"), ("HOdata_ABC_to_D", "ABC", "D"),
    ("HOdata_ABC_to_E", "ABC", "E"), ("HOdata_ABC_to_F", "ABC", "F"),
    ("HOdata_ABC_to_G", "ABC", "G"), ("HOdata_ABC_to_H", "ABC", "H"),
]
LAYERS = {
    "G": ["log_pred_ar", "log_area"],
    "GC": ["log_pred_ar", "log_area", "detection_score"],
    "GCT": ["log_pred_ar", "log_area", "detection_score", "u_axis", "missing_fraction", "iou_loss"],
}
CTX = None
BOOT = None


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def design(frame: pd.DataFrame, classes: list[str], layer: str) -> np.ndarray:
    numeric = frame[LAYERS[layer]].to_numpy(np.float64)
    onehot = np.zeros((len(frame), len(classes)), np.float64)
    lookup = {v: i for i, v in enumerate(classes)}
    for i, value in enumerate(frame.class_name.astype(str).to_numpy()):
        j = lookup.get(value)
        if j is not None:
            onehot[i, j] = 1.0
    return np.column_stack([numeric, onehot])


def estimator(loss: str) -> HistGradientBoostingRegressor:
    kw = dict(max_iter=200, max_leaf_nodes=15, learning_rate=.05, random_state=SEED, early_stopping=False)
    if loss == "q75":
        kw.update(loss="quantile", quantile=.75)
    else:
        kw.update(loss="squared_error")
    return HistGradientBoostingRegressor(**kw)


def fit_task(task: tuple[str, int, str, str]) -> dict:
    source_key, fold, layer, loss = task
    item = CTX[source_key]
    train = np.ones(len(item["y"]), bool) if fold < 0 else item["fold"] != fold
    valid = None if fold < 0 else item["fold"] == fold
    started = time.time()
    fitted = estimator(loss).fit(item["x"][layer][train], item["y"][train])
    result = {"task": task, "started_unix": started, "ended_unix": time.time(), "train_rows": int(train.sum()), "train_clusters": int(np.unique(item["cluster"][train]).size)}
    if fold < 0:
        result["target"] = {config: fitted.predict(matrix[layer]) for config, matrix in item["target_x"].items()}
    else:
        result["valid_index"] = np.flatnonzero(valid)
        result["oof"] = fitted.predict(item["x"][layer][valid])
    return result


def edges(values: np.ndarray) -> np.ndarray:
    e = np.unique(np.quantile(values, np.linspace(0, 1, 6), method="linear"))
    if len(e) < 2:
        e = np.array([-np.inf, np.inf])
    e[0], e[-1] = -np.inf, np.inf
    return e


def bins(values: np.ndarray, e: np.ndarray) -> np.ndarray:
    return np.searchsorted(e[1:-1], values, side="right").astype(np.int8)


def support(source: pd.DataFrame, target: pd.DataFrame) -> tuple[np.ndarray, dict]:
    ae, se = edges(source.log_pred_ar.to_numpy(float)), edges(source.log_area.to_numpy(float))
    shared = sorted(set(source.class_name.astype(str)).intersection(target.class_name.astype(str)))
    src = source.loc[source.class_name.astype(str).isin(shared)].copy()
    tgt = target.loc[target.class_name.astype(str).isin(shared)].copy()
    src["ar_bin"], tgt["ar_bin"] = bins(src.log_pred_ar.to_numpy(float), ae), bins(tgt.log_pred_ar.to_numpy(float), ae)
    src["size_bin"], tgt["size_bin"] = bins(src.log_area.to_numpy(float), se), bins(tgt.log_area.to_numpy(float), se)
    for frame in (src, tgt):
        frame["support_cell"] = frame.class_name.astype(str) + "|" + frame.ar_bin.astype(str) + "|" + frame.size_bin.astype(str)
    src_keys = sorted(src.support_cell.unique())
    tgt_keys = sorted(tgt.support_cell.unique())
    keep_keys = sorted(set(src_keys).intersection(tgt_keys))
    keep = target.row_id.isin(tgt.loc[tgt.support_cell.isin(keep_keys), "row_id"]).to_numpy()
    def key_sha(keys: list[str]) -> str:
        return hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest()
    counts = tgt.groupby("support_cell").agg(rows=("row_id", "size"), clusters=("cluster", "nunique")).reset_index()
    meta = {"source_rows": len(source), "target_rows": len(target), "shared_classes": shared, "source_keys": src_keys, "target_keys": tgt_keys, "retained_keys": keep_keys, "excluded_target_keys": sorted(set(tgt_keys)-set(keep_keys)), "source_key_sha256": key_sha(src_keys), "target_key_sha256": key_sha(tgt_keys), "retained_key_sha256": key_sha(keep_keys), "common_support_rows": int(keep.sum()), "common_support_clusters": int(target.loc[keep, "cluster"].nunique()), "target_cell_counts": counts.to_dict("records"), "ar_edges": ae.tolist(), "size_edges": se.tolist()}
    if not keep.any():
        raise RuntimeError("empty common support")
    return keep, meta


def fit_phase(views: Path, output: Path, workers: int) -> None:
    global CTX
    output.mkdir(parents=True, exist_ok=False)
    sources, targets = {}, {}
    for source_key in ("A", "BC", "ABC"):
        sources[source_key] = pd.read_parquet(views / f"source_labeled_{source_key}.parquet")
    for config, _, _ in CONFIGS:
        targets[config] = pd.read_parquet(views / f"target_covariates_{config}.parquet")
        if "angle_error" in targets[config] or "signed_residual_deg" in targets[config]:
            raise RuntimeError("target label exposed to fit phase")
    CTX = {}
    for source_key, source in sources.items():
        classes = sorted(source.class_name.astype(str).unique())
        target_x = {}
        for config, key, _ in CONFIGS:
            if key == source_key:
                target_x[config] = {layer: design(targets[config], classes, layer) for layer in LAYERS}
        CTX[source_key] = {"y": source.angle_error.to_numpy(float), "fold": source.fold.to_numpy(int), "cluster": source.cluster.astype(str).to_numpy(), "x": {layer: design(source, classes, layer) for layer in LAYERS}, "target_x": target_x, "classes": classes}
    tasks = [(key, fold, layer, loss) for key in ("A", "BC", "ABC") for fold in (-1, 0, 1, 2, 3, 4) for layer in LAYERS for loss in ("mean", "q75")]
    with mp.get_context("fork").Pool(workers) as pool:
        results = pool.map(fit_task, tasks)
    by_task = {tuple(r["task"]): r for r in results}
    oof_parts, ledgers = [], []
    for source_key, source in sources.items():
        part = source[["row_id", "unit", "dataset", "detector", "cluster", "fold", "class_name", "log_pred_ar", "log_area", "angle_error"]].copy()
        for layer in LAYERS:
            for loss in ("mean", "q75"):
                col = f"{layer}_{loss}"
                part[col] = np.nan
                for fold in range(5):
                    result = by_task[(source_key, fold, layer, loss)]
                    part.loc[result["valid_index"], col] = result["oof"]
        if part.filter(regex="_(mean|q75)$").isna().any().any():
            raise RuntimeError("OOF incomplete")
        part["source_units"] = source_key
        oof_parts.append(part)
    pd.concat(oof_parts, ignore_index=True).to_parquet(output / "source_oof_predictions.parquet", index=False, compression="zstd")
    pred_parts, support_lines = [], []
    for config, source_key, target_unit in CONFIGS:
        target = targets[config].copy()
        keep, meta = support(sources[source_key], target)
        target = target.loc[keep].copy().reset_index(drop=True)
        full = {}
        for layer in LAYERS:
            for loss in ("mean", "q75"):
                full[f"{layer}_{loss}"] = by_task[(source_key, -1, layer, loss)]["target"][config][keep]
        for col, values in full.items():
            target[col] = values
        target.insert(0, "config", config)
        pred_parts.append(target)
        meta.update(config=config, source_units=source_key, target_unit=target_unit)
        support_lines.append(meta)
    pred_path = output / "target_predictions_common_support.parquet"
    pd.concat(pred_parts, ignore_index=True).to_parquet(pred_path, index=False, compression="zstd")
    with (output / "common_support.jsonl").open("w") as f:
        for row in support_lines:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    with (output / "fit_ledger.jsonl").open("w") as f:
        for result in sorted(results, key=lambda x: tuple(x["task"])):
            source_key, fold, layer, loss = result["task"]
            rec = {"source_units": source_key, "fold": fold, "layer": layer, "loss": loss, "row_count": result["train_rows"], "cluster_count": result["train_clusters"], "feature_schema": LAYERS[layer] + ["class_onehot"], "label_schema": ["angle_error"], "target_label_rows_in_fit": 0, "start_unix": result["started_unix"], "end_unix": result["ended_unix"], "exit": 0}
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    seal = {"schema_version": 1, "implementation": "A", "prediction_path": str(pred_path), "prediction_bytes": pred_path.stat().st_size, "prediction_sha256": sha(pred_path), "source_oof_sha256": sha(output / "source_oof_predictions.parquet"), "target_label_rows_in_fit": 0, "fit_count": len(results)}
    (output / "prediction_seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")


def pinball(y: np.ndarray, q: np.ndarray) -> np.ndarray:
    d = y-q
    return np.maximum(.75*d, -.25*d)


def augrc(pred: np.ndarray, y: np.ndarray, weights: np.ndarray | None = None) -> float:
    order = np.argsort(pred, kind="mergesort")
    ps, risk = pred[order], np.clip(y[order]/90., 0., 1.)
    w = np.ones(len(y), float) if weights is None else weights[order].astype(float)
    starts = np.r_[0, 1+np.flatnonzero(ps[1:] != ps[:-1])]
    gw = np.add.reduceat(w, starts); gr = np.add.reduceat(w*risk, starts)
    total = gw.sum(); curve = np.cumsum(gr)/total; prev = np.r_[0., curve[:-1]]
    return float(np.sum((prev+curve)*.5*(gw/total)))


def weighted_midrank(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort"); vs, ws = values[order], weights[order]
    starts = np.r_[0, 1+np.flatnonzero(vs[1:] != vs[:-1])]
    gid = np.cumsum(np.r_[True, vs[1:] != vs[:-1]])-1
    gw = np.add.reduceat(ws, starts); before = np.cumsum(gw)-gw
    group_rank = before + (gw+1.)/2.
    rank = np.empty(len(values), float); rank[order] = group_rank[gid]
    return rank


def wcorr(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    sw=w.sum(); mx=np.sum(w*x)/sw; my=np.sum(w*y)/sw
    return float(np.sum(w*(x-mx)*(y-my))/math.sqrt(max(np.sum(w*(x-mx)**2)*np.sum(w*(y-my)**2), 1e-30)))


def boot_init(payload: dict) -> None:
    global BOOT
    BOOT = payload


def boot_task(bounds: tuple[int, int]) -> tuple[int, np.ndarray]:
    first, last = bounds; out=np.empty((last-first,3),float)
    b=BOOT
    for j, rep in enumerate(range(first,last)):
        w=b["mult"][rep][b["ci"]].astype(float)
        ry=weighted_midrank(b["y"],w); rgc=weighted_midrank(b["gc"],w); rgct=weighted_midrank(b["gct"],w)
        dr=wcorr(rgct,ry,w)-wcorr(rgc,ry,w)
        dq=float(np.sum(w*b["qdiff"])/w.sum())
        da=augrc(b["gc"],b["y"],w)-augrc(b["gct"],b["y"],w)
        out[j]=(dr,dq,da)
    return first,out


def holm(p: list[float]) -> list[float]:
    order=np.argsort(p); adjusted=np.empty(len(p)); running=0.
    for rank, idx in enumerate(order):
        running=max(running,(len(p)-rank)*p[idx]); adjusted[idx]=min(1.,running)
    return adjusted.tolist()


def evaluate_phase(views: Path, output: Path, reps: int, workers: int) -> None:
    global BOOT
    seal=json.loads((output/"prediction_seal.json").read_text())
    pred_path=output/"target_predictions_common_support.parquet"
    if sha(pred_path) != seal["prediction_sha256"] or seal["target_label_rows_in_fit"] != 0:
        raise RuntimeError("prediction seal failed")
    preds=pd.read_parquet(pred_path); rows=[]; rep_parts=[]
    mult_dir=output/"multiplicities"; mult_dir.mkdir()
    for config_index,(config,_,target_unit) in enumerate(CONFIGS):
        frame=preds.loc[preds.config.eq(config)].copy()
        labels=pd.read_parquet(views/f"target_evaluation_labels_{config}.parquet")
        frame=frame.merge(labels[["row_id","angle_error"]],on="row_id",how="left",validate="one_to_one")
        if frame.angle_error.isna().any(): raise RuntimeError("evaluation join missing")
        y=frame.angle_error.to_numpy(float); gc=frame.GC_mean.to_numpy(float); gct=frame.GCT_mean.to_numpy(float)
        gcq=frame.GC_q75.to_numpy(float); gctq=frame.GCT_q75.to_numpy(float)
        point={"config":config,"target_unit":target_unit,"target_dataset":str(frame.dataset.iloc[0]),"target_detector":str(frame.detector.iloc[0]),"rows":len(frame),"clusters":int(frame.cluster.nunique())}
        point.update(rho_G=float(spearmanr(frame.G_mean,y).statistic),rho_GC=float(spearmanr(gc,y).statistic),rho_GCT=float(spearmanr(gct,y).statistic))
        point["Delta_rho"]=point["rho_GCT"]-point["rho_GC"]
        point.update(pinball_G=float(pinball(y,frame.G_q75.to_numpy(float)).mean()),pinball_GC=float(pinball(y,gcq).mean()),pinball_GCT=float(pinball(y,gctq).mean()))
        point["Delta_q75"]=point["pinball_GC"]-point["pinball_GCT"]
        point.update(AUGRC_G=augrc(frame.G_mean.to_numpy(float),y),AUGRC_GC=augrc(gc,y),AUGRC_GCT=augrc(gct,y))
        point["Delta_AUGRC"]=point["AUGRC_GC"]-point["AUGRC_GCT"]
        point["AUGRC_floor"]=max(.0005,.02*max(abs(point["AUGRC_GC"]),abs(point["AUGRC_GCT"])))
        clusters=sorted(frame.cluster.astype(str).unique()); lookup={v:i for i,v in enumerate(clusters)}
        ci=frame.cluster.astype(str).map(lookup).to_numpy(np.int32)
        rng=np.random.default_rng(20260815+config_index)
        mult=rng.multinomial(len(clusters),np.full(len(clusters),1/len(clusters)),size=reps).astype(np.uint8)
        np.savez_compressed(mult_dir/f"{config}.npz",multiplicities=mult,clusters=np.array(clusters))
        BOOT={"mult":mult,"ci":ci,"y":y,"gc":gc,"gct":gct,"qdiff":pinball(y,gcq)-pinball(y,gctq)}
        chunk=math.ceil(reps/workers); bounds=[(i,min(i+chunk,reps)) for i in range(0,reps,chunk)]
        with mp.get_context("fork").Pool(workers,initializer=boot_init,initargs=(BOOT,)) as pool:
            pieces=pool.map(boot_task,bounds)
        boot=np.empty((reps,3),float)
        for first,arr in pieces: boot[first:first+len(arr)]=arr
        for k,name in enumerate(("rho","q75","AUGRC")):
            point[f"Delta_{name}_ci_low"],point[f"Delta_{name}_ci_high"]=np.percentile(boot[:,k],[2.5,97.5])
            point[f"Delta_{name}_p"]=(1+int(np.count_nonzero(boot[:,k]<=0)))/(reps+1)
        point["p_unit"]=max(point["Delta_rho_p"],point["Delta_q75_p"],point["Delta_AUGRC_p"])
        rows.append(point)
        rep_parts.append(pd.DataFrame({"config":config,"replicate":np.arange(reps),"Delta_rho":boot[:,0],"Delta_q75":boot[:,1],"Delta_AUGRC":boot[:,2]}))
    adjusted=holm([r["p_unit"] for r in rows])
    for row,adj in zip(rows,adjusted):
        row["p_unit_holm8"]=adj
        row["witness"]=bool(all(row[f"Delta_{x}"]>0 and row[f"Delta_{x}_ci_low"]>0 for x in ("rho","q75","AUGRC")) and adj<=.05 and row["Delta_rho"]>=.02 and row["Delta_AUGRC"]>=row["AUGRC_floor"])
    table=pd.DataFrame(rows); table.to_csv(output/"t2_evidence_increment.csv",index=False)
    pd.concat(rep_parts,ignore_index=True).to_parquet(output/"bootstrap_replicates.parquet",index=False,compression="zstd")
    witness=table.loc[table.witness]
    cross=int(witness.config.str.startswith("HOdata").sum())
    passed=bool(len(witness)>=4 and witness.target_dataset.nunique()>=2 and witness.target_detector.nunique()>=2 and cross>=2)
    judgment={"schema_version":1,"implementation":"A","G_EVIDENCE":"PASS" if passed else "FAIL","witnesses":int(len(witness)),"witness_datasets":int(witness.target_dataset.nunique()),"witness_detector_families":int(witness.target_detector.nunique()),"cross_dataset_witnesses":cross,"candidate":"PROCEED_TO_G_SET" if passed else "QSETOD_KILLED_CORRECTED_EVIDENCE","completion_mode":"continue" if passed else "gated_early_stop","replicates":reps,"weighted_midrank":"recomputed per replicate","AUGRC_ties":"whole tie groups"}
    (output/"judgment_t2.json").write_text(json.dumps(judgment,indent=2,sort_keys=True)+"\n")


def higher_quantile(values: np.ndarray, alpha: float) -> float:
    level=min(1.,math.ceil((len(values)+1)*(1-alpha))/len(values))
    return float(np.quantile(values,level,method="higher"))


def interval_phase(views: Path, output: Path, reps: int, workers: int) -> None:
    judgment=json.loads((output/"judgment_t2.json").read_text())
    if judgment["G_EVIDENCE"] != "PASS":
        raise RuntimeError("G_SET must not run after G_EVIDENCE failure")
    preds=pd.read_parquet(output/"target_predictions_common_support.parquet")
    oof=pd.read_parquet(output/"source_oof_predictions.parquet")
    table_rows=[]; unit_rows=[]; interval_parts=[]
    for config,source_key,target_unit in CONFIGS:
        src=oof.loc[oof.source_units.eq(source_key)].copy()
        tgt=preds.loc[preds.config.eq(config)].copy()
        labels=pd.read_parquet(views/f"target_evaluation_labels_{config}.parquet")
        tgt=tgt.merge(labels[["row_id","angle_error"]],on="row_id",how="left",validate="one_to_one")
        ae,se=edges(src.log_pred_ar.to_numpy(float)),edges(src.log_area.to_numpy(float))
        for frame in (src,tgt):
            frame["primary_bucket"]=np.char.add(np.char.add(bins(frame.log_pred_ar.to_numpy(float),ae).astype(str),"|"),bins(frame.log_area.to_numpy(float),se).astype(str))
        source_bucket_stats=src.groupby("primary_bucket").agg(rows=("row_id","size"),clusters=("cluster","nunique"))
        local_keys=set(source_bucket_stats.loc[(source_bucket_stats.rows>=200)&(source_bucket_stats.clusters>=20)].index)
        result_by_alpha={}
        for alpha in (.1,.2):
            variant_data={}
            for variant in ("GC","GCT"):
                nonconf=src.angle_error.to_numpy(float)/np.maximum(src[f"{variant}_q75"].to_numpy(float),1.)
                global_q=higher_quantile(nonconf,alpha)
                work=src[["primary_bucket"]].copy(); work["nonconf"]=nonconf
                thresholds={k:higher_quantile(g.nonconf.to_numpy(float),alpha) for k,g in work.groupby("primary_bucket") if k in local_keys}
                fallback=~tgt.primary_bucket.isin(thresholds)
                q=tgt.primary_bucket.map(thresholds).fillna(global_q).to_numpy(float)
                half=np.minimum(90.,q*np.maximum(tgt[f"{variant}_q75"].to_numpy(float),1.))
                width=2*half; y=tgt.angle_error.to_numpy(float); covered=y<=half
                score=width+(2/alpha)*np.maximum(y-half,0.)
                variant_data[variant]={"half":half,"width":width,"covered":covered,"score":score,"fallback":fallback.to_numpy(),"global_q":global_q}
            gct=variant_data["GCT"]
            bucket_frame=pd.DataFrame({"bucket":tgt.primary_bucket,"covered":gct["covered"],"cluster":tgt.cluster.astype(str)})
            bst=bucket_frame.groupby("bucket").agg(rows=("covered","size"),clusters=("cluster","nunique"),coverage=("covered","mean"))
            supported=bst.loc[(bst.rows>=200)&(bst.clusters>=20)]
            nominal=1-alpha; overall=float(gct["covered"].mean()); median=float(np.median(gct["width"])); near=float(np.mean(gct["width"]>150)); fallback=float(np.mean(gct["fallback"]))
            overall_pass=overall>=nominal-.05
            bucket_pass=bool(len(supported)>0 and (supported.coverage>=nominal-.10).all())
            efficiency_pass=bool(median<=30 and near<=.10 and fallback<=.05)
            gc_mean=float(variant_data["GC"]["score"].mean()); gct_mean=float(gct["score"].mean()); paired=gc_mean-gct_mean; standardized=paired/gc_mean
            row={"config":config,"target_unit":target_unit,"target_dataset":str(tgt.dataset.iloc[0]),"target_detector":str(tgt.detector.iloc[0]),"alpha":alpha,"nominal_coverage":nominal,"rows":len(tgt),"clusters":int(tgt.cluster.nunique()),"overall_coverage":overall,"overall_validity_pass":overall_pass,"supported_buckets":len(supported),"worst_supported_bucket_coverage":float(supported.coverage.min()) if len(supported) else float("nan"),"supported_bucket_pass":bucket_pass,"median_width_deg":median,"near_full_gt150_rate":near,"global_fallback_rate":fallback,"efficiency_pass":efficiency_pass,"IS_GC":gc_mean,"IS_GCT":gct_mean,"paired_gain":paired,"standardized_paired_gain":standardized}
            table_rows.append(row); result_by_alpha[alpha]=(variant_data,row)
            part=tgt[["config","row_id","cluster"]].copy(); part["alpha"]=alpha
            for variant in ("GC","GCT"):
                part[f"half_width_{variant}"]=variant_data[variant]["half"]; part[f"IS_{variant}"]=variant_data[variant]["score"]
            interval_parts.append(part)
        clusters=sorted(tgt.cluster.astype(str).unique()); lookup={v:i for i,v in enumerate(clusters)}; ci=tgt.cluster.astype(str).map(lookup).to_numpy(np.int32)
        mult=np.load(output/"multiplicities"/f"{config}.npz",allow_pickle=False)["multiplicities"].astype(float)
        set_boot=np.zeros(reps,float)
        for alpha in (.1,.2):
            v,_=result_by_alpha[alpha]; diff=v["GC"]["score"]-v["GCT"]["score"]
            sums=np.bincount(ci,weights=diff,minlength=len(clusters)); base=np.bincount(ci,weights=v["GC"]["score"],minlength=len(clusters))
            set_boot += .5*((mult@sums)/(mult@base))
        point=float(np.mean([result_by_alpha[a][1]["standardized_paired_gain"] for a in (.1,.2)]))
        ci_low,ci_high=np.percentile(set_boot,[2.5,97.5]); p=(1+int(np.count_nonzero(set_boot<=0)))/(reps+1)
        unit_rows.append({"config":config,"target_unit":target_unit,"target_dataset":str(tgt.dataset.iloc[0]),"target_detector":str(tgt.detector.iloc[0]),"set_gain":point,"set_gain_ci_low":ci_low,"set_gain_ci_high":ci_high,"p_unit":p})
    detail=pd.DataFrame(table_rows); units=pd.DataFrame(unit_rows); units["p_unit_holm8"]=holm(units.p_unit.tolist())
    hard_by_config=detail.groupby("config").apply(lambda x: bool(x.overall_validity_pass.all() and x.supported_bucket_pass.all() and x.efficiency_pass.all()))
    units["both_alpha_hard_pass"]=units.config.map(hard_by_config)
    units["set_witness"]=(units.set_gain>0)&(units.set_gain_ci_low>0)&(units.p_unit_holm8<=.05)&(units.set_gain>=.02)&units.both_alpha_hard_pass
    detail.to_csv(output/"t3_interval_validity.csv",index=False); units.to_csv(output/"t3_set_gain.csv",index=False)
    pd.concat(interval_parts,ignore_index=True).to_parquet(output/"interval_predictions.parquet",index=False,compression="zstd")
    wit=units.loc[units.set_witness]
    all_overall=bool(detail.overall_validity_pass.all()); all_hard=bool(detail.supported_bucket_pass.all() and detail.efficiency_pass.all())
    passed=bool(len(wit)>=4 and wit.target_dataset.nunique()>=2 and wit.target_detector.nunique()>=2 and all_overall and all_hard)
    final={"schema_version":1,"implementation":"A","G_EVIDENCE":"PASS","G_SET":"PASS" if passed else "FAIL","set_witnesses":int(len(wit)),"witness_datasets":int(wit.target_dataset.nunique()),"witness_detector_families":int(wit.target_detector.nunique()),"all_16_overall_validity":all_overall,"all_16_supported_bucket_and_efficiency":all_hard,"candidate":"QSETOD_SINGLE_INTERVAL_PROCEED_CANDIDATE" if passed else "QSETOD_EVIDENCE_SCORE_ONLY"}
    (output/"judgment_final.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--phase",choices=["fit","evaluate","interval"],required=True); ap.add_argument("--views",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--workers",type=int,default=90); ap.add_argument("--replicates",type=int,default=20000)
    args=ap.parse_args()
    if args.phase=="fit": fit_phase(args.views,args.output,args.workers)
    elif args.phase=="evaluate": evaluate_phase(args.views,args.output,args.replicates,args.workers)
    else: interval_phase(args.views,args.output,args.replicates,args.workers)


if __name__=="__main__": main()

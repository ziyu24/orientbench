#!/usr/bin/env python3
"""r015 synchronized full-universe bootstrap; reads r014 artifacts only."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from derive_delta_theta_075 import load_interpolator

RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r014"
LABEL_ROOT = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
REPORTS = ROOT / "p3_selector/deployable_proxy_r015/reports"
NEW_RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r015"
UNITS = {
    "A": ("DIOR-R/22", "DIOR-R", "rotated_retinanet_psc"),
    "B": ("DIOR-R/3", "DIOR-R", "oriented_rcnn"),
    "C": ("DIOR-R/61", "DIOR-R", "rotated_rtmdet_s"),
    "D": ("FAIR1M-v1.0/24", "FAIR1M-v1.0", "rotated_retinanet_psc"),
    "E": ("SODA-A/23", "SODA-A", "rotated_retinanet_psc"),
    "F": ("SODA-A/4", "SODA-A", "oriented_rcnn"),
}
DATASETS = ("DIOR-R", "FAIR1M-v1.0", "SODA-A")
DTH = load_interpolator()
FRAMES: dict[str, dict] = {}

def sha_text(values: list[str]) -> str:
    return hashlib.sha256("\n".join(values).encode()).hexdigest()

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        out = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        out.writeheader(); out.writerows(rows)

def load_labels(unit: str) -> pd.DataFrame:
    rows = []
    with (LABEL_ROOT / unit / "matched_fullval.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line); gt = row.get("gt_obb", {})
            w, h = float(gt.get("obb_w", 0)), float(gt.get("obb_h", 0))
            if min(w, h) <= 0: continue
            ar = max(w, h) / min(w, h)
            if ar < 2.1 or row.get("d_cal_daudit_split_flag") != "D_audit": continue
            angle = float(row["angle_error"])
            rows.append({"image_id": str(row["image_id"]), "pred_id": int(row["pred_id"]),
                         "risk": min(angle / max(float(DTH(ar)), 1.0), 3.0)})
    return pd.DataFrame(rows)

def audit_clusters(unit: str) -> tuple[list[str], dict[str, str]]:
    universe = pd.read_csv(LABEL_ROOT / unit / "image_universe.csv", dtype={"image_id": str})
    universe = universe[universe["d_cal_daudit_split_flag"] == "D_audit"]
    ds = UNITS[unit][1]
    if ds != "SODA-A":
        ids = sorted(universe["image_id"].astype(str).unique())
        return ids, {x: x for x in ids}
    mapping = pd.read_csv(RUNTIME / "soda_tile_to_mother_r014.csv", dtype=str)
    mapping = mapping.set_index("tile_id")["mother_scene_id"].to_dict()
    missing = sorted(set(universe["image_id"].astype(str)) - set(mapping))
    if missing: raise RuntimeError(f"SODA mapping missing {len(missing)} audit tiles: {missing[:20]}")
    tile_to_cluster = {tile: str(mapping[tile]) for tile in universe["image_id"].astype(str)}
    return sorted(set(tile_to_cluster.values())), tile_to_cluster

def aurc_nrc(order: np.ndarray, risks: np.ndarray, weights: np.ndarray) -> float:
    # Stable score ordering is fixed. Repeated clusters become integer weights.
    r = risks[order]; w = weights[order].astype(np.int64)
    active = w > 0
    r, w = r[active], w[active]
    if not len(r): return float("nan")
    expanded = np.repeat(r, w)
    csum = np.cumsum(expanded); k = np.arange(1, len(expanded) + 1)
    model = float(np.mean(csum / k))
    oracle_r = np.sort(expanded, kind="stable")
    oracle = float(np.mean(np.cumsum(oracle_r) / k))
    random = float(np.mean(expanded)); denom = random - oracle
    return float("nan") if abs(denom) < 1e-12 else (model - oracle) / denom

def replicate(task: tuple[str, int, np.ndarray]) -> tuple[str, int, float]:
    dataset, rep, multiplicity = task
    values = []
    for unit, frame in FRAMES.items():
        if UNITS[unit][1] != dataset: continue
        weights = multiplicity[frame["cluster_pos"]]
        linear = aurc_nrc(frame["linear_order"], frame["risk"], weights)
        eqs = aurc_nrc(frame["eqs_order"], frame["risk"], weights)
        values.append((unit, linear - eqs))
    return dataset, rep, values

def percentile(x: np.ndarray, q: float) -> float: return float(np.percentile(x, q))
def p_centered(values: np.ndarray, point: float) -> float:
    return float((1 + int(np.sum((values - point) >= point))) / (len(values) + 1))
def holm(rows: list[dict], field: str, out: str) -> None:
    running = 0.0; total = len(rows)
    for rank, idx in enumerate(sorted(range(total), key=lambda i: rows[i][field])):
        running = max(running, min(1.0, (total-rank)*float(rows[idx][field])))
        rows[idx][out] = running

def main() -> None:
    os.environ.update({"OMP_NUM_THREADS":"1", "OPENBLAS_NUM_THREADS":"1", "MKL_NUM_THREADS":"1", "NUMEXPR_NUM_THREADS":"1"})
    REPORTS.mkdir(parents=True, exist_ok=True); NEW_RUNTIME.mkdir(parents=True, exist_ok=True)
    clusters_by_ds: dict[str, list[str]] = {}; cluster_maps: dict[str, dict[str, str]] = {}; universe_rows=[]
    for unit in UNITS:
        clusters, cmap = audit_clusters(unit); ds = UNITS[unit][1]
        cluster_maps[unit] = cmap
        universe_rows.append({"unit":unit,"dataset":ds,"cluster_count":len(clusters),"cluster_sha256":sha_text(clusters),"zero_eligible_included":True})
        if ds in clusters_by_ds and clusters != clusters_by_ds[ds]:
            old=set(clusters_by_ds[ds]); new=set(clusters)
            raise RuntimeError(f"FAIL_PROVENANCE_R015 cluster mismatch {ds}: missing={sorted(old-new)[:20]} extra={sorted(new-old)[:20]}")
        clusters_by_ds[ds] = clusters
    for unit in UNITS:
        labels = load_labels(unit)
        scores = pd.read_parquet(RUNTIME / "scores" / f"{unit}.parquet")
        frame = labels.merge(scores[["image_id","pred_id","score_ar_size_linear","EQS"]], on=["image_id","pred_id"], validate="one_to_one")
        cmap=cluster_maps[unit]; frame["cluster"] = frame["image_id"].map(cmap)
        if frame["cluster"].isna().any(): raise RuntimeError(f"missing cluster map {unit}")
        positions={c:i for i,c in enumerate(clusters_by_ds[UNITS[unit][1]])}
        frame["cluster_pos"] = frame["cluster"].map(positions).astype(int)
        risk=frame["risk"].to_numpy(float)
        FRAMES[unit]={"risk":risk,"cluster_pos":frame["cluster_pos"].to_numpy(int),
                      "linear_order":np.argsort(-frame["score_ar_size_linear"].to_numpy(float),kind="stable"),
                      "eqs_order":np.argsort(-frame["EQS"].to_numpy(float),kind="stable"),"rows":len(frame)}
        universe_rows[-1 if False else 0]
    # Retain full-universe evidence in runtime and report it in every result row.
    (NEW_RUNTIME / "cluster_universe_r015.json").write_text(json.dumps({d:{"count":len(c),"sha256":sha_text(c),"clusters":c} for d,c in clusters_by_ds.items()}, indent=2)+"\n")
    tasks=[]
    for ordinal, ds in enumerate(DATASETS):
        rng=np.random.RandomState(20260807+ordinal); n=len(clusters_by_ds[ds])
        draws=rng.randint(0,n,size=(1000,n))
        for rep, draw in enumerate(draws): tasks.append((ds,rep,np.bincount(draw,minlength=n)))
    started=time.time()
    with ProcessPoolExecutor(max_workers=38) as pool:
        output=list(pool.map(replicate,tasks,chunksize=1))
    elapsed=time.time()-started
    by_unit=defaultdict(lambda:np.empty(1000)); by_dataset=defaultdict(lambda:np.empty(1000))
    for ds,rep, values in output:
        for unit,value in values: by_unit[unit][rep]=value
    long=[]; unit_rows=[]
    for unit in UNITS:
        vals=by_unit[unit]; ds=UNITS[unit][1]; point=aurc_nrc(FRAMES[unit]["linear_order"],FRAMES[unit]["risk"],np.ones(FRAMES[unit]["rows"],dtype=int))-aurc_nrc(FRAMES[unit]["eqs_order"],FRAMES[unit]["risk"],np.ones(FRAMES[unit]["rows"],dtype=int))
        unit_rows.append({"unit":UNITS[unit][0],"unit_key":unit,"dataset":ds,"detector":UNITS[unit][2],"audit_rows":FRAMES[unit]["rows"],"audit_clusters_full":len(clusters_by_ds[ds]),"cluster_set_sha256":sha_text(clusters_by_ds[ds]),"delta_nrc":point,"ci_low":percentile(vals,2.5),"ci_high":percentile(vals,97.5),"p_centered_one_sided":p_centered(vals,point),"bootstrap_reps":1000})
        long.extend({"level":"unit","key":UNITS[unit][0],"dataset":ds,"replicate":i,"delta_nrc":float(v)} for i,v in enumerate(vals))
    holm(unit_rows,"p_centered_one_sided","holm6_p")
    for r in unit_rows: r["supported"]=bool(r["delta_nrc"]>=.02 and r["ci_low"]>0 and r["holm6_p"]<.05)
    ds_rows=[]
    for ds in DATASETS:
        keys=[u for u in UNITS if UNITS[u][1]==ds]; vals=np.mean(np.column_stack([by_unit[u] for u in keys]),axis=1); point=float(np.mean([next(r["delta_nrc"] for r in unit_rows if r["unit_key"]==u) for u in keys])); by_dataset[ds]=vals
        ds_rows.append({"dataset":ds,"units":"|".join(UNITS[u][0] for u in keys),"audit_clusters_full":len(clusters_by_ds[ds]),"cluster_set_sha256":sha_text(clusters_by_ds[ds]),"delta_nrc":point,"ci_low":percentile(vals,2.5),"ci_high":percentile(vals,97.5),"p_centered_one_sided":p_centered(vals,point),"bootstrap_reps":1000})
        long.extend({"level":"dataset","key":ds,"dataset":ds,"replicate":i,"delta_nrc":float(v)} for i,v in enumerate(vals))
    holm(ds_rows,"p_centered_one_sided","holm3_p")
    for r in ds_rows:r["supported"]=bool(r["delta_nrc"]>=.02 and r["ci_low"]>0 and r["holm3_p"]<.05)
    support=[r for r in unit_rows if r["supported"]]; ds_support=[r for r in ds_rows if r["supported"]]
    if len(support)>=4 and len({r["dataset"] for r in support})==3 and len({r["detector"] for r in support})>=2 and any(r["unit_key"]=="D" for r in support) and len(ds_support)==3: status="EXPLORATORY_CORE_SUPPORT_R015"
    elif len(support)<2 or any(r["ci_high"]<=0 for r in ds_rows): status="EXPLORATORY_CORE_NEGATIVE_R015"
    else: status="EXPLORATORY_CORE_INCONCLUSIVE_R015"
    write_csv(REPORTS/"unit_results_r015.csv",unit_rows); write_csv(REPORTS/"dataset_results_r015.csv",ds_rows); write_csv(REPORTS/"bootstrap_replicates_r015.csv",long)
    (REPORTS/"gate_r015.json").write_text(json.dumps({"r014_formal_verdict":"FAIL_PROTOCOL_R014","r015_numeric_status":status,"unit_support":len(support),"dataset_support":len(ds_support),"synchronized":True,"soda_primary":"mother_scene","elapsed_seconds":elapsed},indent=2)+"\n")
    write_csv(REPORTS/"resource_telemetry_r015.csv",[{"phase":"synchronized_cluster_bootstrap","workers":38,"blas_threads":1,"quota_percent":3840,"elapsed_seconds":elapsed,"samples":"start/end; CPU-intensive pool"}])
    print(json.dumps({"status":status,"unit_support":len(support),"dataset_support":len(ds_support),"elapsed":elapsed}))

if __name__ == "__main__": main()

#!/usr/bin/env python3
"""Generate the complete prelabel r019 seal without reading DOTA labels."""
from __future__ import annotations

import os
os.environ.update({"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})

import argparse
import csv
import hashlib
import io
import json
import math
import multiprocessing as mp
import pickle
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "p3_selector/deployable_proxy_r019/scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
import eqs_rc_r019 as eqs
from m069_common import delta_theta_075, split_role
from orientbench.metrics.nrc_auc import nrc_auc

WORK = ROOT / "p3_selector/deployable_proxy_r019"
PRE = WORK / "prelabel"
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r019"
RUNPRE = RUNTIME / "prelabel"
R014 = ROOT / "outputs/persistent_artifacts/orientbench_r014"
LABEL = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
DOTA_IMAGES = Path("/home/rspip/cqc/data/dataset/dota/split_ss_dota10_dota15/val/images")
PTH = Path("/home/rspip/cqc/pro/study/pth_data")
UNITS = {
    "A": ("DIOR-R/22", "DIOR-R", "rotated_retinanet_psc", R014 / "raw/dior22"),
    "B": ("DIOR-R/3", "DIOR-R", "oriented_rcnn", R014 / "raw/dior3"),
    "C": ("DIOR-R/61", "DIOR-R", "rotated_rtmdet_s", R014 / "raw/dior61"),
    "D": ("FAIR1M-v1.0/24", "FAIR1M-v1.0", "rotated_retinanet_psc", R014 / "raw/fair24"),
    "E": ("SODA-A/23", "SODA-A", "rotated_retinanet_psc", ROOT / "outputs/persistent_artifacts/orientbench_v2_047/tta_preds/SODA-A_23"),
    "F": ("SODA-A/4", "SODA-A", "oriented_rcnn", ROOT / "outputs/persistent_artifacts/orientbench_v2_047/tta_preds/SODA-A_4"),
}
FEATURES = eqs.FEATURE_COLUMNS
LINEAR = FEATURES[:3]
MONOTONIC = [-1, 0, 0, -1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
_RECORDS = None
_BOOT = None


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def set_sha(values) -> str:
    return hashlib.sha256("\n".join(sorted(map(str, values))).encode()).hexdigest()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        out = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); out.writeheader(); out.writerows(rows)


def inventory(path: Path, schema=None, rows=None, unique=None):
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path),
            "schema": schema or path.suffix.lstrip("."), "row_count": rows, "unique_keys": unique}


def preflight():
    PRE.mkdir(parents=True, exist_ok=True); RUNPRE.mkdir(parents=True, exist_ok=True)
    images = sorted(DOTA_IMAGES.glob("*.png"), key=lambda p: p.name)
    stems = [p.stem for p in images]
    mothers = [stem.split("__", 1)[0] for stem in stems]
    if len(images) != 5297 or len(set(stems)) != 5297 or any(not value for value in mothers):
        raise RuntimeError("DOTA image-only universe does not close at 5297 unique tiles")
    registry = {
        "schema": "r019_image_only_registry_v1", "tiles": [{"stem": p.stem, "path": str(p), "mother": p.stem.split("__", 1)[0]} for p in images],
        "tile_count": len(stems), "tile_set_sha256": set_sha(stems),
        "mother_count": len(set(mothers)), "mother_set_sha256": set_sha(set(mothers)),
        "unmapped": 0, "ambiguous": 0, "duplicate_tiles": len(stems) - len(set(stems)),
        "units": {
            "orcnn": {"config": str(PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py"), "checkpoint": str(PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth")},
            "rtmdet": {"config": str(PTH / "baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/config.py"), "checkpoint": str(PTH / "baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/best_mAP_7161_epoch_31.pth")},
        },
    }
    write_json(RUNPRE / "image_only_registry.json", registry)
    write_csv(RUNPRE / "tile_to_mother.csv", registry["tiles"])
    expected = {
        "orcnn": ("5076fefbcdb8763e68888abff9f9c39efa2b49881b4450c3f6240446a7898792", "f988b9a6b3d3662b22f2499679269bb00164417801957017082f6acdc9cf314c"),
        "rtmdet": ("d764820e7934f97ac1ab2a0f8e09a24ea3a126cd25e38bf5c2230bb59786fbe7", "fba480d7bd1172ee41fd2b89b314fb48a4e5c0e3b455815c838781b0127954ee"),
    }
    assets = []
    for key, spec in registry["units"].items():
        config, checkpoint = Path(spec["config"]), Path(spec["checkpoint"])
        row = {"unit": key, "config": str(config), "config_sha256": sha(config), "checkpoint": str(checkpoint), "checkpoint_sha256": sha(checkpoint)}
        row["pass"] = (row["config_sha256"], row["checkpoint_sha256"]) == expected[key]
        if not row["pass"]: raise RuntimeError(f"frozen asset mismatch {key}")
        assets.append(row)
    source_assets = []
    tta = pd.read_csv(ROOT / "p3_selector/deployable_proxy_r014/reports/tta_inventory_r014.csv")
    for row in tta.to_dict("records"):
        path = ROOT / str(row["path"])
        actual = sha(path)
        passed = path.is_file() and actual == str(row["sha256"]) and path.stat().st_size == int(row["bytes"])
        source_assets.append({"unit": row["unit_key"], "view": row["view"], "path": str(path),
                              "expected_sha256": row["sha256"], "actual_sha256": actual,
                              "bytes": path.stat().st_size, "pass": passed})
        if not passed:
            raise RuntimeError(f"Core source raw asset mismatch: {path}")
    provenance = pd.read_csv(ROOT / "p3_selector/deployable_proxy_r014/reports/provenance_r014.csv")
    source_lineage = []
    for row in provenance.to_dict("records"):
        gt = ROOT / str(row["gt"])
        universe = LABEL / str(row["unit_key"]) / "image_universe.csv"
        matched = LABEL / str(row["unit_key"]) / "matched_fullval.jsonl"
        checks = {
            "gt": gt.is_file() and sha(gt) == str(row["gt_sha256"]),
            "image_universe": universe.is_file(),
            "matched_labels": matched.is_file(),
        }
        if not all(checks.values()):
            raise RuntimeError(f"Core source lineage incomplete for {row['unit_key']}: {checks}")
        source_lineage.append({"unit": row["unit_key"], "gt": str(gt), "gt_sha256": sha(gt),
                               "image_universe": str(universe), "image_universe_sha256": sha(universe),
                               "matched_labels": str(matched), "matched_labels_sha256": sha(matched),
                               "checks": checks})
    prior = {"searched_before_label": True, "same_endpoint_found": False, "classification": "NO_PRIOR_EQS_RC_R019_ENDPOINT", "excluded_label_paths": True,
             "repository_name_search": [], "persistent_prediction_only_candidates": []}
    write_json(PRE / "preflight_r019.json", {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "B_blob": subprocess.check_output(["git", "rev-parse", "HEAD:dis/B.md"], cwd=ROOT, text=True).strip(), "working_tree_clean_at_start": True, "image_registry": {k: registry[k] for k in ("tile_count", "tile_set_sha256", "mother_count", "mother_set_sha256", "unmapped", "ambiguous", "duplicate_tiles")}, "assets": assets, "source_raw_assets": source_assets, "source_lineage": source_lineage, "prior_exposure": prior, "status": "PASS_PREFLIGHT_R019"})
    return registry


def _feature_worker(index):
    return eqs._aggregate_image(_RECORDS[0][index], _RECORDS[1][index], _RECORDS[2][index], delta_theta_075)


def build_features(unit: str, paths: list[Path], output: Path, workers=38):
    global _RECORDS
    loaded = []
    for path in paths:
        with path.open("rb") as handle: records = pickle.load(handle)
        loaded.append(sorted(records, key=lambda r: str(r["img_id"])))
    ids = [[str(r["img_id"]) for r in rows] for rows in loaded]
    if not (ids[0] == ids[1] == ids[2]) or len(ids[0]) != len(set(ids[0])):
        raise RuntimeError(f"raw view universe mismatch {unit}")
    _RECORDS = loaded
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(".partial")
    writer = None; nrows = 0
    with mp.get_context("fork").Pool(workers) as pool:
        for rows in pool.imap(_feature_worker, range(len(ids[0])), chunksize=4):
            if not rows: continue
            table = pa.Table.from_pylist(rows)
            if writer is None: writer = pq.ParquetWriter(partial, table.schema, compression="zstd")
            writer.write_table(table); nrows += len(rows)
    if writer is None: raise RuntimeError(f"empty feature output {unit}")
    writer.close(); partial.replace(output)
    frame = pd.read_parquet(output, columns=["image_id", "pred_id"])
    if frame.duplicated().any(): raise RuntimeError(f"duplicate feature keys {unit}")
    return {"unit": unit, "images": len(ids[0]), "rows": nrows, **inventory(output, "parquet", nrows, len(frame))}


def merge_forward(unit: str, expected_images: int):
    raw_dir = RUNPRE / "raw" / unit
    records = []
    for part in sorted(raw_dir.glob("part*.pkl")):
        with part.open("rb") as handle: records.extend(pickle.load(handle))
    by_view = {view: [] for view in ("identity", "hflip", "vflip")}
    for row in records: by_view[row["view"]].append(row)
    out = []
    for view, rows in by_view.items():
        rows.sort(key=lambda r: str(r["img_id"]))
        ids = [str(r["img_id"]) for r in rows]
        if len(ids) != expected_images or len(set(ids)) != expected_images: raise RuntimeError(f"{unit} {view} incomplete")
        path = raw_dir / f"{view}.pkl"
        with path.open("wb") as handle: pickle.dump(rows, handle, protocol=4)
        out.append({"unit": unit, "view": view, "images": len(ids), "image_set_sha256": set_sha(ids), "prediction_count": sum(len(r["pred_instances"]["scores"]) for r in rows), **inventory(path, "pickle", len(rows), len(set(ids)))})
    return out


def load_source_labels(unit, wanted_roles=("D_cal-fit", "D_cal-calib")):
    rows = []
    image_re = re.compile(r'"image_id":"([^"]+)"')
    flag_re = re.compile(r'"d_cal_daudit_split_flag":"([^"]+)"')
    skipped_audit = 0
    with (LABEL / unit / "matched_fullval.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            fm = flag_re.search(line)
            if not fm: raise RuntimeError(f"routing flag absent {unit}")
            if fm.group(1) == "D_audit":
                skipped_audit += 1; continue
            im = image_re.search(line)
            if not im: raise RuntimeError(f"routing image absent {unit}")
            image_id = im.group(1); role = "D_cal-" + split_role(image_id)
            if role not in wanted_roles: continue
            row = json.loads(line); gt = row["gt_obb"]
            w, h = float(gt["obb_w"]), float(gt["obb_h"])
            ar = max(w, h) / max(min(w, h), 1e-6)
            if ar < 2.1: continue
            risk = min(float(row["angle_error"]) / max(float(delta_theta_075(ar)), 1.0), 3.0)
            cluster = image_id.split("__", 1)[0] if UNITS[unit][1] == "SODA-A" else image_id
            rows.append({"image_id": image_id, "pred_id": int(row["pred_id"]), "role": role, "risk_value": risk, "cluster": cluster})
    return pd.DataFrame(rows), skipped_audit


def weights(frame):
    result = np.zeros(len(frame))
    datasets = sorted(frame.dataset.unique())
    for dataset in datasets:
        units = sorted(frame[frame.dataset == dataset].unit.unique())
        for unit in units:
            mask = (frame.dataset == dataset) & (frame.unit == unit)
            result[mask] = 1 / len(datasets) / len(units) / int(mask.sum())
    return result


def fit_models(frame):
    sample_weight = weights(frame)
    linear = make_pipeline(StandardScaler(), LinearRegression())
    linear.fit(frame[LINEAR], frame.risk_value, linearregression__sample_weight=sample_weight)
    hgb = HistGradientBoostingRegressor(max_iter=200, learning_rate=.05, max_leaf_nodes=15,
        l2_regularization=1., min_samples_leaf=50, random_state=20260807, monotonic_cst=MONOTONIC)
    hgb.fit(frame[FEATURES], frame.risk_value, sample_weight=sample_weight)
    return {"linear": linear, "eqs": hgb}, sample_weight


def score(frame, models):
    out = frame[["image_id", "pred_id"]].copy()
    out["linear_score"] = -models["linear"].predict(frame[LINEAR])
    out["eqs_rc_score"] = -models["eqs"].predict(frame[FEATURES])
    out["standalone_score"] = -(frame.u_axis + frame.missing_fraction + frame.iou_loss)
    return out


def nrc(score_values, risk): return float(nrc_auc(np.asarray(score_values), np.asarray(risk))["nrc_auc"])


def weighted_nrc(order, risks, multiplicity):
    active = multiplicity[order] > 0
    expanded = np.repeat(risks[order][active], multiplicity[order][active].astype(int))
    if len(expanded) < 2: return float("nan")
    model = float(np.mean(np.cumsum(expanded) / np.arange(1, len(expanded)+1)))
    oracle_r = np.sort(expanded, kind="stable")
    oracle = float(np.mean(np.cumsum(oracle_r) / np.arange(1, len(expanded)+1)))
    random = float(np.mean(expanded)); denom = random - oracle
    return (model - oracle) / denom if abs(denom) > 1e-12 else float("nan")


def _boot_worker(draw):
    values = []
    for frame in _BOOT["units"]:
        mult = np.bincount(draw, minlength=_BOOT["cluster_count"])[frame["cluster_pos"]]
        values.append(weighted_nrc(frame["linear_order"], frame["risk"], mult) - weighted_nrc(frame["eqs_order"], frame["risk"], mult))
    return float(np.mean(values))


def lodo_bootstrap(dataset, frames, clusters, seed):
    global _BOOT
    pos = {value: i for i, value in enumerate(clusters)}
    context = []
    for frame in frames:
        cp = frame.cluster.map(pos)
        if cp.isna().any(): raise RuntimeError(f"cluster mapping absent {dataset}")
        context.append({"cluster_pos": cp.to_numpy(int), "risk": frame.risk_value.to_numpy(float),
                        "linear_order": np.argsort(-frame.linear_score.to_numpy(float), kind="stable"),
                        "eqs_order": np.argsort(-frame.eqs_rc_score.to_numpy(float), kind="stable")})
    _BOOT = {"units": context, "cluster_count": len(clusters)}
    rng = np.random.RandomState(seed); draws = rng.randint(0, len(clusters), size=(10000, len(clusters)), dtype=np.int32)
    with mp.get_context("fork").Pool(38) as pool:
        values = np.asarray(pool.map(_boot_worker, list(draws), chunksize=8), dtype=float)
    if len(values) != 10000 or not np.isfinite(values).all(): raise RuntimeError(f"invalid LODO bootstrap {dataset}")
    return values


def source_phase():
    feature_inventory = []
    for unit, (_, _, _, raw_dir) in UNITS.items():
        identity = R014 / "raw/dior22/identity.pkl" if unit == "A" else (R014 / "raw/dior3/identity.pkl" if unit == "B" else (R014 / "raw/dior61/identity.pkl" if unit == "C" else (R014 / "raw/fair24/identity.pkl" if unit == "D" else (ROOT / "outputs/persistent_artifacts/orientbench_v2_047/tta_preds/SODA-A_23/identity.pkl" if unit == "E" else ROOT / "outputs/persistent_artifacts/orientbench_v2/SODA-A/4/raw/result_b4.pkl"))))
        paths = [identity, raw_dir / "hflip.pkl", raw_dir / "vflip.pkl"]
        feature_inventory.append(build_features(unit, paths, RUNPRE / "source_features" / f"{unit}.parquet"))
    cache = {}; taint = []; parts = []
    for unit, (_, dataset, detector, _) in UNITS.items():
        labels, skipped = load_source_labels(unit)
        features = pd.read_parquet(RUNPRE / "source_features" / f"{unit}.parquet")
        frame = features.merge(labels, on=["image_id", "pred_id"], validate="one_to_one")
        frame["unit"], frame["dataset"], frame["detector"] = unit, dataset, detector
        cache[unit] = frame; parts.append(frame)
        taint.append({"unit": unit, "D_audit_lines_routed_before_materialization": skipped, "D_audit_objects_materialized": 0, "status": "PASS"})
    lodo_rows = []; lodo_reps = []
    soda_map = pd.read_csv(R014 / "soda_tile_to_mother_r014.csv", dtype=str).set_index("tile_id").mother_scene_id.to_dict()
    for ordinal, held in enumerate(("DIOR-R", "FAIR1M-v1.0", "SODA-A")):
        training = pd.concat([f[f.role == "D_cal-fit"] for f in cache.values() if f.dataset.iloc[0] != held], ignore_index=True)
        models, _ = fit_models(training)
        val_units = []
        for unit, frame in cache.items():
            if frame.dataset.iloc[0] != held: continue
            val = frame[frame.role == "D_cal-calib"].copy(); scores = score(val, models)
            val = val.merge(scores, on=["image_id", "pred_id"]); val_units.append(val)
        # Complete held-out calibration cluster universe, including zero-eligible clusters.
        first_unit = next(u for u, meta in UNITS.items() if meta[1] == held)
        universe = pd.read_csv(LABEL / first_unit / "image_universe.csv", dtype={"image_id": str})
        cal_images = [img for img, flag in zip(universe.image_id.astype(str), universe.d_cal_daudit_split_flag.astype(str)) if flag != "D_audit" and split_role(img) == "calib"]
        clusters = sorted({soda_map[x] for x in cal_images} if held == "SODA-A" else set(cal_images))
        reps = lodo_bootstrap(held, val_units, clusters, 20260806 + ordinal)
        points = [nrc(v.linear_score, v.risk_value) - nrc(v.eqs_rc_score, v.risk_value) for v in val_units]
        point = float(np.mean(points)); se = float(np.std(reps, ddof=1))
        lodo_rows.append({"held_out_dataset": held, "train_datasets": "|".join(sorted(set(training.dataset))), "units": len(val_units), "rows": sum(len(v) for v in val_units), "clusters": len(clusters), "cluster_sha256": set_sha(clusters), "delta_nrc": point, "ci_low": float(np.percentile(reps,2.5)), "ci_high": float(np.percentile(reps,97.5)), "bootstrap_reps": 10000, "seed": 20260806+ordinal, "se": se, "gate_authority": False})
        lodo_reps.extend({"dataset": held, "replicate": i, "delta_nrc": value} for i, value in enumerate(reps))
    se_worst = max(row["se"] for row in lodo_rows)
    phi = lambda x: .5 * (1 + math.erf(x / math.sqrt(2)))
    power = {"se_worst": se_worst, "worst_fold": max(lodo_rows, key=lambda r:r["se"])["held_out_dataset"], "power_at_delta_0_02": phi(.02/se_worst - 1.6448536269514722), "MDE80": (1.6448536269514722+0.8416212335729143)*se_worst, "formula": "Phi(0.02/se_worst-1.6448536269514722); MDE80=(1.6448536269514722+0.8416212335729143)*se_worst", "target_data_used": False, "gate_authority": False}
    fit = pd.concat([f[f.role == "D_cal-fit"] for f in cache.values()], ignore_index=True)
    models, sample_weight = fit_models(fit)
    model_path = RUNPRE / "models/eqs_rc_and_linear.joblib"; model_path.parent.mkdir(parents=True, exist_ok=True); joblib.dump(models, model_path)
    source_sets=[]
    for (dataset, unit), group in fit.groupby(["dataset","unit"]):
        keys=[f"{r.image_id}:{r.pred_id}" for r in group.itertuples()]
        source_sets.append({"dataset":dataset,"unit":unit,"rows":len(group),"sorted_key_sha256":set_sha(keys),"weight_per_row":float(sample_weight[group.index[0]]) if group.index[0] < len(sample_weight) else "INDEX_REBASED_IN_GLOBAL_FRAME"})
    write_csv(PRE / "source_lodo_r019.csv", lodo_rows); write_csv(PRE / "source_lodo_replicates_r019.csv", lodo_reps)
    write_json(PRE / "blind_power_mde_r019.json", power); write_json(PRE / "source_taint_audit_r019.json", taint)
    write_json(PRE / "source_model_inventory_r019.json", {"features": feature_inventory, "source_sets": source_sets, "model": inventory(model_path,"joblib"), "environment": {"python":sys.version,"sklearn":__import__('sklearn').__version__,"numpy":np.__version__}, "feature_order":FEATURES,"monotonic":MONOTONIC})


def target_features_scores(registry):
    inventories=[]; models=joblib.load(RUNPRE / "models/eqs_rc_and_linear.joblib")
    for unit in ("orcnn", "rtmdet"):
        raw_dir=RUNPRE/"raw"/unit
        raw_inventory=merge_forward(unit, 5297)
        feature_path=RUNPRE/"target_features"/f"{unit}.parquet"
        feature=build_features(unit,[raw_dir/"identity.pkl",raw_dir/"hflip.pkl",raw_dir/"vflip.pkl"],feature_path)
        frame=pd.read_parquet(feature_path); scores=score(frame,models); scores.insert(2,"detection_score",frame.detection_score.to_numpy())
        score_path=RUNPRE/"target_scores"/f"{unit}.parquet"; score_path.parent.mkdir(parents=True,exist_ok=True); scores.to_parquet(score_path,index=False,compression="zstd")
        inventories.append({"unit":unit,"raw":raw_inventory,"features":feature,"scores":inventory(score_path,"parquet",len(scores),len(scores.drop_duplicates(['image_id','pred_id']))),"target_label_access_count":0})
    write_json(PRE/"dota_prediction_feature_score_inventory_r019.json",inventories)


def draws(registry):
    mothers=sorted({r["mother"] for r in registry["tiles"]}); rng=np.random.RandomState(20260809)
    values=rng.randint(0,len(mothers),size=(10000,len(mothers)),dtype=np.int32)
    path=RUNPRE/"draws/mother_draws.npy"; path.parent.mkdir(parents=True,exist_ok=True); np.save(path,values)
    write_json(PRE/"bootstrap_draw_inventory_r019.json",{"mothers":len(mothers),"mother_sha256":set_sha(mothers),"replicates":10000,"replicate_ids":"0..9999","seed":20260809,"draw":inventory(path,"npy",10000,10000),"same_multiplicity_all_units_scores":True})


def seal():
    files=[]
    for path in sorted(p for p in RUNPRE.rglob("*") if p.is_file() and "part" not in p.name):
        files.append(inventory(path))
    code=[]
    for path in sorted((WORK/"scripts").glob("*.py"))+sorted((WORK/"tests").glob("*.py"))+[WORK/"protocol_r019.json"]:
        code.append(inventory(path))
    tracked_prelabel=[]
    for path in sorted(p for p in PRE.rglob("*") if p.is_file() and p.name != "prelabel_seal_manifest_r019.json"):
        tracked_prelabel.append(inventory(path))
    payload={"schema":"r019_prelabel_seal_v1","generated_before_target_label_access":True,"target_label_access_count":0,"prelabel_commit_sha":"POST_COMMIT_RUNTIME_RECEIPT","runtime_files":files,"tracked_code":code,"tracked_prelabel":tracked_prelabel,"manifest_sha256_semantics":"canonical JSON payload without self hash"}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode(); payload["canonical_payload_sha256"]=hashlib.sha256(canonical).hexdigest()
    write_json(PRE/"prelabel_seal_manifest_r019.json",payload)
    for path in RUNPRE.rglob("*"):
        if path.is_file(): path.chmod(0o444)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("phase",choices=("preflight","source","target","draws","seal"));args=parser.parse_args()
    if args.phase=="preflight": print(json.dumps(preflight()))
    elif args.phase=="source": source_phase()
    elif args.phase=="target": target_features_scores(json.loads((RUNPRE/"image_only_registry.json").read_text()))
    elif args.phase=="draws": draws(json.loads((RUNPRE/"image_only_registry.json").read_text()))
    else: seal()


if __name__=="__main__": main()

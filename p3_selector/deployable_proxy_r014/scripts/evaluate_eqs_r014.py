#!/usr/bin/env python3
"""Frozen source-only EQS fitting, sealing, and one-shot target audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import pickle
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from derive_delta_theta_075 import load_interpolator
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import aurc, risk_at_coverage
from m069_common import split_role

RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r014"
REPORTS = ROOT / "p3_selector/deployable_proxy_r014/reports"
LABEL_ROOT = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
UNITS = {
    "A": ("DIOR-R/22", "DIOR-R", "rotated_retinanet_psc"),
    "B": ("DIOR-R/3", "DIOR-R", "oriented_rcnn"),
    "C": ("DIOR-R/61", "DIOR-R", "rotated_rtmdet_s"),
    "D": ("FAIR1M-v1.0/24", "FAIR1M-v1.0", "rotated_retinanet_psc"),
    "E": ("SODA-A/23", "SODA-A", "rotated_retinanet_psc"),
    "F": ("SODA-A/4", "SODA-A", "oriented_rcnn"),
}
DATASETS = ("DIOR-R", "FAIR1M-v1.0", "SODA-A")
FEATURES_LINEAR = ["logit_score", "log_pred_ar", "half_log_pred_area"]
FEATURES_EQS = FEATURES_LINEAR + [
    "support_fraction", "missing_fraction", "u_axis", "iou_loss",
    "center_dispersion", "width_dispersion", "height_dispersion",
    "score_dispersion", "association_margin",
]
MONOTONIC = [-1, 0, 0, -1, 1, 1, 1, 1, 1, 1, 1, 0]
SELECTORS = ["detection_score", "score_ar_size_linear", "nonlinear_geometry", "standalone_equivariance", "EQS"]
_DTH = load_interpolator()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_features(unit: str) -> pd.DataFrame:
    path = RUNTIME / f"features/{unit}.parquet"
    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_parquet(path)
    forbidden = {"gt", "angle_error", "risk", "aspect_ratio", "d_cal_daudit_split_flag"}
    if forbidden & set(frame.columns):
        raise RuntimeError(f"GT field leaked into feature schema for {unit}")
    return frame


def load_labels(unit: str) -> pd.DataFrame:
    rows = []
    path = LABEL_ROOT / unit / "matched_fullval.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            gt = row.get("gt_obb", {})
            width, height = float(gt.get("obb_w", 0)), float(gt.get("obb_h", 0))
            if min(width, height) <= 0:
                continue
            ar = max(width, height) / min(width, height)
            if ar < 2.1:
                continue
            angle = float(row["angle_error"])
            risk = min(angle / max(float(_DTH(ar)), 1.0), 3.0)
            image_id = str(row["image_id"])
            split = str(row.get("d_cal_daudit_split_flag", row.get("split", "")))
            role = "D_audit" if split == "D_audit" else f"D_cal-{split_role(image_id)}"
            cluster = image_id.split("__", 1)[0] if UNITS[unit][1] == "SODA-A" else image_id
            rows.append({
                "image_id": image_id, "pred_id": int(row["pred_id"]), "role": role,
                "risk": risk, "angle_error": angle, "gt_ar": ar, "cluster": cluster,
            })
    frame = pd.DataFrame(rows)
    if frame.duplicated(["image_id", "pred_id"]).any():
        raise RuntimeError(f"duplicate label keys in {unit}")
    return frame


def eligible(unit: str) -> pd.DataFrame:
    return load_features(unit).merge(load_labels(unit), on=["image_id", "pred_id"], how="inner", validate="one_to_one")


def training_weights(frame: pd.DataFrame) -> np.ndarray:
    weights = np.zeros(len(frame), dtype=float)
    for dataset, dataset_rows in frame.groupby("dataset"):
        units = sorted(dataset_rows["unit"].unique())
        for unit in units:
            mask = (frame["dataset"] == dataset) & (frame["unit"] == unit)
            weights[mask] = 1.0 / len(frame["dataset"].unique()) / len(units) / int(mask.sum())
    return weights


def fit_models(frame: pd.DataFrame) -> dict:
    weights = training_weights(frame)
    linear = make_pipeline(StandardScaler(), LinearRegression())
    linear.fit(frame[FEATURES_LINEAR], frame["risk"], linearregression__sample_weight=weights)
    geometry = HistGradientBoostingRegressor(
        max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
        l2_regularization=1.0, min_samples_leaf=50, random_state=20260807,
    ).fit(frame[FEATURES_LINEAR], frame["risk"], sample_weight=weights)
    eqs = HistGradientBoostingRegressor(
        max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
        l2_regularization=1.0, min_samples_leaf=50, random_state=20260807,
        monotonic_cst=MONOTONIC,
    ).fit(frame[FEATURES_EQS], frame["risk"], sample_weight=weights)
    return {"linear": linear, "geometry": geometry, "eqs": eqs}


def score_frame(frame: pd.DataFrame, models: dict) -> pd.DataFrame:
    out = frame[["image_id", "pred_id"]].copy()
    out["detection_score"] = frame["detection_score"].to_numpy()
    out["score_ar_size_linear"] = -models["linear"].predict(frame[FEATURES_LINEAR])
    out["nonlinear_geometry"] = -models["geometry"].predict(frame[FEATURES_LINEAR])
    out["standalone_equivariance"] = -(frame["u_axis"] + frame["missing_fraction"] + frame["iou_loss"])
    out["EQS"] = -models["eqs"].predict(frame[FEATURES_EQS])
    return out


def nrc(score: np.ndarray, risk: np.ndarray) -> float:
    return float(nrc_auc(score, risk)["nrc_auc"])


def cluster_bootstrap_delta(frame: pd.DataFrame, linear: np.ndarray, eqs: np.ndarray,
                            seed: int, reps: int = 1000) -> np.ndarray:
    clusters = frame["cluster"].astype(str).to_numpy()
    unique = np.unique(clusters)
    groups = {value: np.where(clusters == value)[0] for value in unique}
    risks = frame["risk"].to_numpy()
    seeds = np.random.RandomState(seed).randint(0, np.iinfo(np.int32).max, size=reps)

    def one(rep_seed: int) -> float:
        rng = np.random.RandomState(int(rep_seed))
        selected = rng.choice(unique, len(unique), replace=True)
        indices = np.concatenate([groups[value] for value in selected])
        return nrc(linear[indices], risks[indices]) - nrc(eqs[indices], risks[indices])

    workers = min(38, reps)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        values = np.asarray(list(pool.map(one, seeds)), dtype=float)
    if len(values) != reps or not np.all(np.isfinite(values)):
        raise RuntimeError("invalid bootstrap replicate count")
    return values


def source_data(dataset: str, role: str) -> pd.DataFrame:
    parts = []
    for unit, (_, ds, _) in UNITS.items():
        if ds != dataset:
            continue
        frame = eligible(unit)
        frame = frame[frame["role"] == role].copy()
        frame["unit"], frame["dataset"] = unit, ds
        parts.append(frame)
    return pd.concat(parts, ignore_index=True)


def source_phase() -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    model_dir = RUNTIME / "models"
    score_dir = RUNTIME / "scores"
    for path in (model_dir, score_dir):
        path.mkdir(parents=True, exist_ok=True)
    rows = []
    cache = {}
    for target, (_, target_dataset, _) in UNITS.items():
        sources = [dataset for dataset in DATASETS if dataset != target_dataset]
        for ordinal, (train_dataset, validation_dataset) in enumerate((sources, sources[::-1])):
            train = cache.setdefault((train_dataset, "D_cal-fit"), source_data(train_dataset, "D_cal-fit"))
            validation = cache.setdefault((validation_dataset, "D_cal-calib"), source_data(validation_dataset, "D_cal-calib"))
            models = fit_models(train)
            scores = score_frame(validation, models)
            point = nrc(scores["score_ar_size_linear"].to_numpy(), validation["risk"].to_numpy()) - nrc(scores["EQS"].to_numpy(), validation["risk"].to_numpy())
            boot = cluster_bootstrap_delta(validation, scores["score_ar_size_linear"].to_numpy(), scores["EQS"].to_numpy(), 20260807 + 100 * list(UNITS).index(target) + ordinal)
            rows.append({
                "outer_target": UNITS[target][0], "outer_target_dataset": target_dataset,
                "train_source_dataset": train_dataset, "validation_source_dataset": validation_dataset,
                "train_rows": len(train), "validation_rows": len(validation),
                "delta_nrc": point, "ci_low": np.percentile(boot, 2.5), "ci_high": np.percentile(boot, 97.5),
                "bootstrap_reps": 1000, "status": "CI_UPPER_LT_ZERO" if np.percentile(boot, 97.5) < 0 else "NO_EARLY_STOP",
            })
        fit_parts = []
        for dataset in sources:
            part = cache.setdefault((dataset, "D_cal-fit"), source_data(dataset, "D_cal-fit")).copy()
            fit_parts.append(part)
        fit = pd.concat(fit_parts, ignore_index=True)
        models = fit_models(fit)
        joblib.dump(models, model_dir / f"{target}.joblib")
        target_features = load_features(target)
        target_scores = score_frame(target_features, models)
        target_scores.to_parquet(score_dir / f"{target}.parquet", compression="zstd", index=False)
    write_csv(REPORTS / "source_cv_r014.csv", rows)
    stopped = []
    for target in UNITS:
        selected = [row for row in rows if row["outer_target"] == UNITS[target][0]]
        if len(selected) == 2 and all(row["status"] == "CI_UPPER_LT_ZERO" for row in selected):
            stopped.append(UNITS[target][0])
    seals = []
    for path in sorted((RUNTIME / "features").glob("*.parquet")) + sorted(model_dir.glob("*.joblib")) + sorted(score_dir.glob("*.parquet")):
        seals.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    seal = {"schema": "r014_prelabel_seal_v1", "source_early_stop_targets": stopped, "files": seals}
    (RUNTIME / "prelabel_seal.json").write_text(json.dumps(seal, indent=2) + "\n")
    return seal


def holm(rows: list[dict], pfield: str, outfield: str) -> None:
    order = sorted(range(len(rows)), key=lambda index: rows[index][pfield])
    running = 0.0
    total = len(rows)
    for rank, index in enumerate(order):
        adjusted = min(1.0, (total - rank) * rows[index][pfield])
        running = max(running, adjusted)
        rows[index][outfield] = running


def target_phase() -> dict:
    seal_path = RUNTIME / "prelabel_seal.json"
    if not seal_path.is_file():
        raise RuntimeError("prelabel seal is absent")
    seal = json.loads(seal_path.read_text())
    for entry in seal["files"]:
        path = ROOT / entry["path"]
        if sha256(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise RuntimeError(f"prelabel seal changed: {path}")
    if seal["source_early_stop_targets"]:
        return {"status": "EARLY_STOP_SOURCE_R014", "targets": seal["source_early_stop_targets"]}
    all_boot = {}
    unit_rows = []
    long_boot = []
    unit_frames = {}
    for ordinal, unit in enumerate(UNITS):
        labels = load_labels(unit)
        labels = labels[labels["role"] == "D_audit"]
        scores = pd.read_parquet(RUNTIME / f"scores/{unit}.parquet")
        frame = labels.merge(scores, on=["image_id", "pred_id"], validate="one_to_one")
        unit_frames[unit] = frame
        point = nrc(frame["score_ar_size_linear"].to_numpy(), frame["risk"].to_numpy()) - nrc(frame["EQS"].to_numpy(), frame["risk"].to_numpy())
        boot = cluster_bootstrap_delta(frame, frame["score_ar_size_linear"].to_numpy(), frame["EQS"].to_numpy(), 20260807 + ordinal)
        all_boot[unit] = boot
        pvalue = (1 + int(np.sum((boot - point) >= point))) / (len(boot) + 1)
        metrics = {}
        for selector in SELECTORS:
            score = frame[selector].to_numpy(); risk = frame["risk"].to_numpy()
            metrics[f"nrc_{selector}"] = nrc(score, risk)
            metrics[f"aurc_{selector}"] = float(aurc(score, risk))
            metrics[f"risk70_{selector}"] = float(risk_at_coverage(score, risk, 0.70))
            metrics[f"risk90_{selector}"] = float(risk_at_coverage(score, risk, 0.90))
        unit_rows.append({
            "unit": UNITS[unit][0], "unit_key": unit, "dataset": UNITS[unit][1], "detector": UNITS[unit][2],
            "audit_rows": len(frame), "audit_clusters": frame["cluster"].nunique(), "delta_nrc": point,
            "ci_low": np.percentile(boot, 2.5), "ci_high": np.percentile(boot, 97.5),
            "p_centered_one_sided": pvalue, "bootstrap_reps": 1000, **metrics,
        })
        for rep, value in enumerate(boot):
            long_boot.append({"level": "unit", "key": UNITS[unit][0], "replicate": rep, "delta_nrc": value})
    holm(unit_rows, "p_centered_one_sided", "holm6_p")
    for row in unit_rows:
        row["supported"] = bool(row["delta_nrc"] >= 0.02 and row["ci_low"] > 0 and row["holm6_p"] < 0.05)
    dataset_rows = []
    for dataset in DATASETS:
        keys = [unit for unit in UNITS if UNITS[unit][1] == dataset]
        points = [next(row["delta_nrc"] for row in unit_rows if row["unit_key"] == unit) for unit in keys]
        boot = np.mean(np.column_stack([all_boot[unit] for unit in keys]), axis=1)
        point = float(np.mean(points))
        pvalue = (1 + int(np.sum((boot - point) >= point))) / (len(boot) + 1)
        dataset_rows.append({
            "dataset": dataset, "units": "|".join(UNITS[unit][0] for unit in keys),
            "delta_nrc": point, "ci_low": np.percentile(boot, 2.5), "ci_high": np.percentile(boot, 97.5),
            "p_centered_one_sided": pvalue, "bootstrap_reps": 1000,
        })
        for rep, value in enumerate(boot):
            long_boot.append({"level": "dataset", "key": dataset, "replicate": rep, "delta_nrc": value})
    holm(dataset_rows, "p_centered_one_sided", "holm3_p")
    for row in dataset_rows:
        row["supported"] = bool(row["delta_nrc"] >= 0.02 and row["ci_low"] > 0 and row["holm3_p"] < 0.05)
    write_csv(REPORTS / "unit_results_r014.csv", unit_rows)
    write_csv(REPORTS / "dataset_results_r014.csv", dataset_rows)
    write_csv(REPORTS / "bootstrap_replicates_r014.csv", long_boot)
    supported = [row for row in unit_rows if row["supported"]]
    dataset_supported = [row for row in dataset_rows if row["supported"]]
    pass_gate = (
        len(supported) >= 4
        and len({row["dataset"] for row in supported}) == 3
        and len({row["detector"] for row in supported}) >= 2
        and any(row["unit_key"] == "D" for row in supported)
        and len(dataset_supported) == 3
    )
    if pass_gate:
        status = "PASS_DEPLOYABLE_EQS_R014"
    elif len(supported) >= 2 and not any(row["ci_high"] < 0 for row in dataset_rows):
        status = "INCONCLUSIVE_DEPLOYABLE_EQS_R014"
    else:
        status = "FAIL_DEPLOYABLE_EQS_R014"
    return {"status": status, "unit_support": len(supported), "dataset_support": len(dataset_supported)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("source", "target", "all"))
    args = parser.parse_args()
    source = source_phase() if args.phase in ("source", "all") else None
    target = target_phase() if args.phase in ("target", "all") else None
    print(json.dumps({"source": source, "target": target}, ensure_ascii=False))


if __name__ == "__main__":
    main()

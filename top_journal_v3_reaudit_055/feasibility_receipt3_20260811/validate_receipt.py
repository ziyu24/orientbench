#!/usr/bin/env python3
"""Independent receipt3 validator.

This entry point does not import the generator or either sealed metric module.
It rebuilds the fixed cohort and metrics from the pre-existing sealed inputs,
replays every bootstrap replicate, derives Track D facts from raw evidence,
and derives the joint gate from those independently reconstructed facts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import multiprocessing as mp
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

os.environ.update({
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
})

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811"
SOURCE = ROOT / "outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809"
R014 = ROOT / "outputs/persistent_artifacts/orientbench_r014"
LABEL = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
R014_REPORTS = ROOT / "p3_selector/deployable_proxy_r014/reports"
PTH_README = Path("/home/rspip/cqc/pro/study/pth_data/readme.md")
CURVE_JSON = ROOT / "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json"
UNITS = {
    "A": ("DIOR-R", "DIOR-R/22"),
    "B": ("DIOR-R", "DIOR-R/3"),
    "C": ("DIOR-R", "DIOR-R/61"),
    "D": ("FAIR1M", "FAIR1M-v1.0/24"),
    "E": ("SODA-A", "SODA-A/23"),
    "F": ("SODA-A", "SODA-A/4"),
}
SCORES = {
    "raw_confidence": "detection_score",
    "linear_source_frozen": "score_ar_size_linear",
    "tta_angle": "tta_angle",
    "tta_localization": "tta_localization",
    "S0": "S0",
    "learned_EQS": "EQS",
}
BASELINES = ["raw_confidence", "linear_source_frozen", "tta_angle", "tta_localization"]
BOOT_COLUMNS = [
    f"{dataset}__S0_minus_{baseline}"
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A")
    for baseline in BASELINES
]
_BOOT = None


class ValidationFailure(RuntimeError):
    pass


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sequence_sha(values) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def close_float(actual: Any, expected: Any, label: str, atol: float = 1e-12) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=atol):
        raise ValidationFailure(f"{label}: float mismatch actual={actual} expected={expected}")


def delta_theta_075_independent(aspect_ratio: float) -> float:
    """Independent transcription of the frozen JSON interpolation policy."""
    frozen = delta_theta_075_independent.frozen
    ar = float(aspect_ratio)
    if not math.isfinite(ar) or ar < 1.0:
        raise ValidationFailure(f"invalid aspect ratio {ar}")
    grid = frozen["ar"]
    values = frozen["dtheta"]
    if ar < grid[0]:
        return float("inf")
    if ar <= grid[-1]:
        return float(np.interp(ar, grid, values))
    return max(0.0, frozen["tail_constant"] / ar - 2.0e-3)


_curve = json.loads(CURVE_JSON.read_text())
_ars = np.asarray(_curve["ar"], dtype=np.float64)
_dtheta = np.asarray(_curve["dtheta_075"], dtype=np.float64)
_tail = _ars >= max(8.0, float(_ars[-1]) / 2.0)
delta_theta_075_independent.frozen = {
    "ar": _ars,
    "dtheta": _dtheta,
    "tail_constant": float(np.min(_ars[_tail] * _dtheta[_tail])),
}


def inventory_precheck(base: Path) -> list[dict]:
    path = base / "track_m_source_inventory.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    failures = []
    for row in rows:
        actual = ROOT / row["path"]
        if not actual.is_file():
            failures.append({"path": row["path"], "reason": "missing"})
            continue
        actual_bytes = actual.stat().st_size
        actual_sha = sha256_path(actual)
        if actual_bytes != int(row["bytes"]) or actual_sha != row["sha256"]:
            failures.append({
                "path": row["path"],
                "reason": "source_hash",
                "expected_bytes": row["bytes"],
                "actual_bytes": actual_bytes,
                "expected_sha256": row["sha256"],
                "actual_sha256": actual_sha,
            })
    if failures:
        raise ValidationFailure(f"source_hash mutation or source identity failure: {failures[:3]}")
    return rows


def bootstrap_saved_fast_precheck(base: Path) -> None:
    generated = pd.read_csv(base / "track_m_bootstrap_replicates.csv")
    source = pd.read_csv(SOURCE / "track_m_bootstrap.csv")
    if len(generated) != 10000 or generated.replicate.tolist() != list(range(10000)):
        raise ValidationFailure("bootstrap_replicate sequence/count failure")
    if source.replicate.tolist() != list(range(10000)):
        raise ValidationFailure("source bootstrap replicate sequence/count failure")
    for column in BOOT_COLUMNS:
        actual = generated[f"actual__{column}"].to_numpy(np.float64)
        recorded_source = generated[f"source__{column}"].to_numpy(np.float64)
        source_value = source[column].to_numpy(np.float64)
        if not np.allclose(actual, source_value, atol=1e-12, rtol=0):
            idx = int(np.flatnonzero(~np.isclose(actual, source_value, atol=1e-12, rtol=0))[0])
            raise ValidationFailure(f"bootstrap_replicate mutation: replicate={idx} field=actual__{column}")
        if not np.allclose(recorded_source, source_value, atol=1e-12, rtol=0):
            raise ValidationFailure(f"bootstrap source field mismatch: {column}")
        recorded_error = generated[f"abs_error__{column}"].to_numpy(np.float64)
        if not np.isfinite(recorded_error).all() or np.any(recorded_error > 1e-12):
            raise ValidationFailure(f"bootstrap abs-error tolerance failure: {column}")
    for field in ("worker_pid", "worker_cpu_seconds", "worker_maxrss_kb", "worker_affinity_count"):
        recorded = generated[f"source_{field}"].to_numpy()
        expected = source[field].to_numpy()
        same = np.allclose(recorded, expected, atol=1e-12, rtol=0) if field == "worker_cpu_seconds" else np.array_equal(recorded, expected)
        if not same:
            raise ValidationFailure(f"source bootstrap telemetry mismatch: {field}")


def manifest_entry(tree: Any, relpath: str):
    if isinstance(tree, dict):
        if tree.get("path") == relpath:
            return tree
        for value in tree.values():
            found = manifest_entry(value, relpath)
            if found is not None:
                return found
    elif isinstance(tree, list):
        for value in tree:
            found = manifest_entry(value, relpath)
            if found is not None:
                return found
    return None


def label_frame(unit: str) -> pd.DataFrame:
    rows = []
    with (LABEL / unit / "matched_fullval.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            box = record["gt_obb"]
            width = float(box["obb_w"])
            height = float(box["obb_h"])
            aspect_ratio = max(width, height) / max(min(width, height), 1e-6)
            if aspect_ratio < 2.1:
                continue
            threshold = max(delta_theta_075_independent(aspect_ratio), 1.0)
            risk = min(3.0, max(0.0, float(record["angle_error"]) / threshold))
            rows.append((str(record["image_id"]), int(record["pred_id"]), risk))
    frame = pd.DataFrame(rows, columns=["image_id", "pred_id", "risk_cap3"])
    if frame.duplicated(["image_id", "pred_id"]).any():
        raise ValidationFailure(f"duplicate eligible label keys: {unit}")
    return frame


def load_raw_frames(base: Path, inventory: list[dict]):
    r014_manifest = json.loads((R014_REPORTS / "evidence_manifest_r014.json").read_text())
    soda_map = pd.read_csv(R014 / "soda_tile_to_mother_r014.csv", dtype=str).set_index("tile_id").mother_scene_id.to_dict()
    frames = {}
    cluster_rows = []
    for unit, (dataset, _) in UNITS.items():
        feature_path = R014 / f"features/{unit}.parquet"
        score_path = R014 / f"scores/{unit}.parquet"
        matched_path = LABEL / unit / "matched_fullval.jsonl"
        universe_path = LABEL / unit / "image_universe.csv"
        m069 = json.loads((LABEL / unit / "manifest.json").read_text())
        for source_path in (feature_path, score_path):
            rel = str(source_path.relative_to(ROOT))
            entry = manifest_entry(r014_manifest, rel)
            if entry is None or entry.get("sha256") != sha256_path(source_path) or int(entry.get("bytes")) != source_path.stat().st_size:
                raise ValidationFailure(f"sealed r014 manifest mismatch: {rel}")
        if m069.get("matched_sha256") != sha256_path(matched_path) or int(m069.get("matched_bytes")) != matched_path.stat().st_size:
            raise ValidationFailure(f"sealed m069 matched manifest mismatch: {unit}")
        if m069.get("universe_sha256") != sha256_path(universe_path) or int(m069.get("universe_bytes")) != universe_path.stat().st_size:
            raise ValidationFailure(f"sealed m069 universe manifest mismatch: {unit}")

        features = pd.read_parquet(feature_path, columns=["image_id", "pred_id", "detection_score", "u_axis", "missing_fraction", "iou_loss"])
        scores = pd.read_parquet(score_path, columns=["image_id", "pred_id", "detection_score", "score_ar_size_linear", "EQS"])
        features["image_id"] = features.image_id.astype(str)
        scores["image_id"] = scores.image_id.astype(str)
        if features.duplicated(["image_id", "pred_id"]).any() or scores.duplicated(["image_id", "pred_id"]).any():
            raise ValidationFailure(f"duplicate fixed-score keys: {unit}")
        labels = label_frame(unit)
        eligible = set(zip(labels.image_id, labels.pred_id))
        mask = pd.MultiIndex.from_frame(features[["image_id", "pred_id"]]).isin(pd.MultiIndex.from_tuples(eligible))
        ordered = features.loc[mask].copy()
        ordered_keys = list(zip(ordered.image_id, ordered.pred_id))
        if len(ordered_keys) != len(labels) or set(ordered_keys) != eligible:
            raise ValidationFailure(f"incomplete eligible cohort: {unit}")
        joined = ordered.merge(scores, on=["image_id", "pred_id"], how="left", validate="one_to_one", suffixes=("", "_score"), sort=False)
        joined = joined.merge(labels, on=["image_id", "pred_id"], how="left", validate="one_to_one", sort=False)
        if not np.array_equal(joined.detection_score.to_numpy(), joined.detection_score_score.to_numpy()):
            raise ValidationFailure(f"detection-score join mismatch: {unit}")
        joined.drop(columns=["detection_score_score"], inplace=True)
        joined["tta_angle"] = -joined.u_axis
        joined["tta_localization"] = -(joined.missing_fraction + joined.iou_loss)
        joined["S0"] = -(joined.u_axis + joined.missing_fraction + joined.iou_loss)
        joined["residual"] = joined.risk_cap3 / 3.0
        joined["cluster"] = joined.image_id.map(soda_map) if dataset == "SODA-A" else joined.image_id.astype(str)
        required = ["risk_cap3", "residual", "cluster", *SCORES.values()]
        if joined[required].isna().any().any() or not np.isfinite(joined[["risk_cap3", "residual", *SCORES.values()]].to_numpy(np.float64)).all():
            raise ValidationFailure(f"missing/nonfinite fixed cohort value: {unit}")
        keep = ["image_id", "pred_id", "cluster", "risk_cap3", "residual", *SCORES.values()]
        joined = joined[keep].copy()
        derived = pd.read_parquet(base / f"track_m_rows/{unit}.parquet")
        if list(derived.columns) != keep or len(derived) != len(joined):
            raise ValidationFailure(f"derived rows schema/count mismatch: {unit}")
        for column in ("image_id", "pred_id", "cluster"):
            if not derived[column].astype(str).equals(joined[column].astype(str)):
                raise ValidationFailure(f"derived rows key/order mismatch: {unit}/{column}")
        if not np.array_equal(derived.drop(columns=["image_id", "pred_id", "cluster"]).to_numpy(np.float64), joined.drop(columns=["image_id", "pred_id", "cluster"]).to_numpy(np.float64)):
            raise ValidationFailure(f"derived rows value mismatch: {unit}")
        universe = pd.read_csv(universe_path, dtype=str).image_id.astype(str).tolist()
        clusters = sorted({soda_map[value] for value in universe} if dataset == "SODA-A" else set(universe))
        cluster_rows.extend({"unit": unit, "dataset": dataset, "cluster": str(cluster), "eligible_rows": int((joined.cluster.astype(str) == str(cluster)).sum())} for cluster in clusters)
        frames[unit] = joined
    published_clusters = pd.read_csv(base / "track_m_cluster_universe.csv", dtype=str).fillna("")
    expected_clusters = pd.DataFrame(cluster_rows).astype(str)
    if list(published_clusters.columns) != list(expected_clusters.columns) or not published_clusters.equals(expected_clusters):
        raise ValidationFailure("cluster universe or zero-eligible membership mismatch")
    return frames, cluster_rows


def independent_metric(score: np.ndarray, residual: np.ndarray):
    score = np.asarray(score, dtype=np.float64)
    residual = np.asarray(residual, dtype=np.float64)
    if score.ndim != 1 or score.shape != residual.shape or len(score) == 0 or not np.isfinite(score).all() or not np.isfinite(residual).all():
        raise ValidationFailure("metric input precondition failure")
    order = np.argsort(-score, kind="stable")
    sorted_score = score[order]
    sorted_residual = residual[order]
    starts = np.r_[0, np.flatnonzero(sorted_score[1:] != sorted_score[:-1]) + 1]
    counts = np.diff(np.r_[starts, len(score)])
    sums = np.add.reduceat(sorted_residual, starts)
    cumulative_count = np.cumsum(counts)
    cumulative_sum = np.cumsum(sums)
    coverage = cumulative_count / len(score)
    generalized = cumulative_sum / len(score)
    selective = cumulative_sum / cumulative_count
    augrc = float(np.trapz(np.r_[0.0, generalized], np.r_[0.0, coverage]))
    model = float(np.mean(np.cumsum(sorted_residual) / np.arange(1, len(score) + 1)))
    oracle_residual = np.sort(residual, kind="stable")
    oracle = float(np.mean(np.cumsum(oracle_residual) / np.arange(1, len(score) + 1)))
    random = float(np.mean(residual))
    denominator = random - oracle
    if abs(denominator) < 1e-12:
        raise ValidationFailure("complete metric input has degenerate NRC denominator")
    nrc = float((model - oracle) / denominator)
    fixed = {}
    for target in (0.70, 0.90):
        index = int(np.searchsorted(coverage, target, side="left"))
        fixed[int(target * 100)] = (float(selective[index]), float(coverage[index]))
    return {
        "AUGRC": augrc,
        "AURC": model,
        "AURC_oracle": oracle,
        "AURC_random": random,
        "NRC": nrc,
        "Risk@70": fixed[70][0],
        "actual_coverage@70": fixed[70][1],
        "Risk@90": fixed[90][0],
        "actual_coverage@90": fixed[90][1],
        "nonempty_coverage": float(coverage[-1]),
    }, coverage, generalized, selective


def recompute_metrics_and_curves(base: Path, frames: dict[str, pd.DataFrame]) -> list[dict]:
    published = pd.read_csv(base / "track_m_metrics.csv")
    computed = []
    curve_count = 0
    with (base / "track_m_risk_coverage.csv").open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for unit, frame in frames.items():
            dataset = UNITS[unit][0]
            residual = frame.residual.to_numpy(np.float64)
            for score_name, column in SCORES.items():
                metric, coverage, generalized, selective = independent_metric(frame[column].to_numpy(np.float64), residual)
                expected_curve = [(0, 0.0, 0.0, "", "True")]
                expected_curve.extend((index, cov, gen, sel, "False") for index, (cov, gen, sel) in enumerate(zip(coverage, generalized, selective), 1))
                for index, cov, gen, sel, origin in expected_curve:
                    try:
                        row = next(reader)
                    except StopIteration as exc:
                        raise ValidationFailure(f"risk-coverage curve truncated at {unit}/{score_name}/{index}") from exc
                    if row["dataset"] != dataset or row["unit"] != unit or row["score"] != score_name or int(row["curve_index"]) != index or row["origin"] != origin:
                        raise ValidationFailure(f"risk-coverage curve identity/order mismatch: {unit}/{score_name}/{index}")
                    close_float(row["coverage"], cov, f"curve coverage {unit}/{score_name}/{index}")
                    close_float(row["generalized_risk"], gen, f"curve generalized {unit}/{score_name}/{index}")
                    if index and not math.isclose(float(row["selective_risk"]), float(sel), rel_tol=0, abs_tol=1e-12):
                        raise ValidationFailure(f"curve selective mismatch: {unit}/{score_name}/{index}")
                    if not index and row["selective_risk"] != "":
                        raise ValidationFailure(f"curve origin selective risk must be empty: {unit}/{score_name}")
                    curve_count += 1
                result = {"level": "unit", "dataset": dataset, "unit": unit, "score": score_name, "rows": len(frame), **metric}
                computed.append(result)
        if next(reader, None) is not None:
            raise ValidationFailure("risk-coverage curve has extra rows")
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A"):
        units = [unit for unit, value in UNITS.items() if value[0] == dataset]
        for score_name in SCORES:
            parts = [row for row in computed if row["unit"] in units and row["score"] == score_name]
            computed.append({
                "level": "dataset_aggregate", "dataset": dataset, "unit": "equal-unit mean", "score": score_name,
                "rows": sum(row["rows"] for row in parts),
                **{key: float(np.mean([row[key] for row in parts])) for key in ("AUGRC", "AURC", "AURC_oracle", "AURC_random", "NRC", "Risk@70", "actual_coverage@70", "Risk@90", "actual_coverage@90", "nonempty_coverage")},
            })
    if len(published) != len(computed):
        raise ValidationFailure("point metric row count mismatch")
    for actual in computed:
        match = published[(published.level == actual["level"]) & (published.dataset == actual["dataset"]) & (published.unit == actual["unit"]) & (published.score == actual["score"])]
        if len(match) != 1:
            raise ValidationFailure(f"point metric identity mismatch: {actual['level']}/{actual['unit']}/{actual['score']}")
        expected = match.iloc[0]
        if int(expected.rows) != int(actual["rows"]) or int(expected.n_dropped) != 0 or not as_bool(expected.implementation_A_B_atol_1e_12_pass):
            raise ValidationFailure(f"point metric cohort/drop assertion mismatch: {actual['unit']}/{actual['score']}")
        for metric in ("AUGRC", "AURC", "AURC_oracle", "AURC_random", "NRC", "Risk@70", "actual_coverage@70", "Risk@90", "actual_coverage@90", "nonempty_coverage"):
            close_float(actual[metric], expected[metric], f"point metric {actual['unit']}/{actual['score']}/{metric}")
    if curve_count != 3313581:
        raise ValidationFailure(f"unexpected full curve row count: {curve_count}")
    return computed


def production_state(metrics: list[dict], asset_complete: bool = True, sensitivity_reversal: bool = False):
    if not asset_complete:
        return "INSUFFICIENT_ASSETS", ["required sealed asset or replicate evidence missing"]
    aggregate = {(row["dataset"], row["score"]): row for row in metrics if row["level"] == "dataset_aggregate"}
    reversal = []
    dominated = []
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A"):
        s0 = aggregate[(dataset, "S0")]
        for baseline in BASELINES:
            other = aggregate[(dataset, baseline)]
            delta = {metric: s0[metric] - other[metric] for metric in ("NRC", "AURC", "AUGRC", "Risk@70", "Risk@90")}
            if (delta["NRC"] < 0 or delta["AURC"] < 0) and (delta["AUGRC"] > 0 or delta["Risk@70"] > 0 or delta["Risk@90"] > 0):
                reversal.append({"dataset": dataset, "baseline": baseline, **delta})
            if delta["AUGRC"] > 0:
                dominated.append({"dataset": dataset, "baseline": baseline, "delta_AUGRC": delta["AUGRC"]})
    if reversal:
        return "METRIC_REVERSAL", reversal
    if dominated:
        return "BASELINE_DOMINATED", dominated
    if sensitivity_reversal:
        return "SENSITIVITY_UNSTABLE", ["pre-registered sensitivity reversal"]
    robust = all(aggregate[(dataset, "S0")]["AUGRC"] < aggregate[(dataset, baseline)]["AUGRC"] for dataset in ("DIOR-R", "FAIR1M", "SODA-A") for baseline in BASELINES)
    risk_never_reverses = all(aggregate[(dataset, "S0")][metric] <= aggregate[(dataset, baseline)][metric] for dataset in ("DIOR-R", "FAIR1M", "SODA-A") for baseline in BASELINES for metric in ("Risk@70", "Risk@90", "AURC", "NRC"))
    if robust and risk_never_reverses:
        return "ROBUST_CANDIDATE", ["all strict AUGRC and non-reversal predicates pass"]
    raise ValidationFailure("complete metrics do not map uniquely to the five frozen states")


def verify_state_fixtures(base: Path) -> None:
    fixtures = pd.read_csv(base / "track_m_state_fixtures.csv")
    required = {"INSUFFICIENT_ASSETS", "METRIC_REVERSAL", "BASELINE_DOMINATED", "SENSITIVITY_UNSTABLE", "ROBUST_CANDIDATE"}
    if set(fixtures.fixture) != required or set(fixtures.expected) != required or set(fixtures.actual) != required or not fixtures["pass"].map(as_bool).all():
        raise ValidationFailure("five-state fixture coverage/uniqueness failure")


def boot_context(frames: dict[str, pd.DataFrame], cluster_rows: list[dict]):
    context = {}
    for unit, frame in frames.items():
        universe = [row["cluster"] for row in cluster_rows if row["unit"] == unit]
        positions = {cluster: index for index, cluster in enumerate(universe)}
        values = {
            "residual": frame.residual.to_numpy(np.float64),
            "cluster_position": frame.cluster.astype(str).map(positions).to_numpy(np.int64),
            "cluster_count": len(universe),
            "scores": {name: frame[column].to_numpy(np.float64) for name, column in SCORES.items() if name != "learned_EQS"},
        }
        values["orders"] = {name: np.argsort(-score, kind="stable") for name, score in values["scores"].items()}
        context[unit] = values
    return context


def weighted_aug(context: dict, score_name: str, multiplicities: np.ndarray) -> float:
    order = context["orders"][score_name]
    weights = multiplicities[context["cluster_position"]][order].astype(np.float64)
    residual = context["residual"][order]
    score = context["scores"][score_name][order]
    total = float(weights.sum())
    if total <= 0:
        return float("nan")
    starts = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    group_weight = np.add.reduceat(weights, starts)
    group_risk = np.add.reduceat(weights * residual, starts)
    active = group_weight > 0
    coverage = np.cumsum(group_weight[active]) / total
    generalized = np.cumsum(group_risk[active]) / total
    return float(np.trapz(np.r_[0.0, generalized], np.r_[0.0, coverage]))


def bootstrap_worker(replicate: int):
    rng = np.random.RandomState(20260809 + replicate)
    unit_aug = {}
    hashes = {}
    for unit, context in _BOOT.items():
        draw = rng.randint(0, context["cluster_count"], size=context["cluster_count"])
        counts = np.bincount(draw, minlength=context["cluster_count"]).astype(np.int64)
        hashes[unit] = sha256_bytes(counts.tobytes(order="C"))
        unit_aug[unit] = {name: weighted_aug(context, name, counts) for name in ["S0", *BASELINES]}
    deltas = []
    for dataset in ("DIOR-R", "FAIR1M", "SODA-A"):
        units = [unit for unit, value in UNITS.items() if value[0] == dataset]
        for baseline in BASELINES:
            deltas.append(float(np.mean([unit_aug[unit]["S0"] - unit_aug[unit][baseline] for unit in units])))
    return replicate, deltas, hashes


def replay_bootstrap(base: Path, frames: dict[str, pd.DataFrame], cluster_rows: list[dict], metrics: list[dict]) -> dict:
    global _BOOT
    _BOOT = boot_context(frames, cluster_rows)
    with mp.get_context("fork").Pool(39) as pool:
        results = pool.map(bootstrap_worker, range(10000), chunksize=4)
    saved = pd.read_csv(base / "track_m_bootstrap_replicates.csv")
    source = pd.read_csv(SOURCE / "track_m_bootstrap.csv")
    max_error = {column: 0.0 for column in BOOT_COLUMNS}
    distributions = {column: np.empty(10000, dtype=np.float64) for column in BOOT_COLUMNS}
    for replicate, deltas, hashes in results:
        row = saved.iloc[replicate]
        source_row = source.iloc[replicate]
        if int(row.replicate) != replicate or int(source_row.replicate) != replicate:
            raise ValidationFailure(f"bootstrap replicate id mismatch: {replicate}")
        for index, column in enumerate(BOOT_COLUMNS):
            value = deltas[index]
            distributions[column][replicate] = value
            close_float(value, row[f"actual__{column}"], f"independent bootstrap {replicate}/{column}")
            close_float(value, source_row[column], f"source bootstrap {replicate}/{column}")
            max_error[column] = max(max_error[column], abs(value - float(source_row[column])))
        for unit in UNITS:
            if row[f"cluster_multiplicity_sha256__{unit}"] != hashes[unit] or row[f"source_cluster_multiplicity_sha256__{unit}"] != "SOURCE_FIELD_ABSENT":
                raise ValidationFailure(f"bootstrap cluster multiplicity mismatch: {replicate}/{unit}")
    comparison = pd.read_csv(base / "track_m_bootstrap_comparison.csv")
    point = {(row["dataset"], row["score"]): row for row in metrics if row["level"] == "dataset_aggregate"}
    for column, values in distributions.items():
        dataset, baseline = column.split("__S0_minus_")
        row = comparison[(comparison.dataset == dataset) & (comparison.baseline == baseline)]
        if len(row) != 1:
            raise ValidationFailure(f"bootstrap comparison identity mismatch: {column}")
        row = row.iloc[0]
        close_float(point[(dataset, "S0")]["AUGRC"] - point[(dataset, baseline)]["AUGRC"], row.point_delta, f"bootstrap point delta {column}")
        close_float(np.percentile(values, 2.5), row.ci_lower_2_5, f"bootstrap CI low {column}")
        close_float(np.percentile(values, 97.5), row.ci_upper_97_5, f"bootstrap CI high {column}")
        if int(row.replicates) != 10000 or int(row.seed) != 20260809 or row.bootstrap_ci_role != "REPORT_ONLY_NOT_STATE_DRIVER":
            raise ValidationFailure(f"bootstrap protocol fields mismatch: {column}")
    return {"replicates": 10000, "workers": 39, "max_source_abs_error": max(max_error.values())}


def verify_reference(base: Path) -> dict:
    record = json.loads((base / "track_m_reference_check.json").read_text())
    repo = base / "references/fd-shifts/attempt-01"
    required = {
        "fd_shifts/analysis/rc_stats.py": ("563be2ed8652c730dd940eb241d8642717e25c0d", "d7f823c58bae5bbee4af2c0b5296bea41d6494884bd868d859890e9ccac22619"),
        "fd_shifts/analysis/rc_stats_utils.py": ("9f99c499f370b587d0ca73e2d9679a358de55e05", "a827fcf36d278beccc804e0d1895428f920c746dcc316a19f81bf3f341276b1f"),
    }
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_LFS_SKIP_SMUDGE": "1"}
    def git(*args, expected=(0,)):
        result = subprocess.run(["git", "-C", str(repo), "-c", f"core.hooksPath={base / 'references/fd-shifts/empty-hooks'}", "-c", f"init.templateDir={base / 'references/fd-shifts/empty-template'}", "-c", "submodule.recurse=false", "-c", "protocol.file.allow=never", *args], env=env, capture_output=True)
        if result.returncode not in expected:
            raise ValidationFailure(f"reference local git command failed: {args} exit={result.returncode}")
        return result.stdout
    if git("remote", "get-url", "origin").decode().strip() != "https://github.com/IML-DKFZ/fd-shifts.git":
        raise ValidationFailure("reference remote mismatch")
    if git("rev-parse", "HEAD").decode().strip() != "c4467aec134e99691359da209f811d91283fc1e3" or git("cat-file", "-t", "HEAD").decode().strip() != "commit":
        raise ValidationFailure("reference commit identity mismatch")
    if git("symbolic-ref", "-q", "HEAD", expected=(0, 1)).strip() or git("status", "--porcelain=v1").strip() or git("submodule", "status").strip():
        raise ValidationFailure("reference checkout not detached/clean/submodule-free")
    if git("remote").decode().splitlines() != ["origin"]:
        raise ValidationFailure("reference has extra/missing remote")
    for relpath, (oid, digest) in required.items():
        blob = git("cat-file", "blob", oid)
        if sha256_bytes(blob) != digest or (repo / relpath).read_bytes() != blob:
            raise ValidationFailure(f"reference blob/checkout mismatch: {relpath}")
    adapter_path = base / record["adapter"]["path"]
    if sha256_path(adapter_path) != record["adapter"]["sha256"] or adapter_path.stat().st_size != int(record["adapter"]["bytes"]):
        raise ValidationFailure("reference adapter identity mismatch")
    spec = importlib.util.spec_from_file_location("receipt3_pinned_adapter", adapter_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    if module.RiskCoverageStats.AUC_DISPLAY_SCALE != 1000 or record["reference_auc_display_scale"] != 1000:
        raise ValidationFailure("reference AUC display scale mismatch")
    for vector in record["vectors"]:
        score = np.asarray(vector["score"], dtype=np.float64)
        residual = np.asarray(vector["residual"], dtype=np.float64)
        stats = module.RiskCoverageStats(confids=score, residuals=residual)
        curve = stats.curve_stats_generalized_risk
        display = float(stats.augrc)
        if not np.allclose(curve["coverages"], vector["reference_coverages_descending"], atol=1e-12, rtol=0) or not np.allclose(curve["risks"], vector["reference_risks_descending"], atol=1e-12, rtol=0):
            raise ValidationFailure(f"reference dynamic curve mismatch: {vector['case']}")
        close_float(display, vector["reference_augrc_display"], f"reference display AUGRC {vector['case']}")
        close_float(display / 1000.0, vector["reference_augrc_unscaled"], f"reference unscaled AUGRC {vector['case']}")
    return {"status": "PASS", "commit": record["head"], "vectors": len(record["vectors"]), "path": str(repo)}


def outcome_adjudication(row: dict) -> tuple[str, bool]:
    raw = row["raw_hit"]
    candidate = row["candidate"]
    exact = candidate == "ICDAR-MLT" and (
        row["search_phase"] == "track_d_search_pth_readme"
        or "outputs/bench_core/baseline_inventory" in raw
    ) and bool(re.search(r"best_mAP_|DOTAMetric|\*\*0\.[0-9]+\*\*|,0\.[0-9]{3,},", raw))
    if exact:
        return "OUTCOME_BEARING_PRIOR_PROJECT_ENDPOINT", True
    if "official_sources/" in raw:
        return "OFFICIAL_DATASET_PUBLICATION_NOT_PROJECT_ENDPOINT", False
    if "dis/sug" in raw or "server_reports" in raw or "feasibility_gate" in raw or "claude_code_and_supervisor" in raw:
        return "CONTROL_REPORT_OR_PROTOCOL_MENTION", False
    return "NON_OUTCOME_ASSET_OR_NAME_MENTION", False


def derive_track_d(base: Path, write: bool) -> dict:
    official = pd.read_csv(base / "track_d_official_sources.csv", keep_default_na=False)
    assets = pd.read_csv(base / "track_d_asset_inventory.csv", keep_default_na=False)
    hits = list(csv.DictReader((base / "track_d_prior_outcome_hits.csv").open(encoding="utf-8")))
    source_bodies = {}
    for row in official.to_dict("records"):
        meta_path = ROOT / row["meta_path"]
        if not meta_path.is_file() or meta_path.stat().st_size != int(row["meta_bytes"]) or sha256_path(meta_path) != row["meta_sha256"]:
            raise ValidationFailure(f"Track D meta identity mismatch: {row['source_id']}")
        meta = json.loads(meta_path.read_text())
        if int(meta.get("http_status", 0)) != int(row["http_status"]) or int(meta.get("bytes", 0)) != int(row["body_bytes"]):
            raise ValidationFailure(f"Track D meta facts mismatch: {row['source_id']}")
        body_path = str(row["body_path"])
        if body_path.startswith("outputs/"):
            actual = ROOT / body_path
            if not actual.is_file() or actual.stat().st_size != int(row["body_bytes"]) or sha256_path(actual) != row["body_sha256"]:
                raise ValidationFailure(f"Track D body identity mismatch: {row['source_id']}")
            source_bodies[row["source_id"]] = actual.read_text(encoding="utf-8", errors="replace")
    adjudicated = []
    counts = {name: 0 for name in ("AI-TOD-R", "UAV-OBB", "ShipRSImageNet", "ICDAR-MLT")}
    for row in hits:
        decision, exact = outcome_adjudication(row)
        row["independent_validator_adjudication"] = decision
        row["prior_exact_outcome_or_endpoint"] = str(exact)
        adjudicated.append(row)
        if exact and row["candidate"] in counts:
            counts[row["candidate"]] += 1
    if write:
        write_csv(base / "track_d_prior_outcome_hits.csv", adjudicated)

    aitod = source_bodies.get("aitodr", "")
    uav = source_bodies.get("uavobb", "")
    ship_readme = source_bodies.get("shiprs_readme", "")
    ship_license = source_bodies.get("shiprs_license", "")
    ship_api = source_bodies.get("shiprs_repo_api", "")
    icdar = source_bodies.get("icdar_mlt_insecure", "")
    bodies = {"AI-TOD-R": aitod, "UAV-OBB": uav, "ShipRSImageNet": ship_readme, "ICDAR-MLT": icdar}
    facts = {}
    for candidate in counts:
        candidate_assets = assets[assets.candidate == candidate]
        dataset_rows = candidate_assets[candidate_assets.asset_role == "dataset_root_filename_stat_only"]
        dataset_present = len(dataset_rows) == 1 and as_bool(dataset_rows.iloc[0].present)
        body = bodies[candidate]
        remote = {
            "AI-TOD-R": "drone, satellite imagery" in body and "oriented bounding boxes" in body,
            "UAV-OBB": "aerial urban vehicle dataset" in body and "UAV imagery" in body,
            "ShipRSImageNet": "remote sensing images" in body and "ship detection" in body,
            "ICDAR-MLT": False,
        }[candidate]
        if candidate == "AI-TOD-R":
            license_count = 0 if "This website is licensed" in body and "dataset is licensed" not in body else 1
            license_closed = False
            angle_reasons = ["no stored format/vertex-order/canonicalization contract"]
        elif candidate == "UAV-OBB":
            license_count = int("This dataset is released under the Creative Commons Attribution 4.0 International License" in body)
            license_closed = license_count > 0
            angle_reasons = ["stored source conflicts between center-angle and four-vertex descriptions", "clockwise/long-side/near-square/ignore conversion is not uniquely specified"]
        elif candidate == "ShipRSImageNet":
            api_null = bool(re.search(r'"license"\s*:\s*null', ship_api))
            license_404 = ship_license.strip() == "404: Not Found"
            academic_only = "academic purposes only" in body and "commercial use is prohibited" in body
            license_count = 0 if api_null and license_404 else int(academic_only)
            license_closed = False
            angle_reasons = ["OBB/polygon statement lacks vertex-order/angle/canonicalization/ignore conversion"]
        else:
            license_count = 0
            license_closed = False
            angle_reasons = ["stored competition page does not close frozen OBB conversion semantics"]
        unique_conversion = False
        registered = candidate_assets[candidate_assets.asset_role == "registered_config_or_checkpoint"]
        config_present = bool(len(registered[registered.type == "py"]))
        checkpoint_present = bool(len(registered[registered.type == "pth"]))
        environment_present = False
        parser_present = False
        contamination = counts[candidate] > 0
        license_blocked = license_count == 0 or not license_closed
        angle_blocked = not unique_conversion
        missing_asset = not all((dataset_present, config_present, checkpoint_present, environment_present, parser_present))
        if contamination:
            status = "CONTAMINATED"
        elif license_blocked:
            status = "LICENSE_BLOCKED"
        elif angle_blocked:
            status = "INCOMPATIBLE_ANGLE_CONTRACT"
        elif missing_asset:
            status = "MISSING_ASSET"
        else:
            status = "ELIGIBLE_CANDIDATE"
        facts[candidate] = {
            "auxiliary_only": candidate == "ICDAR-MLT",
            "backup_only": candidate == "ShipRSImageNet",
            "remote_sensing_identity": remote,
            "prior_exact_outcome_or_endpoint_evidence_count": counts[candidate],
            "official_license_evidence_count": license_count,
            "official_license_closed_for_processing_and_redistribution": license_closed,
            "unique_conversion_proven": unique_conversion,
            "angle_contract_failure_reasons": angle_reasons,
            "dataset_present": dataset_present,
            "compatible_exact_config_present": config_present,
            "compatible_exact_checkpoint_present": checkpoint_present,
            "compatible_exact_environment_present": environment_present,
            "compatible_exact_parser_present": parser_present,
            "required_asset_hash_or_load_preflight_failed": missing_asset,
            "common_detector_families": [],
            "target_label_tuning_required": True,
            "predicates": {
                "CONTAMINATED": contamination,
                "LICENSE_BLOCKED": license_blocked,
                "INCOMPATIBLE_ANGLE_CONTRACT": angle_blocked,
                "MISSING_ASSET": missing_asset,
            },
            "status": status,
            "precedence": "CONTAMINATED > LICENSE_BLOCKED > INCOMPATIBLE_ANGLE_CONTRACT > MISSING_ASSET",
            "evidence_paths": ["track_d_official_sources.csv", "track_d_search_runs.csv", "track_d_prior_outcome_hits.csv", "track_d_asset_inventory.csv"],
        }
    result = {
        "candidate_facts": facts,
        "candidate_statuses": {candidate: fact["status"] for candidate, fact in facts.items()},
        "remote_sensing_eligible_candidates": [candidate for candidate, fact in facts.items() if fact["remote_sensing_identity"] and not fact["auxiliary_only"] and fact["status"] == "ELIGIBLE_CANDIDATE"],
        "common_detector_family_set": [],
        "common_detector_family_count": 0,
        "new_family_not_in_old_core_present": False,
        "future_target_label_tuning_required": True,
        "raw_evidence_only_generator": True,
        "derived_by": "independent_validator_from_raw_official/search/stat/hash_evidence",
    }
    existing_path = base / "track_d_status.json"
    if existing_path.is_file():
        existing = json.loads(existing_path.read_text())
        if existing != result:
            raise ValidationFailure("track_d_evidence_fact mutation or Track D derived-fact mismatch")
    elif write:
        write_json(existing_path, result)
    return result


def derive_gate(track_m_state: str, track_d: dict) -> dict:
    eligible = track_d["remote_sensing_eligible_candidates"]
    facts = track_d["candidate_facts"]
    required_remote = [candidate for candidate in ("AI-TOD-R", "UAV-OBB", "ShipRSImageNet")]
    clauses = {
        "track_m_negative_state": track_m_state in {"METRIC_REVERSAL", "BASELINE_DOMINATED", "SENSITIVITY_UNSTABLE"},
        "fewer_than_two_independent_remote_eligible": len(eligible) < 2,
        "common_at_least_three_detector_families": track_d["common_detector_family_count"] >= 3,
        "new_family_not_in_old_core_present": track_d["new_family_not_in_old_core_present"],
        "all_required_license_contracts_closed": all(facts[candidate]["official_license_closed_for_processing_and_redistribution"] for candidate in eligible) if len(eligible) >= 2 else False,
        "all_required_angle_contracts_closed": all(facts[candidate]["unique_conversion_proven"] for candidate in eligible) if len(eligible) >= 2 else False,
        "future_target_label_tuning_required": track_d["future_target_label_tuning_required"],
    }
    negative = (
        clauses["track_m_negative_state"]
        or clauses["fewer_than_two_independent_remote_eligible"]
        or not clauses["common_at_least_three_detector_families"]
        or not clauses["new_family_not_in_old_core_present"]
        or not clauses["all_required_license_contracts_closed"]
        or not clauses["all_required_angle_contracts_closed"]
        or clauses["future_target_label_tuning_required"]
    )
    if negative:
        gate = "FAIL_TO_MEASUREMENT_ONLY"
    elif track_m_state == "INSUFFICIENT_ASSETS":
        gate = "INCONCLUSIVE_FEASIBILITY"
    elif track_m_state == "ROBUST_CANDIDATE" and len(eligible) >= 2 and clauses["common_at_least_three_detector_families"] and clauses["new_family_not_in_old_core_present"] and not clauses["future_target_label_tuning_required"]:
        gate = "PASS_TO_METHOD_DESIGN"
    else:
        raise ValidationFailure("joint gate predicates do not yield a unique frozen gate")
    return {
        "track_m_state": track_m_state,
        "track_d_remote_eligible_count": len(eligible),
        "track_d_remote_eligible_candidates": eligible,
        "clauses": clauses,
        "negative_precedence": True,
        "joint_gate": gate,
        "method_design_authorized": False,
        "final_commit_sha": "POST_COMMIT_EXTERNAL_RECEIPT",
        "git_publish_status": "PENDING_EXTERNAL_RECEIPT",
    }


def early_derived_mutation_precheck(base: Path) -> None:
    track_d_path = base / "track_d_status.json"
    if not track_d_path.is_file():
        return
    track_d = derive_track_d(base, write=False)
    metrics = pd.read_csv(base / "track_m_metrics.csv").to_dict("records")
    state, _ = production_state(metrics)
    gate = derive_gate(state, track_d)
    gate_path = base / "joint_gate.json"
    if gate_path.is_file() and json.loads(gate_path.read_text()) != gate:
        raise ValidationFailure("joint_gate_clause mutation or independently derived joint-gate mismatch")


def validate(base: Path, write: bool) -> dict:
    inventory = inventory_precheck(base)
    bootstrap_saved_fast_precheck(base)
    early_derived_mutation_precheck(base)
    reference = verify_reference(base)
    frames, clusters = load_raw_frames(base, inventory)
    metrics = recompute_metrics_and_curves(base, frames)
    verify_state_fixtures(base)
    track_m_state, witnesses = production_state(metrics)
    bootstrap = replay_bootstrap(base, frames, clusters, metrics)
    track_d = derive_track_d(base, write=write)
    gate = derive_gate(track_m_state, track_d)
    existing_gate = base / "joint_gate.json"
    if existing_gate.is_file():
        if json.loads(existing_gate.read_text()) != gate:
            raise ValidationFailure("joint_gate_clause mutation or independently derived joint-gate mismatch")
    elif write:
        write_json(existing_gate, gate)
    published_m = json.loads((base / "track_m_status.json").read_text())
    published_witnesses = published_m["witnesses"]
    if published_m["state"] != track_m_state or len(published_witnesses) != len(witnesses):
        raise ValidationFailure("Track M published state/witness count mismatch")
    for actual, expected in zip(witnesses, published_witnesses):
        if actual["dataset"] != expected["dataset"] or actual["baseline"] != expected["baseline"]:
            raise ValidationFailure("Track M published witness identity mismatch")
        for metric in ("NRC", "AURC", "AUGRC", "Risk@70", "Risk@90"):
            close_float(actual[metric], expected[metric], f"Track M witness {actual['dataset']}/{actual['baseline']}/{metric}")
    result = {
        "status": "PASS",
        "pre_seal_validator_scope": "FROZEN_SNAPSHOT_AND_PLANNED_OUTPUT",
        "generator_imported": False,
        "sealed_metric_implementation_A_imported": False,
        "source_inventory_rows_verified": len(inventory),
        "raw_core_units_recomputed": list(UNITS),
        "point_metric_rows_recomputed": len(metrics),
        "full_risk_coverage_rows_recomputed": 3313581,
        "bootstrap": bootstrap,
        "reference": reference,
        "track_m_state": track_m_state,
        "track_m_witnesses": witnesses,
        "track_d_candidate_statuses": track_d["candidate_statuses"],
        "joint_gate": gate["joint_gate"],
        "atol": 1e-12,
        "rtol": 0,
        "planned_manifest_schema": {
            "self_bytes": "N/A_SELF_REFERENCE",
            "self_sha256": "N/A_SELF_REFERENCE",
            "classifications": ["PRE_SEAL_SCIENTIFIC_AUDIT_INPUT", "PRE_SEAL_EXECUTED_CODE", "PRE_SEAL_RUNTIME_OUTPUT", "SELF_REFERENCE_NOT_INDEPENDENTLY_VALIDATED", "POST_MANIFEST_TRACKED_OUTPUT_EXTERNAL_VALIDATION", "EXTERNAL_RECEIPT_ONLY_NOT_REPOSITORY_EVIDENCE"],
        },
        "planned_report_tokens": {
            "tracked_report_source": "FROZEN_SNAPSHOT",
            "tracked_report_self_validation": "EXTERNAL_GIT_BLOB_ONLY",
            "final_commit_sha": "POST_COMMIT_EXTERNAL_RECEIPT",
            "git_publish_status": "PENDING_EXTERNAL_RECEIPT",
        },
    }
    if write:
        write_json(base / "validator.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    try:
        result = validate(args.root.resolve(), write=not args.check_only)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error_type": type(exc).__name__, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps({"status": result["status"], "track_m": result["track_m_state"], "joint_gate": result["joint_gate"]}))


if __name__ == "__main__":
    main()

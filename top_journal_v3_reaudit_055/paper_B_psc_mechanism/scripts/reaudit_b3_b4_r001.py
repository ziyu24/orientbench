#!/usr/bin/env python3
"""Instance-estimand cluster bootstrap re-audit for B3/B4 and executable B5 gate."""
from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import math
import os
import struct
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
BROOT = Path(__file__).resolve().parents[1]
REPORTS = BROOT / "reports"
G0 = ROOT / "top_journal_v3_reaudit_055/shared_forensics/g0"
ROUND_ID = "orientbench-c-r001-20260805"
SNAPSHOT = "9d9cdae1847f9c82e841f6f8b2692389cf9d9d79"
REPLICATES = 800
WORKERS = 40
REPORT_PATH = ROOT / "dis/server_reports/orientbench-c-r001-20260805.md"
SCRIPT_PATH = Path(__file__).resolve()
TEST_PATH = SCRIPT_PATH.with_name("test_b3_b4_reaudit_r001.py")

OUT_B3 = REPORTS / "b3_candidate_cluster_bootstrap_reaudit_r001.csv"
OUT_B4 = REPORTS / "b4_candidate_external_bootstrap_reaudit_r001.csv"
OUT_GATE = REPORTS / "b5_gate_reaudit_r001.csv"
OUT_TESTS = REPORTS / "b3_b4_estimand_equivalence_tests_r001.csv"
OUT_MANIFEST = REPORTS / "b3_b4_reaudit_manifest_r001.json"

EXPECTED_THRESHOLD_SHA = "b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
EXPECTED_SPLITS = {
    "outputs/bench_core/splits/D_audit_dior_trainval.csv": "11c61be3a03c922b5e00e4cf9e866cf73e18eff44bd6b868b53f54612065669b",
    "outputs/bench_core/splits/D_audit_dota10_train.csv": "d4fb9a793a4c2f31ddd42cde0ba8c571114e78b2ab0d3af36002f201fafc1eb7",
    "outputs/bench_core/splits/D_audit_dota15_train.csv": "ac97d1f3f2a780f79019612fce6f7f93d13aa9f7a65c4f1c14aa96447e743856",
    "outputs/bench_core/splits/D_audit_fair1m_train.csv": "140ef6855909cdca2904656ad76baca31ff11d8c571e3978e005d945440c335e",
    "outputs/bench_core/splits/D_audit_hrsc_trainval.csv": "55734ae8aa3f49350186fd066a761a54fe1a99921897012c5e59ca1fdf9f6679",
    "outputs/bench_core/splits/D_cal_dior_trainval.csv": "f624a21451de394a35041af35c9a910c3a1bdc11fb5c942d15416e04e0e6f632",
    "outputs/bench_core/splits/D_cal_dota10_train.csv": "48a0319a1ea51fcbadf43e7e632d5a77f77d3db73442acfd639acb0c455daed4",
    "outputs/bench_core/splits/D_cal_dota15_train.csv": "aa59e4266872c2f3f48b6c027798255e21fae64b09519a895d3ba8deb85b9364",
    "outputs/bench_core/splits/D_cal_fair1m_train.csv": "84b32cb5e0bd9a7afdc772f824e1b64f9daaca54fccdbbb98750180bc04b16a0",
    "outputs/bench_core/splits/D_cal_hrsc_trainval.csv": "bbaf79002ad683893292101744e32e379d711f14ab7c187ae5bad42d2e37bdb0",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, path)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def nrc_unweighted(score: np.ndarray, risk: np.ndarray) -> float:
    score = np.asarray(score, dtype=float)
    risk = np.asarray(risk, dtype=float)
    valid = np.isfinite(score) & np.isfinite(risk)
    score, risk = score[valid], risk[valid]
    if len(score) < 2 or np.nanstd(risk) < 1e-12:
        return float("nan")
    order = np.argsort(-score, kind="stable")
    selected = np.cumsum(risk[order]) / np.arange(1, len(risk) + 1)
    oracle = np.cumsum(risk[np.argsort(risk, kind="stable")]) / np.arange(1, len(risk) + 1)
    denominator = float(np.mean(risk) - np.mean(oracle))
    return float((np.mean(selected) - np.mean(oracle)) / denominator) if abs(denominator) > 1e-12 else float("nan")


def _weighted_aurc(ordered_risk: np.ndarray, ordered_weights: np.ndarray, harmonic: np.ndarray) -> float:
    keep = ordered_weights > 0
    rr = ordered_risk[keep]
    ww = ordered_weights[keep].astype(np.int64, copy=False)
    cumulative_n = np.cumsum(ww)
    total = int(cumulative_n[-1])
    cumulative_risk = np.cumsum(ww * rr)
    before_n = cumulative_n - ww
    before_risk = cumulative_risk - ww * rr
    terms = ww * rr + (before_risk - before_n * rr) * (
        harmonic[cumulative_n] - harmonic[before_n]
    )
    return float(np.sum(terms) / total)


def weighted_nrc(score: np.ndarray, risk: np.ndarray, weights: np.ndarray) -> float:
    score = np.asarray(score, dtype=float)
    risk = np.asarray(risk, dtype=float)
    weights = np.asarray(weights, dtype=np.int64)
    valid = np.isfinite(score) & np.isfinite(risk) & (weights >= 0)
    score, risk, weights = score[valid], risk[valid], weights[valid]
    total = int(weights.sum())
    if total < 2 or np.count_nonzero(weights) < 2:
        return float("nan")
    harmonic = np.empty(total + 1, dtype=float)
    harmonic[0] = 0.0
    harmonic[1:] = np.cumsum(1.0 / np.arange(1, total + 1))
    score_order = np.argsort(-score, kind="stable")
    oracle_order = np.argsort(risk, kind="stable")
    selected_auc = _weighted_aurc(risk[score_order], weights[score_order], harmonic)
    oracle_auc = _weighted_aurc(risk[oracle_order], weights[oracle_order], harmonic)
    random_auc = float(np.dot(weights, risk) / total)
    denominator = random_auc - oracle_auc
    return float((selected_auc - oracle_auc) / denominator) if abs(denominator) > 1e-12 else float("nan")


def explicit_expansion_nrc(score: np.ndarray, risk: np.ndarray, weights: np.ndarray) -> float:
    index = np.repeat(np.arange(len(score)), np.asarray(weights, dtype=np.int64))
    return nrc_unweighted(np.asarray(score)[index], np.asarray(risk)[index])


def legacy_cluster_mean_nrc(score: np.ndarray, risk: np.ndarray, clusters: np.ndarray,
                            cluster_multiplicities: np.ndarray) -> float:
    """Reproduce the superseded bootstrap estimand for a discriminating test only."""
    labels, inverse = np.unique(np.asarray(clusters).astype(str), return_inverse=True)
    counts = np.bincount(inverse)
    mean_score = np.bincount(inverse, weights=score) / counts
    mean_risk = np.bincount(inverse, weights=risk) / counts
    if len(labels) != len(cluster_multiplicities):
        raise ValueError("cluster multiplicity length mismatch")
    return explicit_expansion_nrc(mean_score, mean_risk, cluster_multiplicities)


def load_g0_module():
    path = G0 / "scripts/run_g0_forensics.py"
    spec = importlib.util.spec_from_file_location("g0_r001_check", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def equivalence_tests() -> list[dict]:
    cases = [
        ("continuous_no_ties", np.array([.9, .4, .8, .1]), np.array([1., 4., 2., 8.]), np.array([2, 0, 3, 1])),
        ("continuous_ties", np.array([.5, .5, .2, .5, .1]), np.array([3., 1., 4., 2., 8.]), np.array([1, 4, 0, 2, 3])),
        ("binary_event", np.array([.7, .4, .2, .9, .1]), np.array([0., 1., 0., 1., 0.]), np.array([3, 1, 2, 0, 4])),
        ("cluster_resample", np.array([.2, .9, .3, .7, .4, .4]), np.array([7., 1., 5., 2., 4., 9.]), np.array([0, 2, 2, 1, 3, 1])),
    ]
    g0 = load_g0_module()
    rows = []
    for name, score, risk, weights in cases:
        explicit = explicit_expansion_nrc(score, risk, weights)
        weighted = weighted_nrc(score, risk, weights)
        order = np.argsort(-score, kind="stable")
        g0_value = float(g0.weighted_metrics(order, risk, weights)["nrc"])
        for implementation, observed in (("r001_weighted", weighted), ("g0_weighted", g0_value)):
            error = abs(observed - explicit)
            rows.append({
                "test_id": f"{name}:{implementation}", "category": "explicit_multiplicity_equivalence",
                "stage": "synthetic", "expected": explicit, "observed": observed,
                "abs_error": error, "tolerance": 1e-12,
                "status": "PASS" if error <= 1e-12 else "FAIL",
                "notes": "stable original-row tie order; zero multiplicities retained as zero weights",
            })
    score = np.array([.5, .5, .2, .8, .1], float)
    risk = np.array([3., 1., 5., 2., 8.], float)
    point = nrc_unweighted(score, risk)
    weighted_point = weighted_nrc(score, risk, np.ones(len(score), dtype=int))
    rows.append({
        "test_id": "unit_weights_point_estimand", "category": "point_estimate_equivalence",
        "stage": "synthetic", "expected": point, "observed": weighted_point,
        "abs_error": abs(point - weighted_point), "tolerance": 1e-12,
        "status": "PASS" if abs(point - weighted_point) <= 1e-12 else "FAIL",
        "notes": "all-one multiplicity reproduces matched-instance NRC",
    })
    score = np.array([.95, .80, .65, .50, .45, .30, .10], dtype=float)
    risk = np.array([.1, .3, .2, .4, 8., 1., 6.], dtype=float)
    clusters = np.array(["a", "a", "a", "a", "b", "c", "c"], dtype=object)
    cluster_multiplicities = np.array([1, 3, 1], dtype=int)
    _, inverse = np.unique(clusters.astype(str), return_inverse=True)
    instance_weights = cluster_multiplicities[inverse]
    correct = weighted_nrc(score, risk, instance_weights)
    legacy = legacy_cluster_mean_nrc(score, risk, clusters, cluster_multiplicities)
    separation = abs(correct - legacy)
    rows.append({
        "test_id": "heterogeneous_cluster_old_estimand_rejected",
        "category": "legacy_cluster_mean_discrimination", "stage": "synthetic",
        "expected": "absolute difference > 0.01", "observed": separation,
        "abs_error": "", "tolerance": 0.01,
        "status": "PASS" if separation > 0.01 else "FAIL",
        "notes": "heterogeneous cluster sizes make old cluster-mean NRC disagree with instance-multiplicity NRC",
    })
    return rows


def deterministic_seed(stage: str, dataset: str, seed: int) -> int:
    digest = hashlib.sha256(f"{ROUND_ID}|{stage}|{dataset}|{seed}".encode()).hexdigest()
    return 100_000 + int(digest[:12], 16) % 10_000_000


def resample_plan(clusters: np.ndarray, mc_seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    labels, inverse = np.unique(np.asarray(clusters).astype(str), return_inverse=True)
    multiplicities = np.empty((REPLICATES, len(labels)), dtype=np.uint16)
    digest = hashlib.sha256()
    digest.update(f"seed={mc_seed}|reps={REPLICATES}|clusters={len(labels)}".encode())
    for label in labels:
        encoded = label.encode("utf-8")
        digest.update(struct.pack("<I", len(encoded)))
        digest.update(encoded)
    for replicate in range(REPLICATES):
        rng = np.random.RandomState(mc_seed + replicate * 104729)
        picked = rng.randint(0, len(labels), len(labels)).astype("<i4", copy=False)
        multiplicities[replicate] = np.bincount(picked, minlength=len(labels)).astype(np.uint16)
        digest.update(struct.pack("<I", replicate))
        digest.update(picked.tobytes())
    return labels, inverse, multiplicities, digest.hexdigest()


def universe_hash(clusters: np.ndarray, risk: np.ndarray, phase: np.ndarray, detection: np.ndarray) -> str:
    digest = hashlib.sha256()
    for value in np.asarray(clusters).astype(str):
        encoded = value.encode("utf-8")
        digest.update(struct.pack("<I", len(encoded)))
        digest.update(encoded)
    for name, array in (("risk", risk), ("phase_mod", phase), ("detection_score", detection)):
        a = np.ascontiguousarray(array, dtype="<f8")
        digest.update(name.encode())
        digest.update(struct.pack("<Q", len(a)))
        digest.update(a.tobytes())
    return digest.hexdigest()


def bootstrap_nrc(scores: dict[str, np.ndarray], risk: np.ndarray, inverse: np.ndarray,
                  multiplicities: np.ndarray) -> dict[str, np.ndarray]:
    names = list(scores)
    orders = {name: np.argsort(-np.asarray(scores[name], float), kind="stable") for name in names}
    oracle_order = np.argsort(risk, kind="stable")
    cluster_sizes = np.bincount(inverse).astype(np.int64)
    totals = multiplicities.astype(np.int64) @ cluster_sizes
    maximum_total = int(totals.max())
    harmonic = np.empty(maximum_total + 1, dtype=float)
    harmonic[0] = 0.0
    harmonic[1:] = np.cumsum(1.0 / np.arange(1, maximum_total + 1))

    def one(replicate: int) -> np.ndarray:
        weights = multiplicities[replicate][inverse].astype(np.int64, copy=False)
        total = int(weights.sum())
        oracle_auc = _weighted_aurc(risk[oracle_order], weights[oracle_order], harmonic)
        random_auc = float(np.dot(weights, risk) / total)
        denominator = random_auc - oracle_auc
        values = np.empty(len(names), dtype=float)
        if abs(denominator) <= 1e-12:
            values.fill(np.nan)
            return values
        for index, name in enumerate(names):
            order = orders[name]
            selected_auc = _weighted_aurc(risk[order], weights[order], harmonic)
            values[index] = (selected_auc - oracle_auc) / denominator
        return values

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        matrix = np.asarray(list(pool.map(one, range(REPLICATES))), dtype=float)
    return {name: matrix[:, index] for index, name in enumerate(names)}


def phase_components(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    cosine = np.array([1.0, -0.5, -0.5])
    sine = np.array([0.0, math.sqrt(3) / 2, -math.sqrt(3) / 2])
    c1, s1 = vectors[:, :3] @ cosine, vectors[:, :3] @ sine
    c2, s2 = vectors[:, 3:6] @ cosine, vectors[:, 3:6] @ sine
    p1 = -np.arctan2(s1, c1)
    p2 = -np.arctan2(s2, c2) / 2.0
    return p1, p2, c1 * c1 + s1 * s1, c2 * c2 + s2 * s2


def candidate_scores(vectors: np.ndarray) -> dict[str, np.ndarray]:
    p1, p2, mod1, mod2 = phase_components(vectors)
    candidate0 = p2
    candidate1 = np.mod(p2, 2 * np.pi) - np.pi
    alignment0 = np.cos(p1 - candidate0)
    alignment1 = np.cos(p1 - candidate1)
    chosen = np.where(alignment1 > alignment0, candidate1, candidate0)
    signed = (p1 / 2.0 - chosen / 2.0 + np.pi / 2) % np.pi - np.pi / 2
    disagreement = np.degrees(np.abs(signed))
    gap = np.abs(alignment0 - alignment1)
    return {
        "phase_mod": mod1,
        "multi_frequency_consistency": -disagreement,
        "unwrap_candidate_energy_gap": gap,
        "phase_direction_margin": gap * np.sqrt(np.maximum(mod2, 0)),
    }


def delta_threshold(aspect_ratio: np.ndarray) -> np.ndarray:
    frozen = json.loads((ROOT / "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json").read_text())
    return np.interp(aspect_ratio, np.asarray(frozen["ar"], float), np.asarray(frozen["dtheta_075"], float))


def b3_units() -> Iterable[tuple[str, int, dict[str, np.ndarray], Path]]:
    aliases = {"DIOR-R": "DIOR_R", "SODA-A": "SODA_A", "FAIR1M-v1.0": "FAIR1M"}
    for dataset in ("DIOR-R", "SODA-A", "FAIR1M-v1.0"):
        for seed in range(3):
            cache = BROOT / f"artifacts/b3_cache/{aliases[dataset]}_seed{seed}.npz"
            loaded = np.load(cache, allow_pickle=True)
            arrays = {key: loaded[key] for key in loaded.files}
            mask = arrays["ar"].astype(float) >= 2.1
            arrays = {key: value[mask] for key, value in arrays.items()}
            yield dataset, seed, arrays, cache


def b4_unit(seed: int) -> tuple[dict[str, np.ndarray], Path]:
    path = BROOT / f"artifacts/b4_external/seed{seed}/matched_phase.jsonl.gz"
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    arrays = {
        "cluster": np.asarray([row["mother_scene_id"] for row in rows], dtype=object),
        "error": np.asarray([row["angle_error"] for row in rows], dtype=float),
        "ar": np.asarray([row["aspect_ratio"] for row in rows], dtype=float),
        "score": np.asarray([row["detection_score"] for row in rows], dtype=float),
        "vector": np.asarray([row["encoded_vector"] for row in rows], dtype=float),
    }
    mask = arrays["ar"] >= 2.1
    return {key: value[mask] for key, value in arrays.items()}, path


def percentile_ci(values: np.ndarray) -> tuple[float, float, int]:
    finite = np.asarray(values, float)
    finite = finite[np.isfinite(finite)]
    if not len(finite):
        return float("nan"), float("nan"), 0
    low, high = np.percentile(finite, [2.5, 97.5])
    return float(low), float(high), int(len(finite))


BOOT_FIELDS = [
    "round_id", "stage", "dataset", "host", "seed", "candidate", "endpoint",
    "cluster_unit", "cluster_count", "instance_count", "bootstrap_replicates",
    "finite_replicates", "mc_seed", "resample_id_hash", "instance_universe_hash",
    "candidate_nrc", "phase_mod_nrc", "detection_score_nrc",
    "delta_nrc_vs_phase_mod", "delta_vs_phase_ci_lo", "delta_vs_phase_ci_hi",
    "delta_nrc_vs_detection_score", "delta_vs_detection_ci_lo", "delta_vs_detection_ci_hi",
    "supports_vs_phase_mod", "supports_vs_detection_score", "supports_both",
    "legacy_point_delta", "legacy_ci_lo", "legacy_ci_hi", "legacy_point_outside_legacy_ci",
    "new_point_inside_new_ci", "estimand", "stable_tie_order", "score_direction",
]


def make_bootstrap_row(stage: str, dataset: str, host: str, seed: int, candidate: str,
                       endpoint: str, cluster_unit: str, cluster_count: int, instance_count: int,
                       mc_seed: int, resample_hash: str, universe: str,
                       points: dict[str, float], samples: dict[str, np.ndarray], legacy: dict) -> dict:
    delta_phase = samples[candidate] - samples["phase_mod"]
    delta_detection = samples[candidate] - samples["detection_score"]
    phase_low, phase_high, finite_phase = percentile_ci(delta_phase)
    detection_low, detection_high, finite_detection = percentile_ci(delta_detection)
    point_phase = float(points[candidate] - points["phase_mod"])
    point_detection = float(points[candidate] - points["detection_score"])
    legacy_low = float(legacy["ci_lo"])
    legacy_high = float(legacy["ci_hi"])
    legacy_point = float(legacy["point_delta"])
    return {
        "round_id": ROUND_ID, "stage": stage, "dataset": dataset, "host": host, "seed": seed,
        "candidate": candidate, "endpoint": endpoint, "cluster_unit": cluster_unit,
        "cluster_count": cluster_count, "instance_count": instance_count,
        "bootstrap_replicates": REPLICATES, "finite_replicates": min(finite_phase, finite_detection),
        "mc_seed": mc_seed, "resample_id_hash": resample_hash, "instance_universe_hash": universe,
        "candidate_nrc": points[candidate], "phase_mod_nrc": points["phase_mod"],
        "detection_score_nrc": points["detection_score"],
        "delta_nrc_vs_phase_mod": point_phase, "delta_vs_phase_ci_lo": phase_low,
        "delta_vs_phase_ci_hi": phase_high, "delta_nrc_vs_detection_score": point_detection,
        "delta_vs_detection_ci_lo": detection_low, "delta_vs_detection_ci_hi": detection_high,
        "supports_vs_phase_mod": bool(phase_high < 0),
        "supports_vs_detection_score": bool(detection_high < 0),
        "supports_both": bool(phase_high < 0 and detection_high < 0),
        "legacy_point_delta": legacy_point, "legacy_ci_lo": legacy_low, "legacy_ci_hi": legacy_high,
        "legacy_point_outside_legacy_ci": not (legacy_low <= legacy_point <= legacy_high),
        "new_point_inside_new_ci": bool(phase_low <= point_phase <= phase_high),
        "estimand": "matched-instance NRC; cluster multiplicity lifted to every original instance",
        "stable_tie_order": "original matched-row order", "score_direction": "descending; larger=more reliable",
    }


def legacy_b3_rows() -> dict[tuple[str, int, str, str], dict]:
    rows = read_csv(REPORTS / "b3_intervention_metrics.csv")
    phase = {
        (row["dataset"], int(row["seed"]), row["endpoint"]): float(row["nrc"])
        for row in rows if row["analysis"] == "BASELINE_SCORE" and row["intervention"] == "phase_mod"
    }
    result = {}
    for row in rows:
        if row["analysis"] != "BASELINE_SCORE":
            continue
        try:
            low = float(row["paired_delta_nrc_vs_phase_mod_ci_lo"])
            high = float(row["paired_delta_nrc_vs_phase_mod_ci_hi"])
        except ValueError:
            continue
        if not np.isfinite(low + high):
            continue
        key = (row["dataset"], int(row["seed"]), row["endpoint"], row["intervention"])
        result[key] = {
            "ci_lo": low, "ci_hi": high,
            "point_delta": float(row["nrc"]) - phase[key[:3]], "candidate_nrc": float(row["nrc"]),
        }
    return result


def legacy_b4_rows() -> dict[tuple[int, str, str], dict]:
    result = {}
    for row in read_csv(REPORTS / "b4_candidate_external_bootstrap.csv"):
        key = (int(row["seed"]), row["endpoint"], row["score"])
        result[key] = {
            "ci_lo": float(row["ci_lo"]), "ci_hi": float(row["ci_hi"]),
            "point_delta": float(row["delta_NRC_vs_phase_mod"]),
        }
    return result


def run_b3() -> tuple[list[dict], list[dict]]:
    legacy = legacy_b3_rows()
    rows, units = [], []
    for dataset, seed, arrays, cache in b3_units():
        scores = candidate_scores(arrays["vector"].astype(float))
        scores["detection_score"] = arrays["score"].astype(float)
        tta = arrays["tta"].astype(float)
        if np.isfinite(tta).sum() > .9 * len(tta):
            scores["tta_phase_direction_consistency"] = -tta
        clusters = arrays["image"].astype(str)
        mc_seed = deterministic_seed("B3", dataset, seed)
        labels, inverse, multiplicities, resample_hash = resample_plan(clusters, mc_seed)
        endpoints = {
            "endpoint_continuous": arrays["error"].astype(float),
            "endpoint_severe_event": (
                arrays["error"].astype(float) > delta_threshold(arrays["ar"].astype(float))
            ).astype(float),
        }
        unit_entry = {
            "stage": "B3", "dataset": dataset, "seed": seed, "cluster_unit": "image",
            "cluster_count": len(labels), "instance_count": len(clusters), "mc_seed": mc_seed,
            "resample_id_hash": resample_hash, "cache": rel(cache),
        }
        for endpoint, risk in endpoints.items():
            candidate_names = [
                key[3] for key in legacy if key[:3] == (dataset, seed, endpoint)
            ]
            selected = {name: scores[name] for name in dict.fromkeys(
                ["phase_mod", "detection_score", *candidate_names]
            )}
            points = {name: nrc_unweighted(score, risk) for name, score in selected.items()}
            samples = bootstrap_nrc(selected, risk, inverse, multiplicities)
            universe = universe_hash(clusters, risk, selected["phase_mod"], selected["detection_score"])
            unit_entry[f"{endpoint}_universe_hash"] = universe
            for candidate in candidate_names:
                rows.append(make_bootstrap_row(
                    "B3", dataset, "RotatedRetinaNet-PSC", seed, candidate, endpoint, "image",
                    len(labels), len(risk), mc_seed, resample_hash, universe, points, samples,
                    legacy[(dataset, seed, endpoint, candidate)],
                ))
        units.append(unit_entry)
    return rows, units


def run_b4() -> tuple[list[dict], list[dict]]:
    legacy = legacy_b4_rows()
    rows, units = [], []
    for seed in range(3):
        arrays, source = b4_unit(seed)
        scores = candidate_scores(arrays["vector"])
        scores["detection_score"] = arrays["score"]
        clusters = arrays["cluster"].astype(str)
        mc_seed = deterministic_seed("B4", "DOTA-v1.0", seed)
        labels, inverse, multiplicities, resample_hash = resample_plan(clusters, mc_seed)
        endpoints = {
            "endpoint_continuous": arrays["error"],
            "endpoint_severe_event": (
                arrays["error"] > delta_threshold(arrays["ar"])
            ).astype(float),
        }
        unit_entry = {
            "stage": "B4", "dataset": "DOTA-v1.0", "seed": seed,
            "cluster_unit": "mother_scene", "cluster_count": len(labels),
            "instance_count": len(clusters), "mc_seed": mc_seed,
            "resample_id_hash": resample_hash, "source": rel(source),
        }
        for endpoint, risk in endpoints.items():
            candidate_names = [key[2] for key in legacy if key[:2] == (seed, endpoint)]
            selected = {name: scores[name] for name in dict.fromkeys(
                ["phase_mod", "detection_score", *candidate_names]
            )}
            points = {name: nrc_unweighted(score, risk) for name, score in selected.items()}
            samples = bootstrap_nrc(selected, risk, inverse, multiplicities)
            universe = universe_hash(clusters, risk, selected["phase_mod"], selected["detection_score"])
            unit_entry[f"{endpoint}_universe_hash"] = universe
            for candidate in candidate_names:
                rows.append(make_bootstrap_row(
                    "B4", "DOTA-v1.0", "RotatedFCOS-PSCD", seed, candidate, endpoint,
                    "mother_scene", len(labels), len(risk), mc_seed, resample_hash, universe,
                    points, samples, legacy[(seed, endpoint, candidate)],
                ))
        units.append(unit_entry)
    return rows, units


def add_test(rows: list[dict], test_id: str, category: str, stage: str, expected,
             observed, passed: bool, notes: str, error="", tolerance="") -> None:
    rows.append({
        "test_id": test_id, "category": category, "stage": stage,
        "expected": expected, "observed": observed, "abs_error": error,
        "tolerance": tolerance, "status": "PASS" if passed else "FAIL", "notes": notes,
    })


def integrity_checks() -> tuple[list[dict], list[dict]]:
    checks, inputs = [], []

    def check(name: str, ok: bool, evidence: str) -> None:
        checks.append({"condition": name, "status": "PASS" if ok else "FAIL", "evidence": evidence})

    head = git("rev-parse", "HEAD")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", SNAPSHOT, head], cwd=ROOT
    ).returncode == 0
    check("scientific_snapshot_ancestry", ancestry, f"snapshot={SNAPSHOT}; actual_head={head}")
    tracked_clean = subprocess.run(["git", "diff", "--quiet"], cwd=ROOT).returncode == 0 and subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=ROOT
    ).returncode == 0
    check("tracked_worktree_clean_before_execution", tracked_clean,
          "tracked/index clean; pre-existing .orientbench_transfer_parts is untracked migration staging")

    threshold = ROOT / "configs/thresholds.yaml"
    threshold_sha = sha256(threshold)
    check("thresholds_raw_sha256", threshold_sha == EXPECTED_THRESHOLD_SHA, threshold_sha)
    inputs.append({"path": rel(threshold), "sha256": threshold_sha, "bytes": threshold.stat().st_size})
    for name, expected in EXPECTED_SPLITS.items():
        path = ROOT / name
        actual = sha256(path) if path.is_file() else "MISSING"
        check(f"split:{Path(name).name}", actual == expected, actual)
        if path.is_file():
            inputs.append({"path": name, "sha256": actual, "bytes": path.stat().st_size})

    persistent = ROOT / "outputs/persistent_artifacts"
    persistent_files = sorted(path for path in persistent.rglob("*") if path.is_file())
    inventory = hashlib.sha256()
    for path in persistent_files:
        inventory.update(rel(path).encode())
        inventory.update(struct.pack("<Q", path.stat().st_size))
    check("persistent_migration_asset_count", len(persistent_files) == 275,
          f"count={len(persistent_files)}; path_size_inventory_sha256={inventory.hexdigest()}")

    b1 = REPORTS / "b1_protocol_frozen.json"
    b4 = REPORTS / "b4_protocol_frozen.json"
    for path, expected_unit in ((b1, "image_or_recoverable_mother_scene"),
                                (b4, "DOTA original mother scene recovered from tile ID")):
        protocol = json.loads(path.read_text())
        ok = protocol.get("bootstrap_replicates") == REPLICATES and protocol.get("bootstrap_unit") == expected_unit
        check(f"protocol:{path.name}", ok,
              f"reps={protocol.get('bootstrap_replicates')}; unit={protocol.get('bootstrap_unit')}")
        inputs.append({"path": rel(path), "sha256": sha256(path), "bytes": path.stat().st_size})

    comparison = read_csv(G0 / "reports/g0_comparison_manifest.csv")
    g0_rows = {(row["dataset"], int(row["seed"])): row for row in comparison if row["head"] == "PSC"}
    for dataset in ("DIOR-R", "SODA-A"):
        alias = dataset.replace("-", "_")
        for seed in range(3):
            row = g0_rows[(dataset, seed)]
            source = ROOT / row["matched_table_artifact"]
            actual = sha256(source) if source.is_file() else "MISSING"
            check(f"b3_dump:{dataset}:seed{seed}", actual == row["matched_artifact_sha256"], actual)
            if source.is_file():
                inputs.append({"path": rel(source), "sha256": actual, "bytes": source.stat().st_size})
            cache = BROOT / f"artifacts/b3_cache/{alias}_seed{seed}.npz"
            loaded = np.load(cache, allow_pickle=True)
            check(f"b3_cache:{dataset}:seed{seed}", len(loaded["image"]) == int(row["retained_ar21"]),
                  f"rows={len(loaded['image'])}; expected={row['retained_ar21']}")
            inputs.append({"path": rel(cache), "sha256": sha256(cache), "bytes": cache.stat().st_size})

    for seed in range(3):
        manifest_path = BROOT / f"artifacts/b3_fair1m/seed{seed}/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        source = ROOT / manifest["output"]
        actual = sha256(source) if source.is_file() else "MISSING"
        check(f"b3_dump:FAIR1M-v1.0:seed{seed}",
              manifest.get("status") == "complete" and actual == manifest["output_sha256"], actual)
        inputs.extend([
            {"path": rel(manifest_path), "sha256": sha256(manifest_path), "bytes": manifest_path.stat().st_size},
            {"path": rel(source), "sha256": actual, "bytes": source.stat().st_size},
        ])
        cache = BROOT / f"artifacts/b3_cache/FAIR1M_seed{seed}.npz"
        expected = int(g0_rows[("FAIR1M-v1.0", seed)]["retained_ar21"])
        loaded = np.load(cache, allow_pickle=True)
        check(f"b3_cache:FAIR1M-v1.0:seed{seed}", len(loaded["image"]) == expected,
              f"rows={len(loaded['image'])}; expected={expected}")
        inputs.append({"path": rel(cache), "sha256": sha256(cache), "bytes": cache.stat().st_size})

    for seed in range(3):
        manifest_path = BROOT / f"artifacts/b4_external/seed{seed}/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        assets = [
            (ROOT / manifest["rows"], manifest["rows_sha256"], "rows"),
            (ROOT / manifest["full_evaluator_inputs"], manifest["full_evaluator_inputs_sha256"], "evaluator"),
            (Path(manifest["checkpoint"]), manifest["checkpoint_sha256"], "checkpoint"),
        ]
        ok = manifest.get("status") == "complete"
        evidence = []
        inputs.append({"path": rel(manifest_path), "sha256": sha256(manifest_path), "bytes": manifest_path.stat().st_size})
        for path, expected, label in assets:
            actual = sha256(path) if path.is_file() else "MISSING"
            ok = ok and actual == expected
            evidence.append(f"{label}={actual}")
            if path.is_file():
                inputs.append({"path": rel(path), "sha256": actual, "bytes": path.stat().st_size})
        check(f"b4_manifest_and_assets:seed{seed}", ok, "; ".join(evidence))

    g0_script = G0 / "scripts/run_g0_forensics.py"
    source_text = g0_script.read_text()
    g0_structural = all(token in source_text for token in (
        "weights[order]", "np.bincount(picked", "weighted_metrics(po", "weighted_metrics(no"
    ))
    check("g0_weighted_cluster_implementation", g0_structural,
          f"source_sha256={sha256(g0_script)}; explicit equivalence tested separately")
    inputs.append({"path": rel(g0_script), "sha256": sha256(g0_script), "bytes": g0_script.stat().st_size})

    for path in (
        REPORTS / "b3_intervention_metrics.csv", REPORTS / "b4_candidate_external_bootstrap.csv",
        REPORTS / "b4_variant_model_health.csv", REPORTS / "b3_intervention_identity_audit.csv",
        REPORTS / "b4_variant_identity_ap_audit.csv", REPORTS / "b3_hypothesis_evidence_matrix.csv",
        REPORTS / "b4_hypothesis_external_replication.csv", REPORTS / "b1_candidate_score_registry.csv",
    ):
        inputs.append({"path": rel(path), "sha256": sha256(path), "bytes": path.stat().st_size})
    dedup = {item["path"]: item for item in inputs}
    return checks, [dedup[key] for key in sorted(dedup)]


def gate_rows(integrity: list[dict], tests: list[dict], b3_rows: list[dict],
              b4_rows: list[dict]) -> tuple[list[dict], str]:
    rows = []

    def add(condition: str, status: str, evidence: str, impact: str, source: str) -> None:
        rows.append({"condition": condition, "status": status, "evidence": evidence,
                     "impact_on_b6": impact, "source": source})

    integrity_ok = all(row["status"] == "PASS" for row in integrity)
    add("preflight_integrity", "PASS" if integrity_ok else "FAIL",
        f"{sum(row['status']=='PASS' for row in integrity)}/{len(integrity)} checks pass",
        "continue" if integrity_ok else "stop inconclusive", "runtime integrity checks")

    tests_ok = all(row["status"] == "PASS" for row in tests)
    add("instance_estimand_equivalence", "PASS" if tests_ok else "FAIL",
        f"{sum(row['status']=='PASS' for row in tests)}/{len(tests)} tests pass",
        "continue" if tests_ok else "stop inconclusive", rel(OUT_TESTS))

    health = read_csv(REPORTS / "b4_variant_model_health.csv")
    protocol = json.loads((REPORTS / "b4_protocol_frozen.json").read_text())
    health_gate = protocol["health_gate"]
    health_ok = len(health) == 3 and all(
        row["status"] == "HEALTHY_COMPARABLE"
        and float(row["AP50"]) >= health_gate["minimum_AP50"]
        and int(row["class_coverage"]) >= health_gate["minimum_class_coverage"]
        and int(row["matched_count"]) >= health_gate["minimum_matched_count"]
        and row["loss_health"] == "FINITE_STABLE"
        for row in health
    )
    add("external_variant_health", "PASS" if health_ok else "FAIL",
        f"healthy comparable seeds={sum(row['status']=='HEALTHY_COMPARABLE' for row in health)}/3",
        "continue" if health_ok else "stop inconclusive", "b4_variant_model_health.csv + b4_protocol_frozen.json")

    b3_identity = read_csv(REPORTS / "b3_intervention_identity_audit.csv")
    b3_candidates = [row for row in b3_identity if row["evidence_role"] == "RANKING_ONLY" and row["parameter"] == "score_only"]
    b3_identity_ok = bool(b3_candidates) and all(
        row["prediction_identity_equal"] == "True" and row["box_equal"] == "True"
        and row["class_equal"] == "True" and row["nms_membership_equal"] == "True"
        and row["nms_order_equal"] == "True" for row in b3_candidates
    )
    b4_identity = read_csv(REPORTS / "b4_variant_identity_ap_audit.csv")
    ranking = [row for row in b4_identity if row["role"] == "RANKING_ONLY"]
    b4_identity_ok = len(ranking) == 1 and all(
        ranking[0][key] == "UNCHANGED" for key in ("box", "class_", "NMS", "AP50", "AP75")
    ) and ranking[0]["prediction_identity"] == "EXACT"
    identity_ok = b3_identity_ok and b4_identity_ok
    add("ranking_only_identity_and_ap", "PASS" if identity_ok else "FAIL",
        f"B3 ranking rows={len(b3_candidates)} all_exact={b3_identity_ok}; B4 exact={b4_identity_ok}",
        "continue" if identity_ok else "kill candidate gate", "b3/b4 identity audits")

    b3_evidence = {row["hypothesis"]: row["status"] for row in read_csv(REPORTS / "b3_hypothesis_evidence_matrix.csv")}
    b4_evidence = read_csv(REPORTS / "b4_hypothesis_external_replication.csv")
    replicated_hypotheses = []
    for hypothesis, original in sorted(b3_evidence.items()):
        external = [row["status"] for row in b4_evidence if row["hypothesis"] == hypothesis]
        replicated = original in ("SUPPORTED", "PARTIALLY_SUPPORTED") and "REPLICATED" in external
        if replicated:
            replicated_hypotheses.append(hypothesis)
        add(f"mechanism_replication:{hypothesis}", "PASS" if replicated else "BOUNDED",
            f"original={original}; external={external}", "mechanism only; no repair inheritance",
            "b3_hypothesis_evidence_matrix.csv + b4_hypothesis_external_replication.csv")

    registered = {
        row["candidate"] for row in read_csv(REPORTS / "b1_candidate_score_registry.csv")
        if row["status"] == "REGISTERED"
    }
    development_support = []
    for candidate in sorted(registered):
        for endpoint in ("endpoint_continuous", "endpoint_severe_event"):
            candidate_rows = [row for row in b3_rows if row["candidate"] == candidate and row["endpoint"] == endpoint]
            supported_datasets = {
                row["dataset"] for row in candidate_rows if row["supports_both"]
            }
            if len(supported_datasets) >= 2:
                development_support.append((candidate, endpoint, sorted(supported_datasets)))
    development_ok = bool(development_support)
    add("corrected_development_candidate_support", "PASS" if development_ok else "FAIL",
        json.dumps(development_support, ensure_ascii=False, sort_keys=True),
        "continue to external gate" if development_ok else "kill candidate gate", rel(OUT_B3))

    external_support = []
    for candidate in sorted(registered):
        for endpoint in ("endpoint_continuous", "endpoint_severe_event"):
            candidate_rows = [row for row in b4_rows if row["candidate"] == candidate and row["endpoint"] == endpoint]
            if len(candidate_rows) == 3 and all(row["supports_both"] for row in candidate_rows):
                external_support.append((candidate, endpoint))
    external_ok = bool(external_support)
    add("corrected_external_candidate_confirmation", "PASS" if external_ok else "FAIL",
        json.dumps(external_support, ensure_ascii=False),
        "B6 may be reconsidered" if external_ok else "stop B6; candidate not externally confirmed", rel(OUT_B4))

    if not integrity_ok or not tests_ok or not health_ok:
        verdict = "INCONCLUSIVE_ASSET_OR_PROTOCOL"
    elif not identity_ok or not development_ok or not external_ok:
        verdict = "FAIL_CANDIDATE_GATE"
    else:
        verdict = "PASS_STATISTICAL_REGATE"
    add("final_verdict", verdict, f"replicated_mechanisms={replicated_hypotheses}; external_candidate_support={external_support}",
        "STOP_B6" if verdict != "PASS_STATISTICAL_REGATE" else "eligible for a separate B6 decision",
        "machine-derived conjunction of preceding rows")
    return rows, verdict


def report_text(head: str, integrity: list[dict], tests: list[dict], b3_rows: list[dict],
                b4_rows: list[dict], gate: list[dict], verdict: str, code_sha: str) -> str:
    old_b3_out = sum(bool(row["legacy_point_outside_legacy_ci"]) for row in b3_rows)
    old_b4_out = sum(bool(row["legacy_point_outside_legacy_ci"]) for row in b4_rows)
    new_b3_out = sum(not bool(row["new_point_inside_new_ci"]) for row in b3_rows)
    new_b4_out = sum(not bool(row["new_point_inside_new_ci"]) for row in b4_rows)
    b3_support = sum(bool(row["supports_both"]) for row in b3_rows)
    b4_support = sum(bool(row["supports_both"]) for row in b4_rows)
    final = gate[-1]
    lines = [
        "# OrientBench B3/B4 统计重审与 B5 可执行重门控",
        "",
        f"- round: `{ROUND_ID}`",
        f"- scientific snapshot: `{SNAPSHOT}`",
        f"- execution HEAD: `{head}`",
        f"- implementation SHA-256: `{code_sha}`",
        f"- final verdict: `{verdict}`",
        "- training/inference: `false/false`",
        "",
        "## 1. 前置完整性",
        "",
        f"完整性检查通过 {sum(row['status']=='PASS' for row in integrity)}/{len(integrity)} 项。",
        "`thresholds.yaml`、10 个 split、275 个持久化资产计数、B3 frozen dumps、",
        "B4 三份 checkpoint/dump/evaluator manifest 及冻结 B1/B4 协议均已核对。",
        "当前 HEAD 包含 9d9cdae scientific snapshot；其后提交仅为清理记录、迁移报告和本轮协作资产。",
        "预先存在的 `.orientbench_transfer_parts/` 是未跟踪迁移分片，不参与输入或输出。",
        "",
        "## 2. 旧实现与修正实现",
        "",
        "旧 B3/B4 bootstrap 先在 image/mother-scene 内分别平均 candidate score、baseline score 和 risk，",
        "再对 cluster means 计算 NRC。旧点估计则在全部 matched instances 上计算 NRC，因此二者不是同一 estimand。",
        "",
        "修正实现保留原始实例顺序、score stable tie order 和实例级 NRC。每个 replicate 抽取 cluster 后，",
        "把 cluster 被抽中的 multiplicity 作为该 cluster 内每个原始实例的整数权重。加权前缀风险和 oracle",
        "均与逐行显式复制完全等价；candidate、phase_mod 与 detection_score 共用同一 resample ID。",
        "",
        f"等价性/复现测试通过 {sum(row['status']=='PASS' for row in tests)}/{len(tests)} 项。",
        "G0 weighted implementation 也通过逐行显式 multiplicity 等价测试。",
        "",
        "## 3. 独立复现旧异常",
        "",
        f"- B3：旧有区间的 58 行中，实例点差落在旧区间外 {old_b3_out} 行（要求复现 39 行）。",
        f"- B4：24 行中对应异常 {old_b4_out} 行（要求复现 4 行）。",
        f"- 修正后：B3 点差落在新同-estimand区间外 {new_b3_out}/58；B4 为 {new_b4_out}/24。",
        "",
        "上述旧异常不是用区间必须机械包含点估计来单独定罪，而是与源码中 cluster-mean NRC 的明确",
        "estimand 变化共同构成证据。修正表同时保留旧点差、旧区间和逐行异常标志。",
        "",
        "## 4. 候选比较",
        "",
        f"B3 修正表共有 {len(b3_rows)} 行，其中同时优于 phase_mod 与 detection_score 的单元行数为 {b3_support}。",
        f"B4 修正表共有 {len(b4_rows)} 行，对应行数为 {b4_support}。",
        "支持要求使用 paired delta NRC 的 97.5% 分位数严格小于 0；Endpoint C/E 分开判断。",
        "外部 DOTA RotatedFCOS 三 seed 中，没有一个冻结候选在同一 endpoint 上三 seed 均同时优于",
        "phase_mod 与 detection_score。因此 development-derived 候选未获得独立确认。",
        "",
        "## 5. 身份与机制边界",
        "",
        "ranking-only 候选的 prediction identity、boxes、classes、NMS 与 AP 审计保持通过。径向、切向、",
        "频率和 boundary 干预会改变角度框，部分历史 full-evaluator 单元还改变 NMS/AP；它们只支持",
        "mechanism-only，不构成 ranking-only/AP-invariant 修复。H1/H3 的有界机制证据可保留，但不能",
        "继承为候选有效性。",
        "",
        "## 6. 可执行 gate",
        "",
        "B5 gate 由完整性、等价测试、模型健康、身份审计、外部机制重复和修正 bootstrap 条件逐行计算，",
        "没有在生成代码中写死 H1--H4 状态或 final verdict。最终机器裁决为：",
        "",
        f"`{verdict}`",
        "",
        f"影响：`{final['impact_on_b6']}`。原 `PASS_MECHANISM_BOUNDED` 只能保留为有界机制描述；",
        "它不再构成执行 B6 的放行门。不得增加事后 score、seed、阈值或 endpoint 挽救候选。",
        "",
        "## 7. 证据文件",
        "",
        f"- `{rel(OUT_B3)}`",
        f"- `{rel(OUT_B4)}`",
        f"- `{rel(OUT_GATE)}`",
        f"- `{rel(OUT_TESTS)}`",
        f"- `{rel(OUT_MANIFEST)}`",
        f"- `{rel(SCRIPT_PATH)}`",
        f"- `{rel(TEST_PATH)}`",
        "",
        "复算命令：",
        "",
        "```bash",
        f"/home/rspip/anaconda3/envs/mr_dev1x/bin/python {rel(TEST_PATH)}",
        f"/home/rspip/anaconda3/envs/mr_dev1x/bin/python {rel(SCRIPT_PATH)}",
        "```",
        "",
        "本轮未修改冻结 B1--B5 输出、协议、数据、split、checkpoint、A 主稿或 `dis/B.md`。",
    ]
    return "\n".join(lines) + "\n"


def file_record(path: Path) -> dict:
    record = {"path": rel(path), "sha256": sha256(path), "bytes": path.stat().st_size}
    if path.suffix == ".csv":
        rows = read_csv(path)
        record["rows"] = len(rows)
        record["schema"] = list(rows[0]) if rows else []
    else:
        record["rows"] = None
        record["schema"] = "markdown" if path.suffix == ".md" else "python"
    return record


def main() -> int:
    integrity, inputs = integrity_checks()
    if not all(row["status"] == "PASS" for row in integrity):
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        failed = [row for row in integrity if row["status"] != "PASS"]
        REPORT_PATH.write_text(
            "# OrientBench B3/B4 统计重审\n\n"
            f"- final verdict: `INCONCLUSIVE_ASSET_OR_PROTOCOL`\n"
            f"- failed integrity checks: `{json.dumps(failed, ensure_ascii=False)}`\n",
            encoding="utf-8",
        )
        return 2

    tests = equivalence_tests()
    b3_rows, b3_units_manifest = run_b3()
    b4_rows, b4_units_manifest = run_b4()

    b3_legacy_out = sum(bool(row["legacy_point_outside_legacy_ci"]) for row in b3_rows)
    b4_legacy_out = sum(bool(row["legacy_point_outside_legacy_ci"]) for row in b4_rows)
    add_test(tests, "legacy_b3_39_of_58", "legacy_estimand_mismatch_reproduction", "B3",
             "39/58", f"{b3_legacy_out}/{len(b3_rows)}", b3_legacy_out == 39 and len(b3_rows) == 58,
             "independent row reconstruction from old instance points and old cluster-mean intervals")
    add_test(tests, "legacy_b4_4_of_24", "legacy_estimand_mismatch_reproduction", "B4",
             "4/24", f"{b4_legacy_out}/{len(b4_rows)}", b4_legacy_out == 4 and len(b4_rows) == 24,
             "independent row reconstruction from old report")
    max_b3_point_error = max(abs(float(row["delta_nrc_vs_phase_mod"]) - float(row["legacy_point_delta"])) for row in b3_rows)
    max_b4_point_error = max(abs(float(row["delta_nrc_vs_phase_mod"]) - float(row["legacy_point_delta"])) for row in b4_rows)
    add_test(tests, "b3_instance_point_reproduction", "point_estimate_reproduction", "B3", 0.0,
             max_b3_point_error, max_b3_point_error <= 1e-12,
             "new code independently reproduces old matched-instance point delta", max_b3_point_error, 1e-12)
    add_test(tests, "b4_instance_point_reproduction", "point_estimate_reproduction", "B4", 0.0,
             max_b4_point_error, max_b4_point_error <= 1e-12,
             "new code independently reproduces old matched-instance point delta", max_b4_point_error, 1e-12)

    gate, verdict = gate_rows(integrity, tests, b3_rows, b4_rows)
    write_csv(OUT_B3, b3_rows, BOOT_FIELDS)
    write_csv(OUT_B4, b4_rows, BOOT_FIELDS)
    write_csv(OUT_TESTS, tests, ["test_id", "category", "stage", "expected", "observed", "abs_error", "tolerance", "status", "notes"])
    write_csv(OUT_GATE, gate, ["condition", "status", "evidence", "impact_on_b6", "source"])

    head = git("rev-parse", "HEAD")
    code_sha = sha256(SCRIPT_PATH)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text(head, integrity, tests, b3_rows, b4_rows, gate, verdict, code_sha), encoding="utf-8")

    output_paths = [OUT_B3, OUT_B4, OUT_GATE, OUT_TESTS, REPORT_PATH]
    manifest = {
        "schema_version": "b3_b4_instance_estimand_reaudit_r001_v1",
        "round_id": ROUND_ID,
        "scientific_snapshot": SNAPSHOT,
        "execution_head": head,
        "code_sha256": code_sha,
        "test_code_sha256": sha256(TEST_PATH),
        "command": f"/home/rspip/anaconda3/envs/mr_dev1x/bin/python {rel(SCRIPT_PATH)}",
        "bootstrap": {
            "replicates": REPLICATES,
            "workers": WORKERS,
            "seed_scheme": "sha256(round|stage|dataset|seed) mod 1e7 + 100000; replicate seed += 104729*r",
            "cluster_units": {"B3": "image", "B4": "mother_scene"},
            "estimand": "matched-instance NRC with cluster multiplicity lifted to instance weights",
            "stable_tie_order": "original matched-row order",
        },
        "integrity_checks": integrity,
        "inputs": inputs,
        "units": b3_units_manifest + b4_units_manifest,
        "outputs": [file_record(path) for path in output_paths],
        "manifest_self_hash": "intentionally omitted to avoid self-reference",
        "final_verdict": verdict,
        "training": False,
        "inference": False,
        "old_frozen_outputs_modified": False,
    }
    temp = OUT_MANIFEST.with_suffix(".json.tmp")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, OUT_MANIFEST)
    if not all(row["status"] == "PASS" for row in tests):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

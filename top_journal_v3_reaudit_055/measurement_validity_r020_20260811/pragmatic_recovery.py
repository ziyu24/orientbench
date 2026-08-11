#!/usr/bin/env python3
"""User-authorized pragmatic recovery of the r020 measurement-validity analysis.

This script intentionally does not upgrade the consumed formal r020 receipt.  It
reuses only the frozen 26 scientific inputs, excludes learned EQS, and emits a
standalone recovery evidence bundle for supervisor adjudication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import os
import resource
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
M069 = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
R014 = ROOT / "outputs/persistent_artifacts/orientbench_r014"
DELTA_PATH = ROOT / "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json"
SEED = 20260809
UNITS = {
    "A": ("DIOR-R", "PSC"),
    "B": ("DIOR-R", "Oriented R-CNN"),
    "C": ("DIOR-R", "RTMDet"),
    "D": ("FAIR1M", "PSC"),
    "E": ("SODA-A", "PSC"),
    "F": ("SODA-A", "Oriented R-CNN"),
}
DATASET_INDEX = {"DIOR-R": 0, "FAIR1M": 1, "SODA-A": 2}
DATASET_UNITS = {d: [u for u, (ds, _) in UNITS.items() if ds == d] for d in DATASET_INDEX}
PROBES = ("raw_confidence", "linear_source_frozen", "tta_angle", "tta_localization")
CONTRASTS = PROBES[1:]
ENDPOINTS = ("AUGRC", "Risk@70", "Risk@90")
ABLATIONS = (
    "NO_LONGSIDE_AR21",
    "NO_GEONORM_AR21",
    "NORMALIZED_ALL_AR",
    "NORMALIZED_AR16",
    "NORMALIZED_AR13",
)
COHORTS = ("MAIN",) + ABLATIONS
EFFECT_CLASS = {
    "NO_LONGSIDE_AR21": "ANGLE_EQUIVALENCE",
    "NO_GEONORM_AR21": "GEOMETRY_NORMALIZATION",
    "NORMALIZED_ALL_AR": "AR_DOMAIN",
    "NORMALIZED_AR16": "AR_DOMAIN",
    "NORMALIZED_AR13": "AR_DOMAIN",
}
EXPECTED = {
    "outputs/persistent_artifacts/m069_fullval_reliability/A/image_universe.csv": (1658312, "3f1d2ef764c3f6e383e2b9e6285ed947a26f25b9707104bd8d9fb875408d4b0d"),
    "outputs/persistent_artifacts/m069_fullval_reliability/A/matched_fullval.jsonl": (133273156, "00e554fbc45dfd6ab0d964800920e101411bc2ee1e218f575a0eafcfde63761e"),
    "outputs/persistent_artifacts/m069_fullval_reliability/B/image_universe.csv": (1652313, "644ccaa922986d3597049680924a63555975e8a61f8ac26fccf744ff41c5edee"),
    "outputs/persistent_artifacts/m069_fullval_reliability/B/matched_fullval.jsonl": (132369719, "e1772d642990fb45ee00d31a2cc62b8fd468d0e1a99e009e0430e91e51082513"),
    "outputs/persistent_artifacts/m069_fullval_reliability/C/image_universe.csv": (1655606, "52c04690d415a66b59ff9d30d58f97ae836d71d62e543c8e278b707d4565bc77"),
    "outputs/persistent_artifacts/m069_fullval_reliability/C/matched_fullval.jsonl": (132382835, "91d4b372e5340a4849af680d82a3973be0999b2778e89375116067fa6009ea2e"),
    "outputs/persistent_artifacts/m069_fullval_reliability/D/image_universe.csv": (719167, "5cec906c601469dff58a2e6a26293d54613cc7f162c458f6a5abde0cb0f76586"),
    "outputs/persistent_artifacts/m069_fullval_reliability/D/matched_fullval.jsonl": (86428641, "fe2c0b3690e12793f898c0c7a5ce100806567e39f4b3671e9b1e2af5fb8c3bbf"),
    "outputs/persistent_artifacts/m069_fullval_reliability/E/image_universe.csv": (3348604, "75f874fff653e64460d6c91ce0dd07637ad68b55532976fbdca1bd01a4f8b131"),
    "outputs/persistent_artifacts/m069_fullval_reliability/E/matched_fullval.jsonl": (482776147, "337470223fae218aa2969ae8f974a447e6666d22f02830a7a933ea3dadbd72c9"),
    "outputs/persistent_artifacts/m069_fullval_reliability/F/image_universe.csv": (3340530, "0ce7cc5f4d56aceef57faaa85b09115309b961d4e663484ac893731330eef95c"),
    "outputs/persistent_artifacts/m069_fullval_reliability/F/matched_fullval.jsonl": (528736628, "dd7f37b067a569541140a1bad49bf6ae3a5aea7b0f9eff031ef3fe9a9a2c723f"),
    "outputs/persistent_artifacts/orientbench_r014/features/A.parquet": (106414303, "1680039b73ea6419143621ac5776713f2232b1f1bca953d22ba452dae3990800"),
    "outputs/persistent_artifacts/orientbench_r014/features/B.parquet": (76778217, "a4a56429d092ae5f2b99eae5bdbad6033b2bc1d3e9db3cd205534903ccdbabb5"),
    "outputs/persistent_artifacts/orientbench_r014/features/C.parquet": (90348339, "79b8b9299b7e758bbad663f4a55e94eaca186de14337212f8f1542c02fd38e44"),
    "outputs/persistent_artifacts/orientbench_r014/features/D.parquet": (56298120, "3d88592b74e3b6ee51515ab530c9020f07518f26ca74c69a84b90ca408d104af"),
    "outputs/persistent_artifacts/orientbench_r014/features/E.parquet": (235374169, "00e690cd03d5ff00cdd73b87a0c0bec1ad0d1e22889c2da3693975f203252f0b"),
    "outputs/persistent_artifacts/orientbench_r014/features/F.parquet": (161849746, "c3875f572b6c909b39ab4b5797d60963cf097969aca9ca4eb68a3f50c2caad75"),
    "outputs/persistent_artifacts/orientbench_r014/scores/A.parquet": (14113964, "65a38d8dc6e8818f459cb248a9cf90949157010dce2bb11469f5f5b5c161181a"),
    "outputs/persistent_artifacts/orientbench_r014/scores/B.parquet": (5147240, "a7b16608a3495d466de005e998e8ee83803d35bc0222c6c2b398caac9c3b4285"),
    "outputs/persistent_artifacts/orientbench_r014/scores/C.parquet": (9067953, "1724d7bda74542d6f4b02d1ea29e9e1eb19a3880a4c3c2b826acbbeab74e9d67"),
    "outputs/persistent_artifacts/orientbench_r014/scores/D.parquet": (11574260, "1807dc207596f2a26aaee992dd96efd972da36f4bcf7ce82edf1a434c83c8d4a"),
    "outputs/persistent_artifacts/orientbench_r014/scores/E.parquet": (40344077, "e3ef91a92370cbd3cfd2e76fae46f430c8024b73ec9dd56e64c274c531d3e4bd"),
    "outputs/persistent_artifacts/orientbench_r014/scores/F.parquet": (19765066, "fa27f7fed94c410d8bd27a106e96587d6b330d1c38e3f4f0c10986ee3f2367db"),
    "outputs/persistent_artifacts/orientbench_r014/soda_tile_to_mother_r014.csv": (1418786, "7bf9cc5698b0af2796fbb990e387603f3284231e541b1d711fd35c576e8b787f"),
    "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json": (12986, "80d86a5f72e70405fe4a49db87aad61e6aea20a26af0ad1c5745bfd646d1e5cb"),
}


@dataclass
class Prepared:
    unit: str
    dataset: str
    cohort: str
    risk: np.ndarray
    cluster_idx: np.ndarray
    scores: dict[str, np.ndarray]


G_PREPARED: dict[tuple[str, str], Prepared] = {}
G_MULTS: dict[str, np.ndarray] = {}
G_REPLICATES = 0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utf8_sorted(values) -> list[str]:
    return sorted({str(x) for x in values}, key=lambda x: x.encode("utf-8"))


def periodic_error(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(np.mod(a - b, 180.0))
    return np.minimum(d, 180.0 - d)


def obb_values(obb: dict) -> tuple[float, float, float]:
    return float(obb["obb_w"]), float(obb["obb_h"]), math.degrees(float(obb["obb_theta"]))


def longside_angle(w: float, h: float, theta_deg: float) -> float:
    return (theta_deg + (90.0 if h > w else 0.0)) % 180.0


def delta_function(delta_doc: dict):
    pairs = [(float(a), float(d)) for a, d in zip(delta_doc["ar"], delta_doc["dtheta_075"]) if d is not None and np.isfinite(d)]
    pairs.sort(key=lambda x: x[0])
    ar = np.array([x[0] for x in pairs], dtype=np.float64)
    dt = np.array([x[1] for x in pairs], dtype=np.float64)
    if not np.all(np.diff(ar) > 0):
        raise RuntimeError("delta AR grid is not strictly increasing")
    tol = float(delta_doc["solve_tolerance_deg"])
    if tol != 0.001:
        raise RuntimeError("unexpected solve tolerance")
    tail = min(a * d for a, d in pairs if a >= max(8.0, ar[-1] / 2.0))

    def evaluate(x):
        x = np.asarray(x, dtype=np.float64)
        out = np.interp(x, ar, dt)
        out = np.where(x < ar[0], np.inf, out)
        out = np.where(x > ar[-1], np.maximum(0.0, tail / x - 2.0 * tol), out)
        return out

    return evaluate


def metrics_sorted(score: np.ndarray, risk: np.ndarray, weights: np.ndarray | None = None) -> tuple[float, float, float, float, float]:
    order = np.argsort(-score, kind="stable")
    s = score[order]
    r = risk[order]
    w = np.ones(len(order), dtype=np.float64) if weights is None else np.asarray(weights, dtype=np.float64)[order]
    total = float(w.sum())
    if not total > 0:
        raise RuntimeError("zero bootstrap mass")
    starts = np.r_[0, np.flatnonzero(s[1:] != s[:-1]) + 1]
    gc = np.add.reduceat(w, starts)
    gr = np.add.reduceat(w * r, starts)
    positive = gc > 0
    gc = gc[positive]
    gr = gr[positive]
    cc = np.cumsum(gc)
    cr = np.cumsum(gr)
    dcov = gc / total
    prev_grisk = np.r_[0.0, cr[:-1] / total]
    curr_grisk = cr / total
    augrc = float(np.sum(0.5 * (prev_grisk + curr_grisk) * dcov))
    results = []
    coverages = []
    for q in (0.70, 0.90):
        j = int(np.searchsorted(cc, q * total, side="left"))
        results.append(float(cr[j] / cc[j]))
        coverages.append(float(cc[j] / total))
    return augrc, results[0], results[1], coverages[0], coverages[1]


def accepted_set(score: np.ndarray, q: float) -> np.ndarray:
    order = np.argsort(-score, kind="stable")
    sorted_score = score[order]
    starts = np.r_[0, np.flatnonzero(sorted_score[1:] != sorted_score[:-1]) + 1]
    counts = np.diff(np.r_[starts, len(score)])
    j = int(np.searchsorted(np.cumsum(counts), q * len(score), side="left"))
    threshold = sorted_score[starts[j]]
    return score >= threshold


def swap_fraction(a: np.ndarray, b: np.ndarray) -> float:
    union = np.count_nonzero(a | b)
    return float(np.count_nonzero(a ^ b) / union) if union else 0.0


def load_and_join(unit: str, audit_ids: set[str], mother: dict[str, str], delta_eval, join_rows: list[dict]) -> pd.DataFrame:
    records = []
    seen = set()
    matched_path = M069 / unit / "matched_fullval.jsonl"
    with matched_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            rec = json.loads(line)
            image_id = str(rec["image_id"])
            pred_id = int(rec["pred_id"])
            key = (image_id, pred_id)
            if key in seen:
                raise RuntimeError(f"duplicate matched key {unit} {key}")
            seen.add(key)
            if image_id not in audit_ids:
                continue
            if rec.get("d_cal_daudit_split_flag") != "D_audit":
                raise RuntimeError(f"matched membership conflict {unit} {key}")
            pw, ph, pt = obb_values(rec["pred_obb"])
            gw, gh, gt = obb_values(rec["gt_obb"])
            if min(gw, gh) <= 0 or min(pw, ph) <= 0:
                raise RuntimeError(f"nonpositive OBB dimension {unit} {key}")
            pred_can = longside_angle(pw, ph, pt)
            gt_can = longside_angle(gw, gh, gt)
            e_can = float(periodic_error(np.array([pred_can]), np.array([gt_can]))[0])
            e_raw = float(periodic_error(np.array([pt]), np.array([gt]))[0])
            historical = float(rec["angle_error"])
            if not math.isclose(e_can, historical, abs_tol=1e-8, rel_tol=0.0):
                raise RuntimeError(f"historical angle mismatch {unit} {key}: {e_can} {historical}")
            ar = max(gw, gh) / min(gw, gh)
            records.append({
                "image_id": image_id,
                "pred_id": pred_id,
                "row_sequence": len(records),
                "ar": ar,
                "e_can": e_can,
                "e_raw": e_raw,
                "cluster": mother[image_id] if UNITS[unit][0] == "SODA-A" else image_id,
            })
    base = pd.DataFrame(records)
    if base.empty or base[["image_id", "pred_id"]].duplicated().any():
        raise RuntimeError(f"invalid base cohort {unit}")
    keys = pd.MultiIndex.from_frame(base[["image_id", "pred_id"]])
    feature_cols = ["image_id", "pred_id", "detection_score", "u_axis", "missing_fraction", "iou_loss"]
    score_cols = ["image_id", "pred_id", "detection_score", "score_ar_size_linear"]
    features = pd.read_parquet(R014 / f"features/{unit}.parquet", columns=feature_cols)
    scores = pd.read_parquet(R014 / f"scores/{unit}.parquet", columns=score_cols)
    for name, rhs in (("features", features), ("scores", scores)):
        rhs["image_id"] = rhs.image_id.astype(str)
        rhs["pred_id"] = rhs.pred_id.astype(np.int64)
        if rhs[["image_id", "pred_id"]].duplicated().any():
            raise RuntimeError(f"duplicate {name} full-table key {unit}")
    fidx = pd.MultiIndex.from_frame(features[["image_id", "pred_id"]])
    sidx = pd.MultiIndex.from_frame(scores[["image_id", "pred_id"]])
    fextra = fidx.difference(keys)
    sextra = sidx.difference(keys)
    fsemi = features[fidx.isin(keys)]
    ssemi = scores[sidx.isin(keys)]
    joined = base.merge(fsemi, on=["image_id", "pred_id"], how="left", validate="one_to_one", sort=False)
    joined = joined.merge(ssemi, on=["image_id", "pred_id"], how="left", validate="one_to_one", sort=False, suffixes=("_feature", "_score"))
    if len(joined) != len(base) or not np.array_equal(joined.row_sequence.to_numpy(), np.arange(len(base))):
        raise RuntimeError(f"join count/order changed {unit}")
    required = ["detection_score_feature", "detection_score_score", "score_ar_size_linear", "u_axis", "missing_fraction", "iou_loss"]
    if joined[required].isna().any().any() or not np.isfinite(joined[required].to_numpy(dtype=float)).all():
        raise RuntimeError(f"missing/nonfinite joined fields {unit}")
    if not np.array_equal(joined.detection_score_feature.to_numpy(), joined.detection_score_score.to_numpy()):
        raise RuntimeError(f"detection score mismatch {unit}")
    delta = delta_eval(joined.ar.to_numpy(dtype=float))
    joined["risk_main"] = np.clip(joined.e_can.to_numpy() / np.maximum(delta, 1.0), 0.0, 3.0) / 3.0
    joined["risk_raw_theta"] = np.clip(joined.e_raw.to_numpy() / np.maximum(delta, 1.0), 0.0, 3.0) / 3.0
    joined["risk_no_geonorm"] = np.clip(joined.e_can.to_numpy() / 90.0, 0.0, 1.0)
    joined["raw_confidence"] = joined.detection_score_feature
    joined["linear_source_frozen"] = joined.score_ar_size_linear
    joined["tta_angle"] = -joined.u_axis
    joined["tta_localization"] = -(joined.missing_fraction + joined.iou_loss)
    joined["S0_descriptive"] = -(joined.u_axis + joined.missing_fraction + joined.iou_loss)
    join_rows.append({
        "unit": unit,
        "base_rows": len(base),
        "feature_missing": int(len(keys.difference(fidx))),
        "score_missing": int(len(keys.difference(sidx))),
        "feature_extras": int(len(fextra)),
        "score_extras": int(len(sextra)),
        "key_sequence_sha256": hashlib.sha256("\n".join(f"{i}\t{p}" for i, p in keys).encode()).hexdigest(),
        "feature_extras_sha256": hashlib.sha256("\n".join(f"{i}\t{p}" for i, p in fextra).encode()).hexdigest(),
        "score_extras_sha256": hashlib.sha256("\n".join(f"{i}\t{p}" for i, p in sextra).encode()).hexdigest(),
    })
    return joined


def prepare_frame(unit: str, dataset: str, cohort: str, frame: pd.DataFrame, cluster_to_idx: dict[str, int]) -> Prepared:
    if cohort in ("MAIN", "NO_LONGSIDE_AR21", "NO_GEONORM_AR21"):
        mask = frame.ar.to_numpy() >= 2.1
    elif cohort == "NORMALIZED_ALL_AR":
        mask = np.ones(len(frame), dtype=bool)
    elif cohort == "NORMALIZED_AR16":
        mask = frame.ar.to_numpy() >= 1.6
    elif cohort == "NORMALIZED_AR13":
        mask = frame.ar.to_numpy() >= 1.3
    else:
        raise KeyError(cohort)
    selected = frame.loc[mask]
    if selected.empty:
        raise RuntimeError(f"empty cohort {unit} {cohort}")
    if cohort == "NO_LONGSIDE_AR21":
        risk = selected.risk_raw_theta.to_numpy(dtype=np.float64)
    elif cohort == "NO_GEONORM_AR21":
        risk = selected.risk_no_geonorm.to_numpy(dtype=np.float64)
    else:
        risk = selected.risk_main.to_numpy(dtype=np.float64)
    return Prepared(
        unit=unit,
        dataset=dataset,
        cohort=cohort,
        risk=risk,
        cluster_idx=np.array([cluster_to_idx[str(x)] for x in selected.cluster], dtype=np.int32),
        scores={p: selected[p].to_numpy(dtype=np.float64) for p in PROBES},
    )


def worker_init(prepared, mults, replicates):
    global G_PREPARED, G_MULTS, G_REPLICATES
    G_PREPARED = prepared
    G_MULTS = mults
    G_REPLICATES = replicates


def bootstrap_chunk(bounds: tuple[int, int]):
    start, end = bounds
    out = np.empty((end - start, len(UNITS), len(COHORTS), len(PROBES), len(ENDPOINTS)), dtype=np.float64)
    unit_index = {u: i for i, u in enumerate(UNITS)}
    for rr, replicate in enumerate(range(start, end)):
        for unit, (dataset, _) in UNITS.items():
            multiplicity = G_MULTS[dataset][replicate]
            ui = unit_index[unit]
            for ci, cohort in enumerate(COHORTS):
                prep = G_PREPARED[(unit, cohort)]
                weights = multiplicity[prep.cluster_idx]
                for pi, probe in enumerate(PROBES):
                    vals = metrics_sorted(prep.scores[probe], prep.risk, weights)
                    out[rr, ui, ci, pi, :] = vals[:3]
    return start, out


def quantile(a: np.ndarray, q: float) -> float:
    return float(np.quantile(a, q, method="linear"))


def holm(rows: list[dict]) -> None:
    ordered = sorted(range(len(rows)), key=lambda i: (rows[i]["p_raw"], rows[i]["hypothesis_key"]))
    running = 0.0
    m = len(rows)
    for rank, idx in enumerate(ordered, 1):
        running = max(running, min(1.0, (m - rank + 1) * rows[idx]["p_raw"]))
        rows[idx]["p_holm"] = running


def build_hypotheses(point, boot, swap, replicates: int):
    unit_index = {u: i for i, u in enumerate(UNITS)}
    dataset_index = {d: i for i, d in enumerate(DATASET_INDEX)}
    rows = []
    replicate_blocks = []
    for level in ("unit", "dataset"):
        keys = list(UNITS) if level == "unit" else list(DATASET_INDEX)
        for key in keys:
            ki = unit_index[key] if level == "unit" else dataset_index[key]
            for contrast in CONTRASTS:
                pi = PROBES.index(contrast)
                ri = PROBES.index("raw_confidence")
                for endpoint in ENDPOINTS:
                    ei = ENDPOINTS.index(endpoint)
                    for ablation in ABLATIONS:
                        ai = COHORTS.index(ablation)
                        main_probe = point[level][key]["MAIN"][contrast][endpoint]
                        main_raw = point[level][key]["MAIN"]["raw_confidence"][endpoint]
                        abl_probe = point[level][key][ablation][contrast][endpoint]
                        abl_raw = point[level][key][ablation]["raw_confidence"][endpoint]
                        delta_main = main_probe - main_raw
                        delta_ablation = abl_probe - abl_raw
                        dod = delta_main - delta_ablation
                        source = boot[level]
                        dmain_b = source[:, ki, COHORTS.index("MAIN"), pi, ei] - source[:, ki, COHORTS.index("MAIN"), ri, ei]
                        dabl_b = source[:, ki, ai, pi, ei] - source[:, ki, ai, ri, ei]
                        dod_b = dmain_b - dabl_b
                        eps_main = max(5e-4, 0.02 * max(abs(main_probe), abs(main_raw))) if endpoint == "AUGRC" else max(1e-3, 0.02 * max(abs(main_probe), abs(main_raw)))
                        eps_abl = max(5e-4, 0.02 * max(abs(abl_probe), abs(abl_raw))) if endpoint == "AUGRC" else max(1e-3, 0.02 * max(abs(abl_probe), abs(abl_raw)))
                        hkey = f"{level}|{key}|{contrast}|{endpoint}|{ablation}"
                        row = {
                            "level": level,
                            "key": key,
                            "contrast": contrast,
                            "endpoint": endpoint,
                            "ablation_id": ablation,
                            "effect_class": EFFECT_CLASS[ablation],
                            "hypothesis_key": hkey,
                            "main_probe": main_probe,
                            "main_raw": main_raw,
                            "ablation_probe": abl_probe,
                            "ablation_raw": abl_raw,
                            "delta_main": delta_main,
                            "delta_ablation": delta_ablation,
                            "dod": dod,
                            "epsilon_main": eps_main,
                            "epsilon_ablation": eps_abl,
                            "delta_main_ci_low": quantile(dmain_b, 0.025),
                            "delta_main_ci_high": quantile(dmain_b, 0.975),
                            "delta_ablation_ci_low": quantile(dabl_b, 0.025),
                            "delta_ablation_ci_high": quantile(dabl_b, 0.975),
                            "dod_ci_low": quantile(dod_b, 0.025),
                            "dod_ci_high": quantile(dod_b, 0.975),
                            "p_raw": float((1 + np.count_nonzero(np.abs(dod_b - dod) >= abs(dod))) / (replicates + 1)),
                            "main_swap70": swap[level][key]["MAIN"][contrast][0.70],
                            "main_swap90": swap[level][key]["MAIN"][contrast][0.90],
                            "ablation_swap70": swap[level][key][ablation][contrast][0.70],
                            "ablation_swap90": swap[level][key][ablation][contrast][0.90],
                        }
                        rows.append(row)
                        replicate_blocks.append(pd.DataFrame({
                            "hypothesis_key": hkey,
                            "replicate": np.arange(replicates, dtype=np.int32),
                            "delta_main": dmain_b,
                            "delta_ablation": dabl_b,
                            "dod": dod_b,
                        }))
        level_rows = [x for x in rows if x["level"] == level]
        holm(level_rows)
    for row in rows:
        if row["delta_main"] < 0 < row["delta_ablation"]:
            direction = "PROBE_BETTER_MAIN__RAW_BETTER_ABLATION"
            ci_ok = row["delta_main_ci_high"] < -row["epsilon_main"] and row["delta_ablation_ci_low"] > row["epsilon_ablation"]
        elif row["delta_ablation"] < 0 < row["delta_main"]:
            direction = "RAW_BETTER_MAIN__PROBE_BETTER_ABLATION"
            ci_ok = row["delta_main_ci_low"] > row["epsilon_main"] and row["delta_ablation_ci_high"] < -row["epsilon_ablation"]
        else:
            direction = "NONE"
            ci_ok = False
        swap_ok = True
        if row["endpoint"] == "Risk@70":
            swap_ok = row["main_swap70"] >= 0.05 and row["ablation_swap70"] >= 0.05
        elif row["endpoint"] == "Risk@90":
            swap_ok = row["main_swap90"] >= 0.05 and row["ablation_swap90"] >= 0.05
        row["supported_direction"] = direction
        row["witness"] = bool(
            ci_ok
            and row["p_holm"] < 0.05
            and (row["dod_ci_low"] > 0 or row["dod_ci_high"] < 0)
            and abs(row["dod"]) >= row["epsilon_main"] + row["epsilon_ablation"]
            and swap_ok
        )
        row["full_signature"] = "|".join((row["effect_class"], row["ablation_id"], row["contrast"], row["endpoint"], direction)) if row["witness"] else ""
    return pd.DataFrame(rows), pd.concat(replicate_blocks, ignore_index=True)


def candidate_gate(hypotheses: pd.DataFrame) -> tuple[str, dict]:
    witness = hypotheses[hypotheses.witness]
    unit = witness[witness.level == "unit"]
    dataset = witness[witness.level == "dataset"]
    if len(unit) == 0 and len(dataset) == 0:
        return "FAIL_GENERIC_OR_NULL", {"unit_witnesses": 0, "dataset_witnesses": 0, "passing_signatures": []}
    passing = []
    for signature in sorted(set(dataset.full_signature) & set(unit.full_signature)):
        ds = dataset[dataset.full_signature == signature]
        us = unit[unit.full_signature == signature]
        detectors = {UNITS[u][1] for u in us.key}
        if ds.key.nunique() >= 2 and us.key.nunique() >= 4 and len(detectors) >= 2 and "SODA-A" in set(ds.key) and any(u in {"E", "F"} for u in us.key):
            passing.append(signature)
    state = "PASS_TO_EXTERNAL_CONFIRMATION" if passing else "INCONCLUSIVE_MIXED"
    return state, {"unit_witnesses": int(len(unit)), "dataset_witnesses": int(len(dataset)), "passing_signatures": passing}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=10000)
    parser.add_argument("--workers", type=int, default=39)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    args.output.mkdir(parents=True, mode=0o750)
    started = time.time()
    affinity = sorted(os.sched_getaffinity(0))
    if len(affinity) != 48:
        raise SystemExit(f"recovery job requires 48-CPU task affinity, observed {len(affinity)}")
    protocol = {
        "schema": "orientbench-r020-pragmatic-recovery-v1",
        "formal_receipt_status": "CONSUMED_NOT_ADJUDICATED",
        "scientific_use": "RECOVERY_EVIDENCE_PENDING_SUPERVISOR_ADJUDICATION",
        "replicates": args.replicates,
        "workers": args.workers,
        "seed": SEED,
        "affinity": affinity,
        "learned_eqs_read": False,
        "threshold_or_split_changed": False,
    }
    (args.output / "protocol.json").write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")

    inventory = []
    for rel, (expected_bytes, expected_sha) in EXPECTED.items():
        path = ROOT / rel
        actual_bytes = path.stat().st_size
        actual_sha = sha256_file(path)
        ok = actual_bytes == expected_bytes and actual_sha == expected_sha
        inventory.append({"path": rel, "bytes": actual_bytes, "sha256": actual_sha, "identity_ok": ok})
        if not ok:
            raise RuntimeError(f"input identity mismatch: {rel}")
    pd.DataFrame(inventory).to_csv(args.output / "input_inventory.csv", index=False)

    delta_doc = json.loads(DELTA_PATH.read_text())
    delta_eval = delta_function(delta_doc)
    mapping = pd.read_csv(R014 / "soda_tile_to_mother_r014.csv", dtype={"tile_id": str, "mother_scene_id": str})
    if mapping.tile_id.duplicated().any() or not mapping.verified.astype(bool).all():
        raise RuntimeError("invalid SODA mapping")
    mother = dict(zip(mapping.tile_id.astype(str), mapping.mother_scene_id.astype(str)))

    audit_sets = {}
    cluster_universe = {}
    universe_rows = []
    for unit, (dataset, _) in UNITS.items():
        universe = pd.read_csv(M069 / unit / "image_universe.csv", dtype={"image_id": str})
        if universe.image_id.duplicated().any() or universe.d_cal_daudit_split_flag.isna().any():
            raise RuntimeError(f"invalid universe {unit}")
        audit = set(universe.loc[universe.d_cal_daudit_split_flag == "D_audit", "image_id"].astype(str))
        if not audit:
            raise RuntimeError(f"zero D_audit universe {unit}")
        audit_sets[unit] = audit
        if dataset == "SODA-A":
            missing = sorted(audit - mother.keys())
            if missing:
                raise RuntimeError(f"unmapped SODA tiles {unit}: {len(missing)}")
            clusters = utf8_sorted(mother[x] for x in audit)
        else:
            clusters = utf8_sorted(audit)
        cluster_universe[unit] = clusters
        for cluster in clusters:
            universe_rows.append({"unit": unit, "dataset": dataset, "cluster": cluster})
    if audit_sets["A"] != audit_sets["B"] or audit_sets["A"] != audit_sets["C"]:
        raise RuntimeError("DIOR D_audit universes differ")
    if cluster_universe["E"] != cluster_universe["F"]:
        raise RuntimeError("SODA mother universes differ")
    pd.DataFrame(universe_rows).to_csv(args.output / "cluster_universe.csv", index=False)

    join_rows = []
    frames = {}
    all_rows = []
    for unit, (dataset, detector) in UNITS.items():
        frame = load_and_join(unit, audit_sets[unit], mother, delta_eval, join_rows)
        frame.insert(0, "unit", unit)
        frame.insert(1, "dataset", dataset)
        frame.insert(2, "detector", detector)
        frames[unit] = frame
        all_rows.append(frame)
    pd.DataFrame(join_rows).to_csv(args.output / "join_audit.csv", index=False)
    pd.concat(all_rows, ignore_index=True).to_parquet(args.output / "rows.parquet", index=False, compression="zstd")

    prepared = {}
    for unit, (dataset, _) in UNITS.items():
        clusters = cluster_universe[unit]
        cidx = {c: i for i, c in enumerate(clusters)}
        for cohort in COHORTS:
            prepared[(unit, cohort)] = prepare_frame(unit, dataset, cohort, frames[unit], cidx)

    point_unit = {}
    metric_rows = []
    swap_unit = {}
    for unit in UNITS:
        point_unit[unit] = {}
        swap_unit[unit] = {}
        for cohort in COHORTS:
            prep = prepared[(unit, cohort)]
            point_unit[unit][cohort] = {}
            swap_unit[unit][cohort] = {}
            raw_sets = {q: accepted_set(prep.scores["raw_confidence"], q) for q in (0.70, 0.90)}
            for probe in PROBES:
                vals = metrics_sorted(prep.scores[probe], prep.risk)
                point_unit[unit][cohort][probe] = dict(zip(ENDPOINTS, vals[:3]))
                metric_rows.append({
                    "level": "unit", "key": unit, "dataset": UNITS[unit][0], "cohort": cohort, "probe": probe,
                    "rows": len(prep.risk), "AUGRC": vals[0], "Risk@70": vals[1], "Risk@90": vals[2],
                    "actual_coverage@70": vals[3], "actual_coverage@90": vals[4],
                })
                swap_unit[unit][cohort][probe] = {q: swap_fraction(accepted_set(prep.scores[probe], q), raw_sets[q]) for q in (0.70, 0.90)}

    point_dataset = {}
    swap_dataset = {}
    for dataset, units in DATASET_UNITS.items():
        point_dataset[dataset] = {}
        swap_dataset[dataset] = {}
        for cohort in COHORTS:
            point_dataset[dataset][cohort] = {}
            swap_dataset[dataset][cohort] = {}
            for probe in PROBES:
                point_dataset[dataset][cohort][probe] = {e: float(np.mean([point_unit[u][cohort][probe][e] for u in units])) for e in ENDPOINTS}
                swap_dataset[dataset][cohort][probe] = {q: float(np.mean([swap_unit[u][cohort][probe][q] for u in units])) for q in (0.70, 0.90)}
                metric_rows.append({
                    "level": "dataset", "key": dataset, "dataset": dataset, "cohort": cohort, "probe": probe,
                    "rows": int(sum(len(prepared[(u, cohort)].risk) for u in units)),
                    **point_dataset[dataset][cohort][probe],
                    "actual_coverage@70": np.nan, "actual_coverage@90": np.nan,
                })
    pd.DataFrame(metric_rows).to_csv(args.output / "metrics.csv", index=False)

    mults = {}
    mult_sha_rows = []
    for dataset, dindex in DATASET_INDEX.items():
        clusters = cluster_universe[DATASET_UNITS[dataset][0]]
        rng = np.random.RandomState(SEED + dindex)
        counts = np.empty((args.replicates, len(clusters)), dtype=np.int16)
        for replicate in range(args.replicates):
            counts[replicate] = np.bincount(rng.randint(0, len(clusters), size=len(clusters)), minlength=len(clusters))
            mult_sha_rows.append({"dataset": dataset, "replicate": replicate, "sha256": hashlib.sha256(counts[replicate].tobytes()).hexdigest()})
        mults[dataset] = counts
    pd.DataFrame(mult_sha_rows).to_csv(args.output / "multiplicity_sha256.csv", index=False)

    chunks = []
    width = math.ceil(args.replicates / args.workers)
    for start in range(0, args.replicates, width):
        chunks.append((start, min(args.replicates, start + width)))
    ctx = mp.get_context("fork")
    boot_unit = np.empty((args.replicates, len(UNITS), len(COHORTS), len(PROBES), len(ENDPOINTS)), dtype=np.float64)
    with ctx.Pool(args.workers, initializer=worker_init, initargs=(prepared, mults, args.replicates)) as pool:
        for start, values in pool.imap_unordered(bootstrap_chunk, chunks):
            boot_unit[start:start + len(values)] = values
    boot_dataset = np.empty((args.replicates, len(DATASET_INDEX), len(COHORTS), len(PROBES), len(ENDPOINTS)), dtype=np.float64)
    for di, (dataset, units) in enumerate(DATASET_UNITS.items()):
        indices = [list(UNITS).index(u) for u in units]
        boot_dataset[:, di] = np.mean(boot_unit[:, indices], axis=1)
    np.savez_compressed(args.output / "bootstrap_metrics.npz", unit=boot_unit, dataset=boot_dataset)

    point = {"unit": point_unit, "dataset": point_dataset}
    boot = {"unit": boot_unit, "dataset": boot_dataset}
    swap = {"unit": swap_unit, "dataset": swap_dataset}
    hypotheses, hyp_reps = build_hypotheses(point, boot, swap, args.replicates)
    hypotheses.to_csv(args.output / "hypotheses.csv", index=False)
    hyp_reps.to_parquet(args.output / "hypothesis_replicates.parquet", index=False, compression="zstd")
    witnesses = hypotheses[hypotheses.witness].copy()
    witnesses.to_csv(args.output / "witnesses.csv", index=False)
    state, gate_detail = candidate_gate(hypotheses)
    gate = {
        "schema": "orientbench-r020-pragmatic-recovery-gate-v1",
        "candidate_scientific_state": state,
        "formal_cross_machine_state": "NOT_ADJUDICATED_PENDING_SUPERVISOR",
        "completion": "FULL_RECOVERY_ANALYSIS",
        "hypothesis_counts": {"unit": int((hypotheses.level == "unit").sum()), "dataset": int((hypotheses.level == "dataset").sum())},
        **gate_detail,
        "elapsed_seconds": time.time() - started,
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (args.output / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")

    manifest_rows = []
    for path in sorted(args.output.iterdir()):
        if path.is_file() and path.name != "manifest.csv":
            manifest_rows.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    pd.DataFrame(manifest_rows).to_csv(args.output / "manifest.csv", index=False)
    print(json.dumps(gate, sort_keys=True))


if __name__ == "__main__":
    main()

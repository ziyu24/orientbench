#!/usr/bin/env python3
"""Implementation A: preregistered r034 three-way circularity decomposition."""

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
INPUT = ROOT / "outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814/inputs"
UNITS = tuple("ABCDEFGH")
DATASETS = ("DIOR-R", "FAIR1M", "SODA-A", "DOTA-v1.0")
DATASET_UNITS = {"DIOR-R": ("A", "B", "C"), "FAIR1M": ("D",), "SODA-A": ("E", "F"), "DOTA-v1.0": ("G", "H")}
RISKS = ("R_norm", "R_raw")
ELIGIBILITIES = ("AR>=2.1", "all-AR")
ESTIMANDS = ("pooled", "class-standardized")
RANKERS = ("conf", "ARonly", "oracleAR", "probe")
ENDPOINTS = ("AUGRC", "Risk@70")
CONTRASTS = (("probe", "conf"), ("ARonly", "conf"), ("probe", "ARonly"), ("oracleAR", "conf"), ("probe", "oracleAR"), ("ARonly", "oracleAR"))
SEED = 20260814
PRIMARY_DATASETS = {"DIOR-R", "DOTA-v1.0"}


@dataclass
class Pack:
    risk: np.ndarray
    cluster: np.ndarray
    starts: np.ndarray


G_PACKS = {}
G_MULTS = {}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def make_pack(score: np.ndarray, risk: np.ndarray, cluster: np.ndarray) -> Pack:
    order = np.argsort(-score, kind="stable")
    ordered = score[order]
    starts = np.r_[0, np.flatnonzero(ordered[1:] != ordered[:-1]) + 1].astype(np.int64)
    return Pack(risk=risk[order].astype(np.float64), cluster=cluster[order].astype(np.int32), starts=starts)


def evaluate(pack: Pack, multiplicity: np.ndarray) -> tuple[float, float]:
    w = multiplicity[pack.cluster].astype(np.float64, copy=False)
    total = float(w.sum())
    if total <= 0:
        return float("nan"), float("nan")
    gw = np.add.reduceat(w, pack.starts); gr = np.add.reduceat(w * pack.risk, pack.starts)
    keep = gw > 0; gw = gw[keep]; gr = gr[keep]
    cw = np.cumsum(gw); cr = np.cumsum(gr)
    augrc = float(np.sum((np.r_[0.0, cr[:-1] / total] + cr / total) * (gw / total) / 2.0))
    j = int(np.searchsorted(cw, .70 * total, side="left"))
    return augrc, float(cr[j] / cw[j])


def evaluate_estimand(value, multiplicity: np.ndarray) -> tuple[float, float]:
    if isinstance(value, Pack):
        return evaluate(value, multiplicity)
    vals = np.asarray([evaluate(pack, multiplicity) for pack in value], dtype=float)
    if np.isnan(vals).all(axis=0).any():
        raise RuntimeError("class-standardized replicate has no nonempty class")
    return float(np.nanmean(vals[:, 0])), float(np.nanmean(vals[:, 1]))


def accept(score: np.ndarray, q: float = .70) -> np.ndarray:
    order = np.argsort(-score, kind="stable"); ordered = score[order]
    starts = np.r_[0, np.flatnonzero(ordered[1:] != ordered[:-1]) + 1]
    group = int(np.searchsorted(np.cumsum(np.diff(np.r_[starts, len(score)])), q * len(score), side="left"))
    return score >= ordered[starts[group]]


def swap_fraction(a: np.ndarray, b: np.ndarray) -> float:
    x, y = accept(a), accept(b); union = np.count_nonzero(x | y)
    return float(np.count_nonzero(x ^ y) / union) if union else 0.0


def init_worker(packs, mults):
    global G_PACKS, G_MULTS
    G_PACKS, G_MULTS = packs, mults


def worker(bounds: tuple[int, int]):
    first, last = bounds
    shape = (last - first, len(UNITS), len(RISKS), len(ELIGIBILITIES), len(ESTIMANDS), len(RANKERS), len(ENDPOINTS))
    out = np.empty(shape, dtype=np.float64)
    for rr, rep in enumerate(range(first, last)):
        for ui, unit in enumerate(UNITS):
            dataset = next(ds for ds, us in DATASET_UNITS.items() if unit in us)
            mult = G_MULTS[dataset][rep]
            for ri, risk in enumerate(RISKS):
                for ei, eligibility in enumerate(ELIGIBILITIES):
                    for si, estimand in enumerate(ESTIMANDS):
                        for qi, ranker in enumerate(RANKERS):
                            out[rr, ui, ri, ei, si, qi] = evaluate_estimand(G_PACKS[(unit, risk, eligibility, estimand, ranker)], mult)
    return first, out


def p_centered(reps: np.ndarray, point: float) -> float:
    return float((1 + np.count_nonzero(np.abs(reps - point) >= abs(point))) / (len(reps) + 1))


def holm_primary(rows: list[dict]) -> None:
    primary = [r for r in rows if r["primary"]]
    ordered = sorted(primary, key=lambda r: (r["p_raw"], r["hypothesis_key"]))
    running = 0.0; m = len(ordered)
    for i, row in enumerate(ordered):
        running = max(running, min(1.0, (m - i) * row["p_raw"])); row["p_holm"] = running


def witness(row: dict) -> bool:
    p = row["p_holm"] if row["primary"] else row["p_raw"]
    return bool(
        row["delta_ar21_ci_low"] > row["epsilon_ar21"]
        and row["delta_all_ci_high"] < -row["epsilon_all"]
        and p < .05
        and (row["dod_ci_low"] > 0 or row["dod_ci_high"] < 0)
        and abs(row["dod"]) >= row["epsilon_ar21"] + row["epsilon_all"]
        and (row["endpoint"] == "AUGRC" or (row["swap_ar21_70"] >= .05 and row["swap_all_70"] >= .05))
    )


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--replicates", type=int, default=10000); parser.add_argument("--workers", type=int, default=96)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    if args.replicates < 1 or args.workers < 1:
        raise SystemExit("invalid resources")
    started = time.time()
    rows = pd.read_parquet(INPUT / "matched_rows_enriched.parquet")
    universe = pd.read_csv(INPUT / "cluster_universe.csv", dtype={"cluster": str})
    cluster_lists = {ds: universe.loc[universe.dataset.eq(ds)].sort_values("cluster_index").cluster.astype(str).tolist() for ds in DATASETS}
    cindex = {ds: {c: i for i, c in enumerate(values)} for ds, values in cluster_lists.items()}
    packs = {}; point = {}; swaps = {}; metric_rows = []
    for unit in UNITS:
        frame = rows.loc[rows.unit.eq(unit)].copy(); dataset = str(frame.dataset.iloc[0])
        frame["cluster_idx"] = frame.cluster.astype(str).map(cindex[dataset])
        if frame.cluster_idx.isna().any(): raise RuntimeError(f"cluster outside universe {unit}")
        for risk_name, risk_col in (("R_norm", "risk_norm"), ("R_raw", "risk_raw")):
            for eligibility in ELIGIBILITIES:
                selected = frame.loc[frame.gt_ar.ge(2.1)] if eligibility == "AR>=2.1" else frame
                clusters = selected.cluster_idx.to_numpy(np.int32); rv = selected[risk_col].to_numpy(float)
                for estimand in ESTIMANDS:
                    for ranker in RANKERS:
                        score = selected[ranker].to_numpy(float)
                        if estimand == "pooled":
                            value = make_pack(score, rv, clusters)
                        else:
                            value = [make_pack(g[ranker].to_numpy(float), g[risk_col].to_numpy(float), g.cluster_idx.to_numpy(np.int32)) for _, g in selected.groupby("class_id", sort=True)]
                        packs[(unit, risk_name, eligibility, estimand, ranker)] = value
                        metric = evaluate_estimand(value, np.ones(len(cluster_lists[dataset]), dtype=np.int16))
                        point[("unit", unit, risk_name, eligibility, estimand, ranker)] = metric
                        metric_rows.append({"level": "unit", "key": unit, "dataset": dataset, "risk": risk_name, "eligibility": eligibility, "estimand": estimand, "ranker": ranker, "rows": len(selected), "classes": selected.class_id.nunique(), "AUGRC": metric[0], "Risk@70": metric[1]})
                for left, right in CONTRASTS:
                    swaps[("unit", unit, eligibility, left, right)] = swap_fraction(selected[left].to_numpy(float), selected[right].to_numpy(float))
    # Dataset estimands are equal-unit summaries, matching the frozen r020/r023 witness machine.
    for dataset, units in DATASET_UNITS.items():
        for risk in RISKS:
            for eligibility in ELIGIBILITIES:
                for estimand in ESTIMANDS:
                    for ranker in RANKERS:
                        vals = np.asarray([point[("unit", u, risk, eligibility, estimand, ranker)] for u in units])
                        metric = tuple(np.mean(vals, axis=0)); point[("dataset", dataset, risk, eligibility, estimand, ranker)] = metric
                        metric_rows.append({"level": "dataset", "key": dataset, "dataset": dataset, "risk": risk, "eligibility": eligibility, "estimand": estimand, "ranker": ranker, "rows": int(sum(len(rows.loc[rows.unit.eq(u) & (rows.gt_ar.ge(2.1) if eligibility == 'AR>=2.1' else True)]) for u in units)), "classes": int(max(rows.loc[rows.unit.isin(units)].class_id.nunique(), 0)), "AUGRC": metric[0], "Risk@70": metric[1]})
                    for left, right in CONTRASTS:
                        swaps[("dataset", dataset, eligibility, left, right)] = float(np.mean([swaps[("unit", u, eligibility, left, right)] for u in units]))
    pd.DataFrame(metric_rows).to_csv(args.output / "metrics.csv", index=False)

    mults = {}; multiplicity_rows = []
    for di, dataset in enumerate(DATASETS):
        n = len(cluster_lists[dataset]); rng = np.random.RandomState(SEED + di); arr = np.empty((args.replicates, n), dtype=np.int16)
        for rep in range(args.replicates):
            arr[rep] = np.bincount(rng.randint(0, n, size=n), minlength=n)
            multiplicity_rows.append({"dataset": dataset, "replicate": rep, "sha256": hashlib.sha256(arr[rep].tobytes()).hexdigest()})
        mults[dataset] = arr
    np.savez_compressed(args.output / "multiplicities.npz", **mults)
    pd.DataFrame(multiplicity_rows).to_csv(args.output / "multiplicity_sha256.csv", index=False)

    boot_unit = np.empty((args.replicates, len(UNITS), len(RISKS), len(ELIGIBILITIES), len(ESTIMANDS), len(RANKERS), len(ENDPOINTS)), dtype=np.float64)
    width = math.ceil(args.replicates / args.workers); chunks = [(a, min(args.replicates, a + width)) for a in range(0, args.replicates, width)]
    with mp.get_context("fork").Pool(args.workers, initializer=init_worker, initargs=(packs, mults)) as pool:
        for first, block in pool.imap_unordered(worker, chunks):
            boot_unit[first:first + len(block)] = block
    boot_dataset = np.empty((args.replicates, len(DATASETS), len(RISKS), len(ELIGIBILITIES), len(ESTIMANDS), len(RANKERS), len(ENDPOINTS)), dtype=np.float64)
    for di, dataset in enumerate(DATASETS):
        indices = [UNITS.index(u) for u in DATASET_UNITS[dataset]]; boot_dataset[:, di] = np.mean(boot_unit[:, indices], axis=1)
    np.savez_compressed(args.output / "bootstrap_metrics.npz", unit=boot_unit, dataset=boot_dataset)

    hypotheses = []
    index = {"unit": {u: i for i, u in enumerate(UNITS)}, "dataset": {d: i for i, d in enumerate(DATASETS)}}
    source = {"unit": boot_unit, "dataset": boot_dataset}
    for level in ("unit", "dataset"):
        keys = UNITS if level == "unit" else DATASETS
        for key in keys:
            dataset = str(rows.loc[rows.unit.eq(key), "dataset"].iloc[0]) if level == "unit" else key
            ki = index[level][key]
            for risk in RISKS:
                ri = RISKS.index(risk)
                for estimand in ESTIMANDS:
                    si = ESTIMANDS.index(estimand)
                    for left, right in CONTRASTS:
                        li, qi = RANKERS.index(left), RANKERS.index(right)
                        for endpoint in ENDPOINTS:
                            xi = ENDPOINTS.index(endpoint)
                            main_l = point[(level, key, risk, "AR>=2.1", estimand, left)][xi]; main_r = point[(level, key, risk, "AR>=2.1", estimand, right)][xi]
                            all_l = point[(level, key, risk, "all-AR", estimand, left)][xi]; all_r = point[(level, key, risk, "all-AR", estimand, right)][xi]
                            dm, da = main_l - main_r, all_l - all_r; dod = dm - da
                            bm = source[level][:, ki, ri, 0, si, li, xi] - source[level][:, ki, ri, 0, si, qi, xi]
                            ba = source[level][:, ki, ri, 1, si, li, xi] - source[level][:, ki, ri, 1, si, qi, xi]; bd = bm - ba
                            floor = .0005 if endpoint == "AUGRC" else .001
                            primary = level == "dataset" and dataset in PRIMARY_DATASETS and risk in RISKS and estimand == "class-standardized" and endpoint == "AUGRC" and (left, right) in CONTRASTS[:3]
                            hypotheses.append({
                                "hypothesis_key": f"{level}|{key}|{risk}|{estimand}|{left}-{right}|{endpoint}", "level": level, "key": key, "dataset": dataset,
                                "risk": risk, "estimand": estimand, "contrast": f"{left}-{right}", "left_ranker": left, "right_ranker": right, "endpoint": endpoint,
                                "primary": primary, "delta_ar21": dm, "delta_all": da, "dod": dod,
                                "delta_ar21_ci_low": float(np.quantile(bm, .025, method="linear")), "delta_ar21_ci_high": float(np.quantile(bm, .975, method="linear")),
                                "delta_all_ci_low": float(np.quantile(ba, .025, method="linear")), "delta_all_ci_high": float(np.quantile(ba, .975, method="linear")),
                                "dod_ci_low": float(np.quantile(bd, .025, method="linear")), "dod_ci_high": float(np.quantile(bd, .975, method="linear")),
                                "p_raw": p_centered(bd, dod), "p_holm": np.nan,
                                "epsilon_ar21": max(floor, .02 * max(abs(main_l), abs(main_r))), "epsilon_all": max(floor, .02 * max(abs(all_l), abs(all_r))),
                                "swap_ar21_70": swaps[(level, key, "AR>=2.1", left, right)], "swap_all_70": swaps[(level, key, "all-AR", left, right)],
                            })
    holm_primary(hypotheses)
    for row in hypotheses: row["witness"] = witness(row)
    hyp = pd.DataFrame(hypotheses); hyp.to_csv(args.output / "hypotheses.csv", index=False)
    primary = hyp.loc[hyp.primary].copy(); primary.to_csv(args.output / "primary_family.csv", index=False)
    # Persist all 10k primary replicate triples; secondary replicates are reconstructable from bootstrap_metrics.npz.
    replicate_frames = []
    for _, row in primary.iterrows():
        ki = index[row.level][row.key]; ri = RISKS.index(row.risk); si = ESTIMANDS.index(row.estimand); li = RANKERS.index(row.left_ranker); qi = RANKERS.index(row.right_ranker); xi = ENDPOINTS.index(row.endpoint)
        bm = source[row.level][:, ki, ri, 0, si, li, xi] - source[row.level][:, ki, ri, 0, si, qi, xi]
        ba = source[row.level][:, ki, ri, 1, si, li, xi] - source[row.level][:, ki, ri, 1, si, qi, xi]
        replicate_frames.append(pd.DataFrame({"hypothesis_key": row.hypothesis_key, "replicate": np.arange(args.replicates), "delta_ar21": bm, "delta_all": ba, "dod": bm - ba}))
    pd.concat(replicate_frames, ignore_index=True).to_parquet(args.output / "primary_replicates.parquet", index=False, compression="zstd")

    primary_lookup = {(r.dataset, r.risk, r.contrast): r for r in primary.itertuples(index=False)}
    k1_parts = []
    for dataset in ("DIOR-R", "DOTA-v1.0"):
        ar = primary_lookup[(dataset, "R_norm", "ARonly-conf")]; probe = primary_lookup[(dataset, "R_norm", "probe-conf")]; residual = primary_lookup[(dataset, "R_norm", "probe-ARonly")]
        k1_parts.append(abs(ar.dod) >= .8 * abs(probe.dod) and not bool(residual.witness))
    k1 = bool(all(k1_parts))
    residual_rows = [primary_lookup[(ds, "R_norm", "probe-ARonly")] for ds in ("DIOR-R", "DOTA-v1.0")]
    k2 = bool(any(not bool(r.witness) for r in residual_rows))
    pooled = hyp.loc[(hyp.level.eq("dataset")) & hyp.dataset.isin(["DIOR-R", "DOTA-v1.0"]) & hyp.risk.eq("R_norm") & hyp.estimand.eq("pooled") & hyp.endpoint.eq("AUGRC") & hyp.contrast.eq("probe-ARonly")]
    survival = bool(not k1 and not k2 and all(bool(r.witness) for r in residual_rows) and len(pooled) == 2 and all(np.sign(pooled.dod.to_numpy()) == np.sign([r.dod for r in residual_rows])))
    mechanical = []
    for dataset in ("DIOR-R", "DOTA-v1.0"):
        n = primary_lookup[(dataset, "R_norm", "probe-conf")]; raw = primary_lookup[(dataset, "R_raw", "probe-conf")]
        mechanical.append({"dataset": dataset, "R_norm_DoD_probe_conf": n.dod, "R_raw_DoD_probe_conf": raw.dod, "mechanical_disappearance_fraction": float(1 - abs(raw.dod) / max(abs(n.dod), 1e-15)), "AR_information_fraction": float(abs(primary_lookup[(dataset, "R_norm", "ARonly-conf")].dod) / max(abs(n.dod), 1e-15)), "residual_probe_ARonly_DoD": primary_lookup[(dataset, "R_norm", "probe-ARonly")].dod, "residual_witness": bool(primary_lookup[(dataset, "R_norm", "probe-ARonly")].witness)})
    pd.DataFrame(mechanical).to_csv(args.output / "three_way_decomposition.csv", index=False)
    state = "K1_K2_KILL_STRONG_JSTARS" if k1 and k2 else "K1_KILL_STRONG_JSTARS" if k1 else "K2_KILL_STRONG_JSTARS" if k2 else "SURVIVES_TOP_JOURNAL_ROUTE" if survival else "INCONCLUSIVE_DECISIVE"
    judgment = {"schema": "r034_judgment_v1", "candidate_state": state, "K1": k1, "K2": k2, "survival": survival, "primary_count": len(primary), "primary_witnesses": int(primary.witness.sum()), "residual_Rnorm_witness": {r.dataset: bool(r.witness) for r in residual_rows}, "replicates": args.replicates, "seed": SEED, "elapsed_seconds": time.time() - started, "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (args.output / "judgment.json").write_text(json.dumps(judgment, indent=2, sort_keys=True) + "\n")
    protocol = {"schema": "r034_protocol_v1", "seed": SEED, "replicates": args.replicates, "risks": list(RISKS), "eligibilities": list(ELIGIBILITIES), "estimands": list(ESTIMANDS), "rankers": list(RANKERS), "endpoints": list(ENDPOINTS), "contrasts": [f"{a}-{b}" for a, b in CONTRASTS], "primary_estimand": "class-standardized", "primary_endpoint": "AUGRC", "primary_holm_family_size": 12, "K1_ratio_threshold": 0.8, "dataset_aggregation": "equal-unit mean with shared dataset cluster multiplicities", "class_standardization": "equal mean across nonempty official class IDs within each eligibility and bootstrap draw", "validator_output_forcing": False}
    (args.output / "protocol.json").write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
    files = []
    for path in sorted(args.output.iterdir()):
        if path.is_file() and path.name != "manifest.csv": files.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)})
    pd.DataFrame(files).to_csv(args.output / "manifest.csv", index=False)
    print(json.dumps(judgment, sort_keys=True))


if __name__ == "__main__":
    main()

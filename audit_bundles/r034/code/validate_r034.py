#!/usr/bin/env python3
"""Raw-level r034 validator: independently recompute the 12 primary hypotheses."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
import pandas as pd


UNITS = list("ABCGH")
DATASETS = ["DIOR-R", "DOTA-v1.0"]
MEMBERS = {"DIOR-R": ["A", "B", "C"], "DOTA-v1.0": ["G", "H"]}
RISKS = ["R_norm", "R_raw"]
ELIG = ["AR>=2.1", "all-AR"]
RANKERS = ["conf", "ARonly", "probe"]
CONTRASTS = [("probe", "conf"), ("ARonly", "conf"), ("probe", "ARonly")]
WORK = {}; MULT = {}


def sha(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""): h.update(b)
    return h.hexdigest()


def die(message): raise RuntimeError(message)


def pack(score, risk, cluster):
    order = np.argsort(-score, kind="stable"); s = score[order]
    return risk[order], cluster[order], np.r_[0, np.flatnonzero(s[1:] != s[:-1]) + 1]


def augrc(item, mult):
    risk, cluster, starts = item; w = mult[cluster].astype(float, copy=False); total = w.sum()
    if total <= 0: return np.nan
    gw = np.add.reduceat(w, starts); gr = np.add.reduceat(w * risk, starts); keep = gw > 0; gw = gw[keep]; gr = gr[keep]
    cr = np.cumsum(gr)
    return float(np.sum((np.r_[0.0, cr[:-1] / total] + cr / total) * gw / total / 2))


def class_metric(items, mult): return float(np.nanmean([augrc(item, mult) for item in items]))


def init(work, mult):
    global WORK, MULT
    WORK, MULT = work, mult


def chunk(bounds):
    first, last = bounds; out = np.empty((last - first, 5, 2, 2, 3), float)
    domain_of = {u: d for d, units in MEMBERS.items() for u in units}
    for rr, rep in enumerate(range(first, last)):
        for ui, unit in enumerate(UNITS):
            m = MULT[domain_of[unit]][rep]
            for ri, risk in enumerate(RISKS):
                for ei, eligibility in enumerate(ELIG):
                    for qi, ranker in enumerate(RANKERS): out[rr, ui, ri, ei, qi] = class_metric(WORK[unit, risk, eligibility, ranker], m)
    return first, out


def compare_number(a, b, name):
    if not (np.isnan(a) and np.isnan(b)) and abs(float(a) - float(b)) > 1e-10: die(f"numeric mismatch {name}: {a} {b}")


def main():
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, required=True); p.add_argument("--output", type=Path); p.add_argument("--workers", type=int, default=96); p.add_argument("--quiet", action="store_true"); a = p.parse_args(); root = a.root.resolve()
    try:
        impl = root / "implementation_a"; inputs = root / "inputs"
        protocol = json.loads((impl / "protocol.json").read_text())
        if protocol.get("K1_ratio_threshold") != .8: die("K1 threshold protocol mutation")
        if protocol.get("primary_estimand") != "class-standardized": die("primary estimand protocol mutation")
        if protocol.get("primary_endpoint") != "AUGRC" or protocol.get("primary_holm_family_size") != 12: die("primary family protocol mutation")
        if protocol.get("replicates") != 10000 or protocol.get("seed") != 20260814: die("bootstrap protocol mutation")
        if protocol.get("validator_output_forcing") is not False: die("validator output forcing token")
        # Verify Implementation A's own pre-output manifest before trusting any result table.
        manifest = pd.read_csv(impl / "manifest.csv")
        for row in manifest.itertuples(index=False):
            path = impl / row.path
            if not path.is_file() or path.stat().st_size != int(row.bytes) or sha(path) != row.sha256: die(f"implementation A manifest mismatch: {row.path}")
        comparator = json.loads((root / "comparator/comparator.json").read_text())
        if comparator.get("status") != "PASS" or comparator.get("hypotheses") != 576 or comparator.get("atol") != 1e-10: die("A/B comparator invalid")
        lineage = pd.read_csv(root / "lineage_status.csv")
        if len(lineage) != 8 or lineage.contradiction.astype(str).str.lower().eq("true").any(): die("lineage contradiction or incomplete lineage table")
        rows = pd.read_parquet(inputs / "matched_rows_enriched.parquet")
        if len(rows) != 616184 or rows.duplicated(["unit", "image_id", "pred_id"]).any(): die("row identity")
        if not np.allclose(rows.risk_raw, np.clip(rows.e_can / 90., 0, 1), atol=1e-15, rtol=0): die("raw-risk relation mutation")
        if not np.allclose(rows.ARonly, -rows.log_pred_ar, atol=1e-15, rtol=0): die("ARonly relation mutation")
        if not np.allclose(rows.oracleAR, -np.log(np.maximum(rows.gt_ar, 1.)), atol=1e-15, rtol=0): die("oracleAR relation mutation")
        universe = pd.read_csv(inputs / "cluster_universe.csv", dtype={"cluster": str})
        lists = {d: universe[universe.dataset.eq(d)].sort_values("cluster_index").cluster.astype(str).tolist() for d in DATASETS}
        cidx = {d: {x: i for i, x in enumerate(v)} for d, v in lists.items()}
        mult_file = np.load(impl / "multiplicities.npz"); mult = {d: mult_file[d] for d in DATASETS}
        declared_mult_hash = pd.read_csv(impl / "multiplicity_sha256.csv").set_index(["dataset", "replicate"], verify_integrity=True)
        if len(declared_mult_hash) != 40000: die("multiplicity hash row count")
        for dataset in ["DIOR-R", "FAIR1M", "SODA-A", "DOTA-v1.0"]:
            array = mult_file[dataset]
            for replicate in range(10000):
                actual_hash = hashlib.sha256(array[replicate].tobytes()).hexdigest()
                if actual_hash != declared_mult_hash.at[(dataset, replicate), "sha256"]: die(f"multiplicity hash mismatch {dataset}/{replicate}")
        for d in DATASETS:
            if mult[d].shape != (10000, len(lists[d])) or not np.all(mult[d].sum(axis=1) == len(lists[d])): die(f"multiplicity structure {d}")
        work = {}; point = {}; domain_of = {u: d for d, us in MEMBERS.items() for u in us}
        for unit in UNITS:
            frame = rows[rows.unit.eq(unit)].copy(); domain = domain_of[unit]; frame["ci"] = frame.cluster.astype(str).map(cidx[domain])
            if frame.ci.isna().any(): die(f"cluster gap {unit}")
            for risk, column in (("R_norm", "risk_norm"), ("R_raw", "risk_raw")):
                for eligibility in ELIG:
                    selected = frame[frame.gt_ar.ge(2.1)] if eligibility == "AR>=2.1" else frame
                    for ranker in RANKERS:
                        items = [pack(g[ranker].to_numpy(float), g[column].to_numpy(float), g.ci.to_numpy(np.int32)) for _, g in selected.groupby("class_id", sort=True)]
                        work[unit, risk, eligibility, ranker] = items
                        point[unit, risk, eligibility, ranker] = class_metric(items, np.ones(len(lists[domain]), np.int16))
        reps = np.empty((10000, 5, 2, 2, 3), float); width = math.ceil(10000 / a.workers); tasks = [(x, min(x + width, 10000)) for x in range(0, 10000, width)]
        with mp.get_context("fork").Pool(a.workers, initializer=init, initargs=(work, mult)) as pool:
            for first, block in pool.imap_unordered(chunk, tasks): reps[first:first + len(block)] = block
        recomputed = []
        for dataset in DATASETS:
            uidx = [UNITS.index(u) for u in MEMBERS[dataset]]
            for risk in RISKS:
                ri = RISKS.index(risk)
                for left, right in CONTRASTS:
                    li, qi = RANKERS.index(left), RANKERS.index(right)
                    dm = np.mean([point[u, risk, "AR>=2.1", left] - point[u, risk, "AR>=2.1", right] for u in MEMBERS[dataset]])
                    da = np.mean([point[u, risk, "all-AR", left] - point[u, risk, "all-AR", right] for u in MEMBERS[dataset]])
                    bm = np.mean(reps[:, uidx, ri, 0, li] - reps[:, uidx, ri, 0, qi], axis=1)
                    ba = np.mean(reps[:, uidx, ri, 1, li] - reps[:, uidx, ri, 1, qi], axis=1); bd = bm - ba; dod = dm - da
                    recomputed.append({"hypothesis_key": f"dataset|{dataset}|{risk}|class-standardized|{left}-{right}|AUGRC", "dataset": dataset, "risk": risk, "contrast": f"{left}-{right}", "delta_ar21": dm, "delta_all": da, "dod": dod, "delta_ar21_ci_low": float(np.quantile(bm, .025, method="linear")), "delta_ar21_ci_high": float(np.quantile(bm, .975, method="linear")), "delta_all_ci_low": float(np.quantile(ba, .025, method="linear")), "delta_all_ci_high": float(np.quantile(ba, .975, method="linear")), "dod_ci_low": float(np.quantile(bd, .025, method="linear")), "dod_ci_high": float(np.quantile(bd, .975, method="linear")), "p_raw": float((1 + np.count_nonzero(np.abs(bd - dod) >= abs(dod))) / 10001), "p_holm": np.nan})
        ordered = sorted(recomputed, key=lambda x: (x["p_raw"], x["hypothesis_key"])); running = 0.
        for i, row in enumerate(ordered): running = max(running, min(1., (12 - i) * row["p_raw"])); row["p_holm"] = running
        declared = pd.read_csv(impl / "primary_family.csv").set_index("hypothesis_key", verify_integrity=True)
        if len(declared) != 12: die("primary family size")
        numeric = ["delta_ar21", "delta_all", "dod", "delta_ar21_ci_low", "delta_ar21_ci_high", "delta_all_ci_low", "delta_all_ci_high", "dod_ci_low", "dod_ci_high", "p_raw", "p_holm"]
        for row in recomputed:
            if row["hypothesis_key"] not in declared.index: die("primary key missing")
            for field in numeric: compare_number(row[field], declared.at[row["hypothesis_key"], field], row["hypothesis_key"] + "/" + field)
        # Recompute witness predicates using declared epsilon/swap fields, then derive K1/K2 without expecting an outcome.
        for row in recomputed:
            d = declared.loc[row["hypothesis_key"]]
            row["witness"] = bool(row["delta_ar21_ci_low"] > d.epsilon_ar21 and row["delta_all_ci_high"] < -d.epsilon_all and row["p_holm"] < .05 and (row["dod_ci_low"] > 0 or row["dod_ci_high"] < 0) and abs(row["dod"]) >= d.epsilon_ar21 + d.epsilon_all)
            if row["witness"] != bool(d.witness): die("witness mismatch " + row["hypothesis_key"])
        lookup = {(x["dataset"], x["risk"], x["contrast"]): x for x in recomputed}
        k1 = all(abs(lookup[d, "R_norm", "ARonly-conf"]["dod"]) >= .8 * abs(lookup[d, "R_norm", "probe-conf"]["dod"]) and not lookup[d, "R_norm", "probe-ARonly"]["witness"] for d in DATASETS)
        k2 = any(not lookup[d, "R_norm", "probe-ARonly"]["witness"] for d in DATASETS)
        state = "K1_K2_KILL_STRONG_JSTARS" if k1 and k2 else "K1_KILL_STRONG_JSTARS" if k1 else "K2_KILL_STRONG_JSTARS" if k2 else "PRIMARY_NO_KILL"
        judgment = json.loads((impl / "judgment.json").read_text())
        if bool(judgment["K1"]) != k1 or bool(judgment["K2"]) != k2 or judgment["candidate_state"] != state: die("judgment mismatch")
        result = {"status": "PASS", "raw_rows": len(rows), "recomputed_primary": len(recomputed), "numeric_fields_per_primary": len(numeric), "K1": k1, "K2": k2, "candidate_state": state, "validator_output_forcing": False}
        if a.output: a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        if not a.quiet: print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Independent structural and gate validator for pragmatic r020 recovery output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROBES = ("raw_confidence", "linear_source_frozen", "tta_angle", "tta_localization")
COHORTS = ("MAIN", "NO_LONGSIDE_AR21", "NO_GEONORM_AR21", "NORMALIZED_ALL_AR", "NORMALIZED_AR16", "NORMALIZED_AR13")
ENDPOINTS = ("AUGRC", "Risk@70", "Risk@90")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def independent_metrics(score: np.ndarray, risk: np.ndarray):
    frame = pd.DataFrame({"score": score, "risk": risk}).sort_values("score", ascending=False, kind="stable")
    groups = frame.groupby("score", sort=False).agg(count=("risk", "size"), risk_sum=("risk", "sum"))
    n = len(frame)
    count = groups["count"].to_numpy(dtype=float)
    risk_sum = groups["risk_sum"].to_numpy(dtype=float)
    cumulative_count = np.cumsum(count)
    cumulative_risk = np.cumsum(risk_sum)
    coverage_step = count / n
    generalized = cumulative_risk / n
    augrc = float(np.sum((np.r_[0.0, generalized[:-1]] + generalized) * coverage_step / 2.0))
    selective = []
    for q in (0.70, 0.90):
        i = int(np.flatnonzero(cumulative_count >= q * n)[0])
        selective.append(float(cumulative_risk[i] / cumulative_count[i]))
    return augrc, selective[0], selective[1]


def independent_point_check(out: Path):
    rows = pd.read_parquet(out / "rows.parquet")
    metrics = pd.read_csv(out / "metrics.csv")
    unit_values = {}
    for unit, frame in rows.groupby("unit", sort=False):
        unit_values[unit] = {}
        ar = frame.ar.to_numpy()
        for cohort in COHORTS:
            if cohort in ("MAIN", "NO_LONGSIDE_AR21", "NO_GEONORM_AR21"):
                mask = ar >= 2.1
            elif cohort == "NORMALIZED_ALL_AR":
                mask = np.ones(len(frame), dtype=bool)
            elif cohort == "NORMALIZED_AR16":
                mask = ar >= 1.6
            else:
                mask = ar >= 1.3
            part = frame.loc[mask]
            risk_column = "risk_raw_theta" if cohort == "NO_LONGSIDE_AR21" else "risk_no_geonorm" if cohort == "NO_GEONORM_AR21" else "risk_main"
            unit_values[unit][cohort] = {}
            for probe in PROBES:
                values = independent_metrics(part[probe].to_numpy(dtype=float), part[risk_column].to_numpy(dtype=float))
                unit_values[unit][cohort][probe] = dict(zip(ENDPOINTS, values))
                reported = metrics[(metrics.level == "unit") & (metrics.key == unit) & (metrics.cohort == cohort) & (metrics.probe == probe)].iloc[0]
                if not np.allclose(values, reported[list(ENDPOINTS)].to_numpy(dtype=float), atol=1e-12, rtol=0):
                    raise SystemExit(f"independent point mismatch {unit} {cohort} {probe}")
    for rec in metrics[metrics.level == "dataset"].to_dict("records"):
        units = rows.loc[rows.dataset == rec["dataset"], "unit"].drop_duplicates().tolist()
        expected = [np.mean([unit_values[u][rec["cohort"]][rec["probe"]][endpoint] for u in units]) for endpoint in ENDPOINTS]
        actual = [rec[endpoint] for endpoint in ENDPOINTS]
        if not np.allclose(expected, actual, atol=1e-12, rtol=0):
            raise SystemExit(f"independent dataset point mismatch {rec['dataset']} {rec['cohort']} {rec['probe']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-replicates", type=int, required=True)
    args = parser.parse_args()
    out = args.output
    required = {
        "protocol.json", "input_inventory.csv", "cluster_universe.csv", "join_audit.csv", "rows.parquet",
        "metrics.csv", "multiplicity_sha256.csv", "bootstrap_metrics.npz", "hypotheses.csv",
        "hypothesis_replicates.parquet", "witnesses.csv", "gate.json", "manifest.csv",
    }
    missing = required - {p.name for p in out.iterdir()}
    if missing:
        raise SystemExit(f"missing outputs: {sorted(missing)}")
    protocol = json.loads((out / "protocol.json").read_text())
    if protocol["replicates"] != args.expected_replicates or protocol["learned_eqs_read"] is not False:
        raise SystemExit("protocol mismatch")
    inventory = pd.read_csv(out / "input_inventory.csv")
    if len(inventory) != 26 or not inventory.identity_ok.all():
        raise SystemExit("input inventory mismatch")
    joins = pd.read_csv(out / "join_audit.csv")
    if len(joins) != 6 or joins[["feature_missing", "score_missing"]].to_numpy().any():
        raise SystemExit("join audit failure")
    independent_point_check(out)
    hypotheses = pd.read_csv(out / "hypotheses.csv")
    if len(hypotheses) != 405 or (hypotheses.level == "unit").sum() != 270 or (hypotheses.level == "dataset").sum() != 135:
        raise SystemExit("hypothesis family size mismatch")
    if hypotheses.hypothesis_key.duplicated().any() or hypotheses.p_holm.isna().any():
        raise SystemExit("hypothesis identity/Holm mismatch")
    for level, size in (("unit", 270), ("dataset", 135)):
        part = hypotheses[hypotheses.level == level].sort_values(["p_raw", "hypothesis_key"], kind="stable")
        expected = []
        running = 0.0
        for rank, p in enumerate(part.p_raw, 1):
            running = max(running, min(1.0, (size - rank + 1) * p))
            expected.append(running)
        if not np.allclose(part.p_holm, expected, atol=1e-14, rtol=0):
            raise SystemExit(f"Holm mismatch {level}")
    reps = pd.read_parquet(out / "hypothesis_replicates.parquet", columns=["hypothesis_key", "replicate", "dod"])
    if len(reps) != 405 * args.expected_replicates:
        raise SystemExit("replicate row count mismatch")
    counts = reps.groupby("hypothesis_key", sort=False).replicate.nunique()
    if len(counts) != 405 or not (counts == args.expected_replicates).all() or not np.isfinite(reps.dod).all():
        raise SystemExit("replicate completeness mismatch")
    replicate_count = args.expected_replicates
    block_keys = reps.hypothesis_key.to_numpy()[::replicate_count]
    if len(block_keys) != 405:
        raise SystemExit("replicate block count mismatch")
    dod_matrix = reps.dod.to_numpy().reshape(405, replicate_count)
    for block, key in enumerate(block_keys):
        if not (reps.hypothesis_key.iloc[block * replicate_count:(block + 1) * replicate_count] == key).all():
            raise SystemExit(f"noncontiguous replicate block {key}")
        row = hypotheses[hypotheses.hypothesis_key == key].iloc[0]
        expected_p = (1 + np.count_nonzero(np.abs(dod_matrix[block] - row.dod) >= abs(row.dod))) / (replicate_count + 1)
        if not np.isclose(expected_p, row.p_raw, atol=1e-14, rtol=0):
            raise SystemExit(f"centered bootstrap p mismatch {key}")
        if row.delta_main < 0 < row.delta_ablation:
            ci_ok = row.delta_main_ci_high < -row.epsilon_main and row.delta_ablation_ci_low > row.epsilon_ablation
        elif row.delta_ablation < 0 < row.delta_main:
            ci_ok = row.delta_main_ci_low > row.epsilon_main and row.delta_ablation_ci_high < -row.epsilon_ablation
        else:
            ci_ok = False
        swap_ok = True
        if row.endpoint == "Risk@70":
            swap_ok = row.main_swap70 >= 0.05 and row.ablation_swap70 >= 0.05
        elif row.endpoint == "Risk@90":
            swap_ok = row.main_swap90 >= 0.05 and row.ablation_swap90 >= 0.05
        expected_witness = bool(ci_ok and row.p_holm < 0.05 and (row.dod_ci_low > 0 or row.dod_ci_high < 0) and abs(row.dod) >= row.epsilon_main + row.epsilon_ablation and swap_ok)
        if bool(row.witness) != expected_witness:
            raise SystemExit(f"witness predicate mismatch {key}")
    manifest = pd.read_csv(out / "manifest.csv")
    for rec in manifest.to_dict("records"):
        path = out / rec["path"]
        if path.stat().st_size != rec["bytes"] or sha256_file(path) != rec["sha256"]:
            raise SystemExit(f"manifest mismatch {path.name}")
    gate = json.loads((out / "gate.json").read_text())
    witness = hypotheses[hypotheses.witness]
    if gate["unit_witnesses"] != int((witness.level == "unit").sum()) or gate["dataset_witnesses"] != int((witness.level == "dataset").sum()):
        raise SystemExit("gate witness count mismatch")
    if gate["formal_cross_machine_state"] != "NOT_ADJUDICATED_PENDING_SUPERVISOR":
        raise SystemExit("formal-state guard missing")
    print(json.dumps({"status": "PASS", "candidate_scientific_state": gate["candidate_scientific_state"], "witnesses": len(witness)}, sort_keys=True))


if __name__ == "__main__":
    main()

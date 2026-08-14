#!/usr/bin/env python3
"""Independent implementation B for r034; consumes only the frozen derived input."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing
import time
from pathlib import Path

import numpy
import pandas


PROJECT = Path(__file__).resolve().parents[2]
INPUTS = PROJECT / "outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814/inputs"
CELLS = list("ABCDEFGH")
DOMAINS = ["DIOR-R", "FAIR1M", "SODA-A", "DOTA-v1.0"]
MEMBERS = {"DIOR-R": ["A", "B", "C"], "FAIR1M": ["D"], "SODA-A": ["E", "F"], "DOTA-v1.0": ["G", "H"]}
LOSS_NAMES = ["R_norm", "R_raw"]
SUBSETS = ["AR>=2.1", "all-AR"]
STANDARDIZATIONS = ["pooled", "class-standardized"]
METHODS = ["conf", "ARonly", "oracleAR", "probe"]
OUTCOMES = ["AUGRC", "Risk@70"]
PAIRS = [("probe", "conf"), ("ARonly", "conf"), ("probe", "ARonly"), ("oracleAR", "conf"), ("probe", "oracleAR"), ("ARonly", "oracleAR")]
RANDOM_SEED = 20260814
WORK = None
COUNTS = None


def ordered_groups(values, losses, cluster_number):
    permutation = numpy.argsort(-values, kind="stable")
    sorted_values = values[permutation]
    return (losses[permutation].astype(numpy.float64), cluster_number[permutation].astype(numpy.int32), numpy.r_[0, numpy.where(sorted_values[:-1] != sorted_values[1:])[0] + 1].astype(numpy.int64))


def score_curve(package, count):
    losses, cluster_number, starts = package
    weight = count[cluster_number].astype(numpy.float64, copy=False)
    total = weight.sum()
    if total <= 0:
        return numpy.nan, numpy.nan
    mass = numpy.add.reduceat(weight, starts); loss_mass = numpy.add.reduceat(weight * losses, starts)
    valid = mass > 0; mass = mass[valid]; loss_mass = loss_mass[valid]
    coverage = numpy.cumsum(mass); cumulative_loss = numpy.cumsum(loss_mass)
    normalized = cumulative_loss / total
    area = numpy.sum((numpy.r_[0.0, normalized[:-1]] + normalized) * mass / total / 2.0)
    cut = numpy.searchsorted(coverage, .7 * total, side="left")
    return float(area), float(cumulative_loss[cut] / coverage[cut])


def evaluate(entry, count):
    if isinstance(entry, tuple):
        return score_curve(entry, count)
    values = numpy.asarray([score_curve(x, count) for x in entry])
    return float(numpy.nanmean(values[:, 0])), float(numpy.nanmean(values[:, 1]))


def initializer(work, counts):
    global WORK, COUNTS
    WORK = work; COUNTS = counts


def calculate_range(bounds):
    begin, finish = bounds
    answer = numpy.empty((finish - begin, 8, 2, 2, 2, 4, 2), numpy.float64)
    cell_domain = {cell: domain for domain, cells in MEMBERS.items() for cell in cells}
    for offset, replicate in enumerate(range(begin, finish)):
        for c, cell in enumerate(CELLS):
            multiplicity = COUNTS[cell_domain[cell]][replicate]
            for r, loss_name in enumerate(LOSS_NAMES):
                for s, subset in enumerate(SUBSETS):
                    for z, standardization in enumerate(STANDARDIZATIONS):
                        for m, method in enumerate(METHODS):
                            answer[offset, c, r, s, z, m] = evaluate(WORK[cell, loss_name, subset, standardization, method], multiplicity)
    return begin, answer


def selected_at_70(values):
    permutation = numpy.argsort(-values, kind="stable"); sorted_values = values[permutation]
    starts = numpy.r_[0, numpy.where(sorted_values[:-1] != sorted_values[1:])[0] + 1]
    sizes = numpy.diff(numpy.r_[starts, len(values)])
    group = numpy.searchsorted(numpy.cumsum(sizes), .7 * len(values), side="left")
    return values >= sorted_values[starts[group]]


def swap(left, right):
    a, b = selected_at_70(left), selected_at_70(right)
    return float(numpy.count_nonzero(a ^ b) / numpy.count_nonzero(a | b))


def centered_probability(distribution, observed):
    return float((1 + numpy.sum(numpy.abs(distribution - observed) >= abs(observed))) / (len(distribution) + 1))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True, type=Path); parser.add_argument("--replicates", type=int, default=10000); parser.add_argument("--workers", type=int, default=96)
    arguments = parser.parse_args(); arguments.output.mkdir(parents=True, exist_ok=True); beginning = time.time()
    rows = pandas.read_parquet(INPUTS / "matched_rows_enriched.parquet")
    universe = pandas.read_csv(INPUTS / "cluster_universe.csv", dtype={"cluster": str})
    cluster_names = {domain: universe[universe.dataset == domain].sort_values("cluster_index").cluster.astype(str).tolist() for domain in DOMAINS}
    cluster_positions = {domain: {name: i for i, name in enumerate(names)} for domain, names in cluster_names.items()}
    packages = {}; point = {}; swaps = {}
    cell_domain = {cell: domain for domain, cells in MEMBERS.items() for cell in cells}
    for cell in CELLS:
        data = rows[rows.unit == cell].copy(); domain = cell_domain[cell]
        data["cluster_number"] = data.cluster.astype(str).map(cluster_positions[domain])
        if data.cluster_number.isna().any(): raise ValueError("cluster mapping " + cell)
        for loss_name, risk_column in zip(LOSS_NAMES, ["risk_norm", "risk_raw"]):
            for subset in SUBSETS:
                chosen = data[data.gt_ar >= 2.1] if subset == "AR>=2.1" else data
                for standardization in STANDARDIZATIONS:
                    for method in METHODS:
                        if standardization == "pooled":
                            package = ordered_groups(chosen[method].to_numpy(float), chosen[risk_column].to_numpy(float), chosen.cluster_number.to_numpy(numpy.int32))
                        else:
                            package = [ordered_groups(part[method].to_numpy(float), part[risk_column].to_numpy(float), part.cluster_number.to_numpy(numpy.int32)) for _, part in chosen.groupby("class_id", sort=True)]
                        packages[cell, loss_name, subset, standardization, method] = package
                        point["unit", cell, loss_name, subset, standardization, method] = evaluate(package, numpy.ones(len(cluster_names[domain]), numpy.int16))
                for left, right in PAIRS:
                    swaps["unit", cell, subset, left, right] = swap(chosen[left].to_numpy(float), chosen[right].to_numpy(float))
    for domain, cells in MEMBERS.items():
        for loss_name in LOSS_NAMES:
            for subset in SUBSETS:
                for standardization in STANDARDIZATIONS:
                    for method in METHODS:
                        point["dataset", domain, loss_name, subset, standardization, method] = tuple(numpy.mean([point["unit", cell, loss_name, subset, standardization, method] for cell in cells], axis=0))
                for left, right in PAIRS:
                    swaps["dataset", domain, subset, left, right] = float(numpy.mean([swaps["unit", cell, subset, left, right] for cell in cells]))

    counts = {}; count_hashes = []
    for domain_number, domain in enumerate(DOMAINS):
        n = len(cluster_names[domain]); random = numpy.random.RandomState(RANDOM_SEED + domain_number); matrix = numpy.empty((arguments.replicates, n), numpy.int16)
        for replicate in range(arguments.replicates):
            matrix[replicate] = numpy.bincount(random.randint(0, n, n), minlength=n)
            count_hashes.append({"dataset": domain, "replicate": replicate, "sha256": hashlib.sha256(matrix[replicate].tobytes()).hexdigest()})
        counts[domain] = matrix
    numpy.savez_compressed(arguments.output / "multiplicities.npz", **counts)
    pandas.DataFrame(count_hashes).to_csv(arguments.output / "multiplicity_sha256.csv", index=False)
    blocks = numpy.empty((arguments.replicates, 8, 2, 2, 2, 4, 2), numpy.float64)
    width = math.ceil(arguments.replicates / arguments.workers)
    jobs = [(first, min(first + width, arguments.replicates)) for first in range(0, arguments.replicates, width)]
    with multiprocessing.get_context("fork").Pool(arguments.workers, initializer=initializer, initargs=(packages, counts)) as pool:
        for first, block in pool.imap_unordered(calculate_range, jobs): blocks[first:first + len(block)] = block
    dataset_blocks = numpy.empty((arguments.replicates, 4, 2, 2, 2, 4, 2), numpy.float64)
    for domain_number, domain in enumerate(DOMAINS):
        dataset_blocks[:, domain_number] = numpy.mean(blocks[:, [CELLS.index(c) for c in MEMBERS[domain]]], axis=1)
    numpy.savez_compressed(arguments.output / "bootstrap_metrics.npz", unit=blocks, dataset=dataset_blocks)

    arrays = {"unit": blocks, "dataset": dataset_blocks}; indices = {"unit": {v: i for i, v in enumerate(CELLS)}, "dataset": {v: i for i, v in enumerate(DOMAINS)}}
    records = []
    for level, keys in (("unit", CELLS), ("dataset", DOMAINS)):
        for key in keys:
            domain = cell_domain[key] if level == "unit" else key; key_number = indices[level][key]
            for loss_name in LOSS_NAMES:
                loss_number = LOSS_NAMES.index(loss_name)
                for standardization in STANDARDIZATIONS:
                    std_number = STANDARDIZATIONS.index(standardization)
                    for left, right in PAIRS:
                        left_number, right_number = METHODS.index(left), METHODS.index(right)
                        for endpoint in OUTCOMES:
                            endpoint_number = OUTCOMES.index(endpoint)
                            main_left = point[level, key, loss_name, "AR>=2.1", standardization, left][endpoint_number]; main_right = point[level, key, loss_name, "AR>=2.1", standardization, right][endpoint_number]
                            all_left = point[level, key, loss_name, "all-AR", standardization, left][endpoint_number]; all_right = point[level, key, loss_name, "all-AR", standardization, right][endpoint_number]
                            delta_main, delta_all = main_left - main_right, all_left - all_right
                            main_rep = arrays[level][:, key_number, loss_number, 0, std_number, left_number, endpoint_number] - arrays[level][:, key_number, loss_number, 0, std_number, right_number, endpoint_number]
                            all_rep = arrays[level][:, key_number, loss_number, 1, std_number, left_number, endpoint_number] - arrays[level][:, key_number, loss_number, 1, std_number, right_number, endpoint_number]
                            difference = main_rep - all_rep; observed = delta_main - delta_all; floor = .0005 if endpoint == "AUGRC" else .001
                            is_primary = level == "dataset" and domain in {"DIOR-R", "DOTA-v1.0"} and standardization == "class-standardized" and endpoint == "AUGRC" and (left, right) in PAIRS[:3]
                            records.append({"hypothesis_key": f"{level}|{key}|{loss_name}|{standardization}|{left}-{right}|{endpoint}", "level": level, "key": key, "dataset": domain, "risk": loss_name, "estimand": standardization, "contrast": left + "-" + right, "left_ranker": left, "right_ranker": right, "endpoint": endpoint, "primary": is_primary, "delta_ar21": delta_main, "delta_all": delta_all, "dod": observed, "delta_ar21_ci_low": float(numpy.quantile(main_rep, .025, method="linear")), "delta_ar21_ci_high": float(numpy.quantile(main_rep, .975, method="linear")), "delta_all_ci_low": float(numpy.quantile(all_rep, .025, method="linear")), "delta_all_ci_high": float(numpy.quantile(all_rep, .975, method="linear")), "dod_ci_low": float(numpy.quantile(difference, .025, method="linear")), "dod_ci_high": float(numpy.quantile(difference, .975, method="linear")), "p_raw": centered_probability(difference, observed), "p_holm": numpy.nan, "epsilon_ar21": max(floor, .02 * max(abs(main_left), abs(main_right))), "epsilon_all": max(floor, .02 * max(abs(all_left), abs(all_right))), "swap_ar21_70": swaps[level, key, "AR>=2.1", left, right], "swap_all_70": swaps[level, key, "all-AR", left, right]})
    primary_records = sorted([r for r in records if r["primary"]], key=lambda r: (r["p_raw"], r["hypothesis_key"])); running = 0.0
    for position, record in enumerate(primary_records): running = max(running, min(1.0, (len(primary_records) - position) * record["p_raw"])); record["p_holm"] = running
    for record in records:
        probability = record["p_holm"] if record["primary"] else record["p_raw"]
        record["witness"] = bool(record["delta_ar21_ci_low"] > record["epsilon_ar21"] and record["delta_all_ci_high"] < -record["epsilon_all"] and probability < .05 and (record["dod_ci_low"] > 0 or record["dod_ci_high"] < 0) and abs(record["dod"]) >= record["epsilon_ar21"] + record["epsilon_all"] and (record["endpoint"] == "AUGRC" or min(record["swap_ar21_70"], record["swap_all_70"]) >= .05))
    hypotheses = pandas.DataFrame(records); hypotheses.to_csv(arguments.output / "hypotheses.csv", index=False); hypotheses[hypotheses.primary].to_csv(arguments.output / "primary_family.csv", index=False)
    lookup = {(r.dataset, r.risk, r.contrast): r for r in hypotheses[hypotheses.primary].itertuples(index=False)}
    k1 = all(abs(lookup[domain, "R_norm", "ARonly-conf"].dod) >= .8 * abs(lookup[domain, "R_norm", "probe-conf"].dod) and not bool(lookup[domain, "R_norm", "probe-ARonly"].witness) for domain in ["DIOR-R", "DOTA-v1.0"])
    k2 = any(not bool(lookup[domain, "R_norm", "probe-ARonly"].witness) for domain in ["DIOR-R", "DOTA-v1.0"])
    pooled = hypotheses[(hypotheses.level == "dataset") & hypotheses.dataset.isin(["DIOR-R", "DOTA-v1.0"]) & (hypotheses.risk == "R_norm") & (hypotheses.estimand == "pooled") & (hypotheses.endpoint == "AUGRC") & (hypotheses.contrast == "probe-ARonly")]
    residual = [lookup[d, "R_norm", "probe-ARonly"] for d in ["DIOR-R", "DOTA-v1.0"]]
    survives = bool(not k1 and not k2 and all(x.witness for x in residual) and len(pooled) == 2 and numpy.array_equal(numpy.sign(pooled.dod.to_numpy()), numpy.sign([x.dod for x in residual])))
    state = "K1_K2_KILL_STRONG_JSTARS" if k1 and k2 else "K1_KILL_STRONG_JSTARS" if k1 else "K2_KILL_STRONG_JSTARS" if k2 else "SURVIVES_TOP_JOURNAL_ROUTE" if survives else "INCONCLUSIVE_DECISIVE"
    judgment = {"schema": "r034_judgment_v1", "candidate_state": state, "K1": bool(k1), "K2": bool(k2), "survival": survives, "primary_count": 12, "primary_witnesses": int(hypotheses[hypotheses.primary].witness.sum()), "residual_Rnorm_witness": {x.dataset: bool(x.witness) for x in residual}, "replicates": arguments.replicates, "seed": RANDOM_SEED, "elapsed_seconds": time.time() - beginning}
    (arguments.output / "judgment.json").write_text(json.dumps(judgment, indent=2, sort_keys=True) + "\n")
    (arguments.output / "protocol.json").write_text(json.dumps({"seed": RANDOM_SEED, "replicates": arguments.replicates, "K1_ratio_threshold": .8, "primary_estimand": "class-standardized", "primary_holm_family_size": 12, "validator_output_forcing": False}, indent=2, sort_keys=True) + "\n")
    print(json.dumps(judgment, sort_keys=True))


if __name__ == "__main__":
    main()

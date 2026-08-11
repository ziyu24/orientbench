#!/usr/bin/env python3
"""Independent raw-input implementation B for the pragmatic r020 recovery.

No code or derived rows from pragmatic_recovery.py are imported or read.  This
program reconstructs the frozen cohorts and all bootstrap endpoints directly
from the 26 source assets, then seals its own output for later comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as multiprocessing
import os
import time
from pathlib import Path

import numpy as numpy
import pandas as pandas


PROJECT = Path(__file__).resolve().parents[2]
SOURCE_M = PROJECT / "outputs/persistent_artifacts/m069_fullval_reliability"
SOURCE_R = PROJECT / "outputs/persistent_artifacts/orientbench_r014"
DELTA_JSON = PROJECT / "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json"
CELLS = ("A", "B", "C", "D", "E", "F")
CELL_DATASET = {"A": "DIOR-R", "B": "DIOR-R", "C": "DIOR-R", "D": "FAIR1M", "E": "SODA-A", "F": "SODA-A"}
CELL_DETECTOR = {"A": "PSC", "B": "Oriented R-CNN", "C": "RTMDet", "D": "PSC", "E": "PSC", "F": "Oriented R-CNN"}
DATASETS = ("DIOR-R", "FAIR1M", "SODA-A")
DATASET_CELLS = {name: tuple(c for c in CELLS if CELL_DATASET[c] == name) for name in DATASETS}
METHODS = ("raw_confidence", "linear_source_frozen", "tta_angle", "tta_localization")
LOSSES = ("AUGRC", "Risk@70", "Risk@90")
VARIANTS = ("MAIN", "NO_LONGSIDE_AR21", "NO_GEONORM_AR21", "NORMALIZED_ALL_AR", "NORMALIZED_AR16", "NORMALIZED_AR13")
TEST_ABLATIONS = VARIANTS[1:]
CLASS_OF = {
    "NO_LONGSIDE_AR21": "ANGLE_EQUIVALENCE",
    "NO_GEONORM_AR21": "GEOMETRY_NORMALIZATION",
    "NORMALIZED_ALL_AR": "AR_DOMAIN",
    "NORMALIZED_AR16": "AR_DOMAIN",
    "NORMALIZED_AR13": "AR_DOMAIN",
}
RANDOM_SEED = 20260809


WORK_PACKS = None
WORK_MULTIPLICITIES = None


def file_hash(filename: Path) -> str:
    digest = hashlib.sha256()
    with filename.open("rb") as stream:
        while True:
            block = stream.read(16 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def byte_sort(items) -> list[str]:
    return sorted({str(item) for item in items}, key=lambda item: item.encode("utf-8"))


def circular_distance(left: float, right: float) -> float:
    value = abs((left - right) % 180.0)
    return min(value, 180.0 - value)


def unpack_box(box: dict) -> tuple[float, float, float]:
    return float(box["obb_w"]), float(box["obb_h"]), math.degrees(float(box["obb_theta"]))


def canonical_heading(width: float, height: float, angle: float) -> float:
    if height > width:
        angle += 90.0
    return angle % 180.0


def make_delta_lookup():
    document = json.loads(DELTA_JSON.read_text(encoding="utf-8"))
    tolerance = float(document["solve_tolerance_deg"])
    finite = [(float(a), float(v)) for a, v in zip(document["ar"], document["dtheta_075"]) if v is not None and math.isfinite(float(v))]
    finite = sorted(finite)
    grid = numpy.asarray([item[0] for item in finite], dtype=numpy.float64)
    values = numpy.asarray([item[1] for item in finite], dtype=numpy.float64)
    if tolerance != 0.001 or numpy.any(numpy.diff(grid) <= 0):
        raise ValueError("invalid frozen delta table")
    tail_constant = min(a * v for a, v in finite if a >= max(8.0, grid[-1] / 2.0))

    def lookup(aspect):
        aspect = numpy.asarray(aspect, dtype=numpy.float64)
        result = numpy.interp(aspect, grid, values)
        result[aspect < grid[0]] = numpy.inf
        high = aspect > grid[-1]
        result[high] = numpy.maximum(0.0, tail_constant / aspect[high] - 2.0 * tolerance)
        return result

    return lookup


def load_membership(cell: str):
    table = pandas.read_csv(SOURCE_M / cell / "image_universe.csv", dtype={"image_id": str})
    if table.image_id.duplicated().any() or table.d_cal_daudit_split_flag.isna().any():
        raise ValueError(f"bad image universe {cell}")
    members = set(table.loc[table.d_cal_daudit_split_flag.eq("D_audit"), "image_id"].astype(str))
    if not members:
        raise ValueError(f"empty image universe {cell}")
    return members


def reconstruct_cell(cell: str, members: set[str], tile_to_scene: dict[str, str], delta_lookup):
    raw_rows = []
    observed_keys = set()
    with (SOURCE_M / cell / "matched_fullval.jsonl").open("r", encoding="utf-8") as handle:
        for text in handle:
            record = json.loads(text)
            image = str(record["image_id"])
            prediction = int(record["pred_id"])
            identity = (image, prediction)
            if identity in observed_keys:
                raise ValueError(f"duplicate matched key {cell} {identity}")
            observed_keys.add(identity)
            if image not in members:
                continue
            if record["d_cal_daudit_split_flag"] != "D_audit":
                raise ValueError(f"membership conflict {cell} {identity}")
            pw, ph, pa = unpack_box(record["pred_obb"])
            gw, gh, ga = unpack_box(record["gt_obb"])
            if min(pw, ph, gw, gh) <= 0:
                raise ValueError(f"bad OBB {cell} {identity}")
            canonical_error = circular_distance(canonical_heading(pw, ph, pa), canonical_heading(gw, gh, ga))
            raw_error = circular_distance(pa, ga)
            if abs(canonical_error - float(record["angle_error"])) > 1e-8:
                raise ValueError(f"angle parity failure {cell} {identity}")
            raw_rows.append((image, prediction, len(raw_rows), max(gw, gh) / min(gw, gh), canonical_error, raw_error))
    base = pandas.DataFrame(raw_rows, columns=["image_id", "pred_id", "ordinal", "aspect", "canonical_error", "raw_error"])
    identity_index = pandas.MultiIndex.from_frame(base[["image_id", "pred_id"]])
    feature_columns = ["image_id", "pred_id", "detection_score", "u_axis", "missing_fraction", "iou_loss"]
    score_columns = ["image_id", "pred_id", "detection_score", "score_ar_size_linear"]
    features = pandas.read_parquet(SOURCE_R / "features" / f"{cell}.parquet", columns=feature_columns)
    scores = pandas.read_parquet(SOURCE_R / "scores" / f"{cell}.parquet", columns=score_columns)
    for table in (features, scores):
        table["image_id"] = table.image_id.astype(str)
        table["pred_id"] = table.pred_id.astype(numpy.int64)
        table.set_index(["image_id", "pred_id"], inplace=True, verify_integrity=True)
    selected_features = features.reindex(identity_index)
    selected_scores = scores.reindex(identity_index)
    if selected_features.isna().any().any() or selected_scores.isna().any().any():
        raise ValueError(f"RHS key missing {cell}")
    feature_detection = selected_features.detection_score.to_numpy(dtype=numpy.float64)
    score_detection = selected_scores.detection_score.to_numpy(dtype=numpy.float64)
    if not numpy.array_equal(feature_detection, score_detection):
        raise ValueError(f"score source mismatch {cell}")
    for source in (selected_features, selected_scores):
        if not numpy.isfinite(source.to_numpy(dtype=numpy.float64)).all():
            raise ValueError(f"nonfinite RHS {cell}")
    base["raw_confidence"] = feature_detection
    base["linear_source_frozen"] = selected_scores.score_ar_size_linear.to_numpy(dtype=numpy.float64)
    base["tta_angle"] = -selected_features.u_axis.to_numpy(dtype=numpy.float64)
    base["tta_localization"] = -(selected_features.missing_fraction.to_numpy(dtype=numpy.float64) + selected_features.iou_loss.to_numpy(dtype=numpy.float64))
    scale = numpy.maximum(delta_lookup(base.aspect.to_numpy(dtype=numpy.float64)), 1.0)
    base["normalized_risk"] = numpy.clip(base.canonical_error.to_numpy() / scale, 0.0, 3.0) / 3.0
    base["raw_theta_risk"] = numpy.clip(base.raw_error.to_numpy() / scale, 0.0, 3.0) / 3.0
    base["plain_angle_risk"] = numpy.clip(base.canonical_error.to_numpy() / 90.0, 0.0, 1.0)
    if CELL_DATASET[cell] == "SODA-A":
        try:
            base["cluster"] = [tile_to_scene[x] for x in base.image_id]
        except KeyError as error:
            raise ValueError(f"unmapped SODA tile {cell}: {error}") from error
    else:
        base["cluster"] = base.image_id
    audit = {
        "cell": cell,
        "base_rows": len(base),
        "feature_extras": len(features.index.difference(identity_index)),
        "score_extras": len(scores.index.difference(identity_index)),
    }
    return base, audit


def choose_rows(frame: pandas.DataFrame, variant: str):
    if variant in ("MAIN", "NO_LONGSIDE_AR21", "NO_GEONORM_AR21"):
        mask = frame.aspect.to_numpy() >= 2.1
    elif variant == "NORMALIZED_ALL_AR":
        mask = numpy.ones(len(frame), dtype=bool)
    elif variant == "NORMALIZED_AR16":
        mask = frame.aspect.to_numpy() >= 1.6
    elif variant == "NORMALIZED_AR13":
        mask = frame.aspect.to_numpy() >= 1.3
    else:
        raise KeyError(variant)
    return frame.loc[mask]


def choose_risk(frame: pandas.DataFrame, variant: str):
    if variant == "NO_LONGSIDE_AR21":
        return frame.raw_theta_risk.to_numpy(dtype=numpy.float64)
    if variant == "NO_GEONORM_AR21":
        return frame.plain_angle_risk.to_numpy(dtype=numpy.float64)
    return frame.normalized_risk.to_numpy(dtype=numpy.float64)


def make_pack(score, risk, cluster_number):
    order = numpy.argsort(-score, kind="stable")
    ordered_score = score[order]
    return {
        "risk": risk[order],
        "cluster": cluster_number[order],
        "starts": numpy.r_[0, numpy.flatnonzero(ordered_score[1:] != ordered_score[:-1]) + 1].astype(numpy.int64),
    }


def evaluate_pack(pack, cluster_multiplicity):
    weights = cluster_multiplicity[pack["cluster"]].astype(numpy.float64, copy=False)
    total = weights.sum()
    if total <= 0:
        raise ValueError("zero bootstrap mass")
    group_weight = numpy.add.reduceat(weights, pack["starts"])
    group_loss = numpy.add.reduceat(weights * pack["risk"], pack["starts"])
    keep = group_weight > 0
    group_weight = group_weight[keep]
    group_loss = group_loss[keep]
    cumulative_weight = numpy.cumsum(group_weight)
    cumulative_loss = numpy.cumsum(group_loss)
    generalized = cumulative_loss / total
    augrc = numpy.sum((numpy.r_[0.0, generalized[:-1]] + generalized) * (group_weight / total) / 2.0)
    output = [float(augrc)]
    for target in (0.70, 0.90):
        index = int(numpy.searchsorted(cumulative_weight, target * total, side="left"))
        output.append(float(cumulative_loss[index] / cumulative_weight[index]))
    return output


def full_set_swap(left_score, right_score, target):
    def accepted(score):
        order = numpy.argsort(-score, kind="stable")
        sorted_score = score[order]
        starts = numpy.r_[0, numpy.flatnonzero(sorted_score[1:] != sorted_score[:-1]) + 1]
        sizes = numpy.diff(numpy.r_[starts, len(score)])
        group = int(numpy.searchsorted(numpy.cumsum(sizes), target * len(score), side="left"))
        return score >= sorted_score[starts[group]]
    left = accepted(left_score)
    right = accepted(right_score)
    return float(numpy.count_nonzero(left ^ right) / numpy.count_nonzero(left | right))


def initialize_workers(packs, multiplicities):
    global WORK_PACKS, WORK_MULTIPLICITIES
    WORK_PACKS = packs
    WORK_MULTIPLICITIES = multiplicities


def run_chunk(bounds):
    first, last = bounds
    result = numpy.empty((last - first, 6, 6, 4, 3), dtype=numpy.float64)
    for out_index, replicate in enumerate(range(first, last)):
        for cell_index, cell in enumerate(CELLS):
            sampled = WORK_MULTIPLICITIES[CELL_DATASET[cell]][replicate]
            for variant_index, variant in enumerate(VARIANTS):
                for method_index, method in enumerate(METHODS):
                    result[out_index, cell_index, variant_index, method_index] = evaluate_pack(WORK_PACKS[(cell, variant, method)], sampled)
    return first, result


def percentile(values, probability):
    return float(numpy.quantile(values, probability, method="linear"))


def apply_holm(records):
    sequence = sorted(range(len(records)), key=lambda index: (records[index]["p_raw"], records[index]["hypothesis_key"]))
    running = 0.0
    total = len(records)
    for rank, index in enumerate(sequence, 1):
        running = max(running, min(1.0, (total - rank + 1) * records[index]["p_raw"]))
        records[index]["p_holm"] = running


def summarize(point_unit, point_dataset, bootstrap_unit, bootstrap_dataset, swaps, replicate_count):
    hypotheses = []
    for level in ("unit", "dataset"):
        keys = CELLS if level == "unit" else DATASETS
        points = point_unit if level == "unit" else point_dataset
        samples = bootstrap_unit if level == "unit" else bootstrap_dataset
        for key_index, key in enumerate(keys):
            for method in METHODS[1:]:
                method_index = METHODS.index(method)
                raw_index = METHODS.index("raw_confidence")
                for loss in LOSSES:
                    loss_index = LOSSES.index(loss)
                    for ablation in TEST_ABLATIONS:
                        ablation_index = VARIANTS.index(ablation)
                        dm = points[key]["MAIN"][method][loss] - points[key]["MAIN"]["raw_confidence"][loss]
                        da = points[key][ablation][method][loss] - points[key][ablation]["raw_confidence"][loss]
                        dm_boot = samples[:, key_index, 0, method_index, loss_index] - samples[:, key_index, 0, raw_index, loss_index]
                        da_boot = samples[:, key_index, ablation_index, method_index, loss_index] - samples[:, key_index, ablation_index, raw_index, loss_index]
                        dod = dm - da
                        dod_boot = dm_boot - da_boot
                        main_pair = (points[key]["MAIN"][method][loss], points[key]["MAIN"]["raw_confidence"][loss])
                        ablation_pair = (points[key][ablation][method][loss], points[key][ablation]["raw_confidence"][loss])
                        if loss == "AUGRC":
                            em = max(5e-4, 0.02 * max(abs(x) for x in main_pair))
                            ea = max(5e-4, 0.02 * max(abs(x) for x in ablation_pair))
                        else:
                            em = max(1e-3, 0.02 * max(abs(x) for x in main_pair))
                            ea = max(1e-3, 0.02 * max(abs(x) for x in ablation_pair))
                        hypotheses.append({
                            "level": level,
                            "key": key,
                            "contrast": method,
                            "endpoint": loss,
                            "ablation_id": ablation,
                            "effect_class": CLASS_OF[ablation],
                            "hypothesis_key": f"{level}|{key}|{method}|{loss}|{ablation}",
                            "delta_main": dm,
                            "delta_ablation": da,
                            "dod": dod,
                            "epsilon_main": em,
                            "epsilon_ablation": ea,
                            "delta_main_ci_low": percentile(dm_boot, 0.025),
                            "delta_main_ci_high": percentile(dm_boot, 0.975),
                            "delta_ablation_ci_low": percentile(da_boot, 0.025),
                            "delta_ablation_ci_high": percentile(da_boot, 0.975),
                            "dod_ci_low": percentile(dod_boot, 0.025),
                            "dod_ci_high": percentile(dod_boot, 0.975),
                            "p_raw": float((1 + numpy.count_nonzero(numpy.abs(dod_boot - dod) >= abs(dod))) / (replicate_count + 1)),
                            "main_swap70": swaps[level][key]["MAIN"][method][0.70],
                            "main_swap90": swaps[level][key]["MAIN"][method][0.90],
                            "ablation_swap70": swaps[level][key][ablation][method][0.70],
                            "ablation_swap90": swaps[level][key][ablation][method][0.90],
                        })
        apply_holm([row for row in hypotheses if row["level"] == level])
    for row in hypotheses:
        if row["delta_main"] < 0 < row["delta_ablation"]:
            direction = "PROBE_BETTER_MAIN__RAW_BETTER_ABLATION"
            ci_pass = row["delta_main_ci_high"] < -row["epsilon_main"] and row["delta_ablation_ci_low"] > row["epsilon_ablation"]
        elif row["delta_ablation"] < 0 < row["delta_main"]:
            direction = "RAW_BETTER_MAIN__PROBE_BETTER_ABLATION"
            ci_pass = row["delta_main_ci_low"] > row["epsilon_main"] and row["delta_ablation_ci_high"] < -row["epsilon_ablation"]
        else:
            direction = "NONE"
            ci_pass = False
        swap_pass = True
        if row["endpoint"] == "Risk@70":
            swap_pass = row["main_swap70"] >= 0.05 and row["ablation_swap70"] >= 0.05
        if row["endpoint"] == "Risk@90":
            swap_pass = row["main_swap90"] >= 0.05 and row["ablation_swap90"] >= 0.05
        row["supported_direction"] = direction
        row["witness"] = bool(ci_pass and row["p_holm"] < 0.05 and (row["dod_ci_low"] > 0 or row["dod_ci_high"] < 0) and abs(row["dod"]) >= row["epsilon_main"] + row["epsilon_ablation"] and swap_pass)
        row["full_signature"] = "|".join((row["effect_class"], row["ablation_id"], row["contrast"], row["endpoint"], direction)) if row["witness"] else ""
    return pandas.DataFrame(hypotheses)


def decide(hypotheses):
    witnesses = hypotheses[hypotheses.witness]
    units = witnesses[witnesses.level.eq("unit")]
    datasets = witnesses[witnesses.level.eq("dataset")]
    if units.empty and datasets.empty:
        state = "FAIL_GENERIC_OR_NULL"
        passing = []
    else:
        passing = []
        for signature in sorted(set(units.full_signature) & set(datasets.full_signature)):
            unit_part = units[units.full_signature.eq(signature)]
            dataset_part = datasets[datasets.full_signature.eq(signature)]
            detector_families = {CELL_DETECTOR[cell] for cell in unit_part.key}
            if dataset_part.key.nunique() >= 2 and unit_part.key.nunique() >= 4 and len(detector_families) >= 2 and "SODA-A" in set(dataset_part.key) and any(cell in ("E", "F") for cell in unit_part.key):
                passing.append(signature)
        state = "PASS_TO_EXTERNAL_CONFIRMATION" if passing else "INCONCLUSIVE_MIXED"
    return {
        "candidate_scientific_state": state,
        "unit_witnesses": int(len(units)),
        "dataset_witnesses": int(len(datasets)),
        "passing_signatures": passing,
        "formal_state": "RECOVERY_B_PENDING_COMPARATOR",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--replicates", required=True, type=int)
    parser.add_argument("--workers", default=39, type=int)
    arguments = parser.parse_args()
    if arguments.output.exists():
        raise SystemExit(f"output exists: {arguments.output}")
    arguments.output.mkdir(parents=True, mode=0o750)
    if len(os.sched_getaffinity(0)) != 48:
        raise SystemExit("implementation B requires 48-CPU job affinity")
    start_time = time.time()
    mapping = pandas.read_csv(SOURCE_R / "soda_tile_to_mother_r014.csv", dtype={"tile_id": str, "mother_scene_id": str})
    mapping.set_index("tile_id", inplace=True, verify_integrity=True)
    tile_to_scene = mapping.mother_scene_id.astype(str).to_dict()
    delta_lookup = make_delta_lookup()
    memberships = {cell: load_membership(cell) for cell in CELLS}
    frames = {}
    audits = []
    for cell in CELLS:
        frames[cell], audit = reconstruct_cell(cell, memberships[cell], tile_to_scene, delta_lookup)
        audits.append(audit)
    if not (memberships["A"] == memberships["B"] == memberships["C"]):
        raise ValueError("DIOR universes differ")
    soda_universe = {}
    for cell in ("E", "F"):
        soda_universe[cell] = byte_sort(tile_to_scene[tile] for tile in memberships[cell])
    if soda_universe["E"] != soda_universe["F"]:
        raise ValueError("SODA mother universes differ")
    cluster_lists = {}
    for cell in CELLS:
        if CELL_DATASET[cell] == "SODA-A":
            cluster_lists[cell] = soda_universe[cell]
        else:
            cluster_lists[cell] = byte_sort(memberships[cell])
    packs = {}
    points = {}
    swaps_unit = {}
    metric_records = []
    for cell in CELLS:
        cluster_index = {name: position for position, name in enumerate(cluster_lists[cell])}
        points[cell] = {}
        swaps_unit[cell] = {}
        for variant in VARIANTS:
            selected = choose_rows(frames[cell], variant)
            risk = choose_risk(selected, variant)
            clusters = numpy.asarray([cluster_index[str(name)] for name in selected.cluster], dtype=numpy.int32)
            points[cell][variant] = {}
            swaps_unit[cell][variant] = {}
            for method in METHODS:
                score = selected[method].to_numpy(dtype=numpy.float64)
                pack = make_pack(score, risk, clusters)
                packs[(cell, variant, method)] = pack
                values = evaluate_pack(pack, numpy.ones(len(cluster_index), dtype=numpy.int16))
                points[cell][variant][method] = dict(zip(LOSSES, values))
                metric_records.append({"level": "unit", "key": cell, "variant": variant, "method": method, "rows": len(selected), **points[cell][variant][method]})
                swaps_unit[cell][variant][method] = {
                    q: full_set_swap(score, selected.raw_confidence.to_numpy(dtype=numpy.float64), q) for q in (0.70, 0.90)
                }
    dataset_points = {}
    swaps_dataset = {}
    for dataset in DATASETS:
        cells = DATASET_CELLS[dataset]
        dataset_points[dataset] = {}
        swaps_dataset[dataset] = {}
        for variant in VARIANTS:
            dataset_points[dataset][variant] = {}
            swaps_dataset[dataset][variant] = {}
            for method in METHODS:
                dataset_points[dataset][variant][method] = {loss: float(numpy.mean([points[cell][variant][method][loss] for cell in cells])) for loss in LOSSES}
                swaps_dataset[dataset][variant][method] = {q: float(numpy.mean([swaps_unit[cell][variant][method][q] for cell in cells])) for q in (0.70, 0.90)}
                metric_records.append({"level": "dataset", "key": dataset, "variant": variant, "method": method, "rows": sum(len(choose_rows(frames[cell], variant)) for cell in cells), **dataset_points[dataset][variant][method]})
    pandas.DataFrame(audits).to_csv(arguments.output / "join_audit.csv", index=False)
    pandas.DataFrame(metric_records).to_csv(arguments.output / "metrics.csv", index=False)

    multiplicities = {}
    for dataset_number, dataset in enumerate(DATASETS):
        cluster_count = len(cluster_lists[DATASET_CELLS[dataset][0]])
        random = numpy.random.RandomState(RANDOM_SEED + dataset_number)
        array = numpy.empty((arguments.replicates, cluster_count), dtype=numpy.int16)
        for replicate in range(arguments.replicates):
            array[replicate] = numpy.bincount(random.randint(0, cluster_count, size=cluster_count), minlength=cluster_count)
        multiplicities[dataset] = array
    bootstrap_unit = numpy.empty((arguments.replicates, 6, 6, 4, 3), dtype=numpy.float64)
    chunk_width = math.ceil(arguments.replicates / arguments.workers)
    chunks = [(first, min(arguments.replicates, first + chunk_width)) for first in range(0, arguments.replicates, chunk_width)]
    with multiprocessing.get_context("fork").Pool(arguments.workers, initializer=initialize_workers, initargs=(packs, multiplicities)) as pool:
        for first, block in pool.imap_unordered(run_chunk, chunks):
            bootstrap_unit[first:first + len(block)] = block
    bootstrap_dataset = numpy.empty((arguments.replicates, 3, 6, 4, 3), dtype=numpy.float64)
    for dataset_index, dataset in enumerate(DATASETS):
        indices = [CELLS.index(cell) for cell in DATASET_CELLS[dataset]]
        bootstrap_dataset[:, dataset_index] = numpy.mean(bootstrap_unit[:, indices], axis=1)
    numpy.savez_compressed(arguments.output / "bootstrap_metrics.npz", unit=bootstrap_unit, dataset=bootstrap_dataset)
    swaps = {"unit": swaps_unit, "dataset": swaps_dataset}
    hypotheses = summarize(points, dataset_points, bootstrap_unit, bootstrap_dataset, swaps, arguments.replicates)
    hypotheses.to_csv(arguments.output / "hypotheses.csv", index=False)
    hypotheses[hypotheses.witness].to_csv(arguments.output / "witnesses.csv", index=False)
    gate = decide(hypotheses)
    gate["elapsed_seconds"] = time.time() - start_time
    (arguments.output / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    manifest = []
    for filename in sorted(arguments.output.iterdir()):
        if filename.is_file() and filename.name != "manifest.csv":
            manifest.append({"path": filename.name, "bytes": filename.stat().st_size, "sha256": file_hash(filename)})
    pandas.DataFrame(manifest).to_csv(arguments.output / "manifest.csv", index=False)
    print(json.dumps(gate, sort_keys=True))


if __name__ == "__main__":
    main()

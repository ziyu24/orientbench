#!/usr/bin/env python3
"""Aggregate the nine frozen FAIR1M final runs for Command 070."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
sys.path.insert(0, str(ROOT))
EVAL = ROOT / "outputs/persistent_artifacts/m4_third_dataset_070/eval"
CHECKPOINTS = ROOT / "outputs/persistent_artifacts/m4_third_dataset_070/checkpoints"
HEADS = ("PSC", "CSL", "DCL")
SEEDS = (0, 1, 2)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refuse empty output: {path}")
    fields = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, path)


def value(block: dict, key: str):
    item = block.get(key)
    return "" if item is None else item


def nrc(score: np.ndarray, risk: np.ndarray) -> float:
    from orientbench.metrics.nrc_auc import nrc_auc
    return float(nrc_auc(score, risk)["nrc_auc"])


def direction(value_: float) -> str:
    if not math.isfinite(value_):
        return "undefined"
    if value_ > 1.05:
        return "reversed"
    if value_ < 0.95:
        return "informative"
    return "near-random"


def main() -> int:
    evaluations = {}
    arrays = {}
    for head in HEADS:
        for seed in SEEDS:
            run_id = f"M4_070_final__{head}__FAIR1M__seed{seed}"
            json_path = EVAL / f"{run_id}.json"
            npz_path = EVAL / f"{run_id}_matched.npz"
            checkpoint = CHECKPOINTS / f"{run_id}.pth"
            if not all(path.is_file() and path.stat().st_size > 0 for path in (json_path, npz_path, checkpoint)):
                raise RuntimeError(f"incomplete final artifacts: {run_id}")
            evaluations[(head, seed)] = json.loads(json_path.read_text())
            arrays[(head, seed)] = dict(np.load(npz_path))

    seed_rows = []
    bootstrap_rows = []
    detailed_rows = []
    for head in HEADS:
        for seed in SEEDS:
            result = evaluations[(head, seed)]
            main_block = result["main_ar2.1"]
            row = {
                "run_id": result["run_id"], "head": head, "dataset": "FAIR1M-v1.0",
                "seed": seed, "native_signal": result["native_signal"], "status": result["evaluation_status"],
                "AP50": result["AP50"], "AP75": result["AP75"],
                "matched_instances": result["matched_instances"],
                "retained_count_ar21": main_block["retained_count"],
                "retained_ratio_ar21": main_block["retained_ratio"],
                "NRC_ar21": main_block["NRC_native"],
                "geometry_NRC_ar21": main_block["geometry_severe_NRC_native"],
                "AURC_ar21": main_block["AURC_native"],
                "Risk70_ar21": main_block["Risk70_native"],
                "Risk90_ar21": main_block["Risk90_native"],
                "mean_angle_error_ar21": main_block["mean_angle_error"],
                "geometry_severe_rate_ar21": main_block["geometry_severe_rate"],
                "NRC_ar16": result["sensitivity_ar1.6"]["NRC_native"],
                "NRC_ar13": result["sensitivity_ar1.3"]["NRC_native"],
                "NRC_direction_ar21": direction(float(main_block["NRC_native"])),
                "NRC_direction_ar16": direction(float(result["sensitivity_ar1.6"]["NRC_native"])),
                "NRC_direction_ar13": direction(float(result["sensitivity_ar1.3"]["NRC_native"])),
                "checkpoint_sha256": sha256(CHECKPOINTS / f"{result['run_id']}.pth"),
                "eval_sha256": sha256(EVAL / f"{result['run_id']}.json"),
                "matched_npz_sha256": sha256(EVAL / f"{result['run_id']}_matched.npz"),
            }
            seed_rows.append(row)
            for endpoint, key in (("angle_error_NRC", "NRC_native_image_cluster_CI"),
                                  ("geometry_severe_NRC", "geometry_NRC_image_cluster_CI")):
                interval = main_block[key]
                bootstrap_rows.append({
                    "run_id": result["run_id"], "head": head, "seed": seed,
                    "dataset": "FAIR1M-v1.0", "endpoint": endpoint, "estimate": (
                        main_block["NRC_native"] if endpoint == "angle_error_NRC"
                        else main_block["geometry_severe_NRC_native"]),
                    "ci_lo": interval[0], "ci_hi": interval[1],
                    "unit": "complete_evaluation_image", "replicates": 800,
                })

            data = arrays[(head, seed)]
            score = data["native"].astype(float)
            error = data["error"].astype(float)
            ar = data["ar"].astype(float)
            size = data["size"].astype(float)
            class_id = data["class_id"].astype(int)
            scopes = [
                ("overall", "ar>=2.1", ar >= 2.1),
                ("size", "small", (ar >= 2.1) & (size < 32 ** 2)),
                ("size", "medium", (ar >= 2.1) & (size >= 32 ** 2) & (size < 96 ** 2)),
                ("size", "large", (ar >= 2.1) & (size >= 96 ** 2)),
                ("ar_bin", "2.1<=ar<3", (ar >= 2.1) & (ar < 3.0)),
                ("ar_bin", "3<=ar<5", (ar >= 3.0) & (ar < 5.0)),
                ("ar_bin", "ar>=5", ar >= 5.0),
            ]
            for cls in sorted(set(class_id.tolist())):
                scopes.append(("class", str(cls), (ar >= 2.1) & (class_id == cls)))
            for scope, group, mask in scopes:
                if int(mask.sum()) < 100:
                    continue
                estimate = nrc(score[mask], error[mask])
                detailed_rows.append({
                    "head": head, "dataset": "FAIR1M-v1.0", "seed": seed,
                    "scope": scope, "group": group, "n": int(mask.sum()),
                    "NRC_native": estimate, "direction": direction(estimate),
                    "main_mask": "matched_GT_ar>=2.1",
                })

    variance_rows = []
    head_flags = {}
    for head in HEADS:
        subset = [row for row in seed_rows if row["head"] == head]
        values = np.asarray([float(row["NRC_ar21"]) for row in subset])
        ci_lows = [float(next(row["ci_lo"] for row in bootstrap_rows
                             if row["run_id"] == seed_row["run_id"] and row["endpoint"] == "angle_error_NRC"))
                   for seed_row in subset]
        ci_highs = [float(next(row["ci_hi"] for row in bootstrap_rows
                              if row["run_id"] == seed_row["run_id"] and row["endpoint"] == "angle_error_NRC"))
                    for seed_row in subset]
        variance_rows.append({
            "head": head, "dataset": "FAIR1M-v1.0", "n_seeds": 3,
            "mean_NRC_ar21": float(values.mean()), "std_NRC_ar21": float(values.std()),
            "min_NRC_ar21": float(values.min()), "max_NRC_ar21": float(values.max()),
            "all_seed_NRC_gt1": bool(np.all(values > 1.0)),
            "all_seed_CI_lo_gt1": all(item > 1.0 for item in ci_lows),
            "all_seed_NRC_lt1": bool(np.all(values < 1.0)),
            "all_seed_CI_hi_lt1": all(item < 1.0 for item in ci_highs),
            "sensitivity_direction_consistent": all(
                row["NRC_direction_ar21"] == row["NRC_direction_ar16"] == row["NRC_direction_ar13"]
                for row in subset),
        })
        head_flags[head] = variance_rows[-1]

    psc_strata = [row for row in detailed_rows if row["head"] == "PSC" and row["scope"] in ("size", "ar_bin")]
    size_support = len({row["group"] for row in psc_strata if row["scope"] == "size" and row["direction"] == "reversed"})
    ar_support = len({row["group"] for row in psc_strata if row["scope"] == "ar_bin" and row["direction"] == "reversed"})
    psc_replicates = head_flags["PSC"]["all_seed_CI_lo_gt1"]
    csl_not_reverse = not head_flags["CSL"]["all_seed_CI_lo_gt1"]
    dcl_informative = head_flags["DCL"]["all_seed_NRC_lt1"]
    if psc_replicates and csl_not_reverse and dcl_informative and size_support >= 2 and ar_support >= 2:
        decision = "REPLICATES_A"
    elif head_flags["PSC"]["all_seed_NRC_gt1"] and csl_not_reverse:
        decision = "PARTIAL_REPLICATION"
    else:
        decision = "DOES_NOT_REPLICATE"
    detailed_rows.append({
        "head": "ALL", "dataset": "FAIR1M-v1.0", "seed": "ALL", "scope": "decision",
        "group": decision, "n": sum(int(row["retained_count_ar21"]) for row in seed_rows),
        "NRC_native": "", "direction": "",
        "main_mask": "matched_GT_ar>=2.1",
        "evidence": (f"PSC_all_CIlo_gt1={psc_replicates}; CSL_stable_reverse={not csl_not_reverse}; "
                     f"DCL_all_NRC_lt1={dcl_informative}; PSC_reversed_size_groups={size_support}; "
                     f"PSC_reversed_ar_groups={ar_support}"),
    })

    write_csv(ROOT / "reports/m4_third_dataset_seed_results.csv", seed_rows)
    write_csv(ROOT / "reports/m4_third_dataset_seed_variance.csv", variance_rows)
    write_csv(ROOT / "reports/m4_third_dataset_bootstrap_intervals.csv", bootstrap_rows)
    write_csv(ROOT / "reports/m4_optional_third_dataset_results.csv", detailed_rows)

    artifacts = []
    roles = [
        (ROOT / "docs/m4_optional_third_dataset_extension.md", "frozen protocol"),
        (ROOT / "reports/m4_third_dataset_pilot_results.csv", "pilot results"),
        (ROOT / "reports/m4_third_dataset_lr_selection.csv", "LR selection"),
        (ROOT / "reports/m4_third_dataset_seed_results.csv", "seed results"),
        (ROOT / "reports/m4_third_dataset_seed_variance.csv", "seed variance"),
        (ROOT / "reports/m4_third_dataset_bootstrap_intervals.csv", "image cluster bootstrap"),
        (ROOT / "reports/m4_optional_third_dataset_results.csv", "strata and decision"),
    ]
    for head in HEADS:
        roles.append((ROOT / f"configs/m4_third_dataset_070/fair1m_{head.lower()}.py", "frozen config"))
        for seed in SEEDS:
            run_id = f"M4_070_final__{head}__FAIR1M__seed{seed}"
            roles.extend([
                (CHECKPOINTS / f"{run_id}.pth", "weights-only final checkpoint"),
                (EVAL / f"{run_id}.json", "full-val evaluation"),
                (EVAL / f"{run_id}_matched.npz", "compressed matched native endpoint"),
                (ROOT / f"logs/m4_third_dataset/final/{run_id}.log", "training and evaluation log"),
            ])
    for path, role in roles:
        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError(f"missing artifact: {path}")
        artifacts.append({
            "artifact": str(path.relative_to(ROOT)), "role": role, "bytes": path.stat().st_size,
            "sha256": sha256(path), "status": "COMPLETE", "persistent": True,
            "can_recompute": True, "depends_on_dev_shm": False,
        })
    write_csv(ROOT / "reports/m4_third_dataset_artifact_manifest.csv", artifacts)

    document = ROOT / "docs/m4_optional_third_dataset_extension.md"
    protocol = document.read_text().split("\n## Final frozen result", 1)[0].rstrip()
    summary = [
        "", "## Final frozen result", "",
        f"- Third-dataset decision: **{decision}**.",
        f"- PSC: mean NRC={head_flags['PSC']['mean_NRC_ar21']:.4f}; all seeds CI lower >1: {head_flags['PSC']['all_seed_CI_lo_gt1']}.",
        f"- CSL: mean NRC={head_flags['CSL']['mean_NRC_ar21']:.4f}; stable reverse: {head_flags['CSL']['all_seed_CI_lo_gt1']}.",
        f"- DCL: mean NRC={head_flags['DCL']['mean_NRC_ar21']:.4f}; all seeds NRC<1: {head_flags['DCL']['all_seed_NRC_lt1']}.",
        f"- PSC support spans {size_support} fixed size groups and {ar_support} exclusive aspect-ratio groups; it is not attributed to one such layer.",
        "- Historical K2 outcome A is not modified; this extension only changes its cross-dataset scope.",
    ]
    document.write_text(protocol + "\n" + "\n".join(summary) + "\n")
    for item in artifacts:
        if item["artifact"] == "docs/m4_optional_third_dataset_extension.md":
            item["bytes"] = document.stat().st_size
            item["sha256"] = sha256(document)
    write_csv(ROOT / "reports/m4_third_dataset_artifact_manifest.csv", artifacts)
    print(f"M4_070_AGGREGATE_DONE decision={decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

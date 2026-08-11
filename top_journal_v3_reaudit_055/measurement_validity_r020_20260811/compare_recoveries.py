#!/usr/bin/env python3
"""Comparator C for independently generated pragmatic recovery A and B."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest(root: Path) -> str:
    manifest_path = root / "manifest.csv"
    manifest = pd.read_csv(manifest_path)
    for row in manifest.to_dict("records"):
        target = root / row["path"]
        if target.stat().st_size != int(row["bytes"]) or sha256(target) != row["sha256"]:
            raise SystemExit(f"manifest mismatch: {target}")
    return sha256(manifest_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", type=Path, required=True)
    parser.add_argument("--b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    args.output.mkdir(parents=True, mode=0o750)
    a_manifest = validate_manifest(args.a)
    b_manifest = validate_manifest(args.b)

    arrays_a = np.load(args.a / "bootstrap_metrics.npz")
    arrays_b = np.load(args.b / "bootstrap_metrics.npz")
    array_results = {}
    for level in ("unit", "dataset"):
        if arrays_a[level].shape != arrays_b[level].shape:
            raise SystemExit(f"bootstrap shape mismatch {level}")
        difference = np.abs(arrays_a[level] - arrays_b[level])
        maximum = float(difference.max())
        if not np.allclose(arrays_a[level], arrays_b[level], atol=1e-10, rtol=0):
            raise SystemExit(f"bootstrap parity mismatch {level}: {maximum}")
        array_results[level] = {"shape": list(arrays_a[level].shape), "max_abs_diff": maximum}

    metrics_a = pd.read_csv(args.a / "metrics.csv").rename(columns={"cohort": "variant", "probe": "method"})
    metrics_b = pd.read_csv(args.b / "metrics.csv")
    metric_keys = ["level", "key", "variant", "method"]
    metrics_a = metrics_a.sort_values(metric_keys).reset_index(drop=True)
    metrics_b = metrics_b.sort_values(metric_keys).reset_index(drop=True)
    if not metrics_a[metric_keys].equals(metrics_b[metric_keys]) or not np.array_equal(metrics_a.rows, metrics_b.rows):
        raise SystemExit("point metric key/count mismatch")
    metric_diffs = {}
    for column in ("AUGRC", "Risk@70", "Risk@90"):
        difference = np.abs(metrics_a[column] - metrics_b[column])
        metric_diffs[column] = float(difference.max())
        if not np.allclose(metrics_a[column], metrics_b[column], atol=1e-10, rtol=0):
            raise SystemExit(f"point metric mismatch {column}")

    join_a = pd.read_csv(args.a / "join_audit.csv").rename(columns={"unit": "cell"}).sort_values("cell").reset_index(drop=True)
    join_b = pd.read_csv(args.b / "join_audit.csv").sort_values("cell").reset_index(drop=True)
    for column in ("base_rows", "feature_extras", "score_extras"):
        if not np.array_equal(join_a[column], join_b[column]):
            raise SystemExit(f"join audit mismatch {column}")

    hypothesis_a = pd.read_csv(args.a / "hypotheses.csv").sort_values("hypothesis_key").reset_index(drop=True)
    hypothesis_b = pd.read_csv(args.b / "hypotheses.csv").sort_values("hypothesis_key").reset_index(drop=True)
    if not hypothesis_a.hypothesis_key.equals(hypothesis_b.hypothesis_key) or len(hypothesis_a) != 405:
        raise SystemExit("hypothesis key mismatch")
    hypothesis_diffs = {}
    numeric = (
        "delta_main", "delta_ablation", "dod", "epsilon_main", "epsilon_ablation",
        "delta_main_ci_low", "delta_main_ci_high", "delta_ablation_ci_low", "delta_ablation_ci_high",
        "dod_ci_low", "dod_ci_high", "p_raw", "p_holm", "main_swap70", "main_swap90",
        "ablation_swap70", "ablation_swap90",
    )
    for column in numeric:
        difference = np.abs(hypothesis_a[column] - hypothesis_b[column])
        hypothesis_diffs[column] = float(difference.max())
        if not np.allclose(hypothesis_a[column], hypothesis_b[column], atol=1e-10, rtol=0):
            raise SystemExit(f"hypothesis numeric mismatch {column}")
    for column in ("effect_class", "supported_direction", "witness", "full_signature"):
        left = hypothesis_a[column].fillna("")
        right = hypothesis_b[column].fillna("")
        if not left.equals(right):
            raise SystemExit(f"hypothesis exact mismatch {column}")

    gate_a = json.loads((args.a / "gate.json").read_text())
    gate_b = json.loads((args.b / "gate.json").read_text())
    gate_fields = ("candidate_scientific_state", "unit_witnesses", "dataset_witnesses", "passing_signatures")
    for field in gate_fields:
        if gate_a[field] != gate_b[field]:
            raise SystemExit(f"gate mismatch {field}")
    output = {
        "schema": "orientbench-r020-pragmatic-comparator-v1",
        "status": "PASS",
        "comparison_tolerance": {"atol": 1e-10, "rtol": 0},
        "implementation_a_manifest_sha256": a_manifest,
        "implementation_b_manifest_sha256": b_manifest,
        "bootstrap": array_results,
        "point_metric_max_abs_diff": metric_diffs,
        "hypothesis_max_abs_diff": hypothesis_diffs,
        "hypothesis_count": len(hypothesis_a),
        "witness_count": int(hypothesis_a.witness.sum()),
        "candidate_scientific_state": gate_a["candidate_scientific_state"],
        "unit_witnesses": gate_a["unit_witnesses"],
        "dataset_witnesses": gate_a["dataset_witnesses"],
        "passing_signatures": gate_a["passing_signatures"],
        "formal_state": "RECOVERY_AB_PARITY_PENDING_SUPERVISOR",
    }
    (args.output / "comparator.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Traceable AST reference probe for pinned fd-shifts generalized risk/AUGRC."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np


COMMIT = "c4467aec134e99691359da209f811d91283fc1e3"
EXPECTED = {
    "fd_shifts/analysis/rc_stats.py": ("563be2ed8652c730dd940eb241d8642717e25c0d", "d7f823c58bae5bbee4af2c0b5296bea41d6494884bd868d859890e9ccac22619"),
    "fd_shifts/analysis/rc_stats_utils.py": ("9f99c499f370b587d0ca73e2d9679a358de55e05", "a827fcf36d278beccc804e0d1895428f920c746dcc316a19f81bf3f341276b1f"),
}


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repository: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repository), *args], text=True).strip()


def extract_function(source: str, name: str):
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(selected) != 1:
        raise RuntimeError(f"function not found exactly once: {name}")
    module = ast.Module(body=[selected[0]], type_ignores=[])
    namespace = {"np": np}
    exec(compile(ast.fix_missing_locations(module), "pinned:rc_stats_utils.py", "exec"), namespace)
    return namespace[name], ast.get_source_segment(source, selected[0])


def display_scale(source: str) -> int:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "AUC_DISPLAY_SCALE":
            return int(ast.literal_eval(node.value))
    raise RuntimeError("AUC_DISPLAY_SCALE not found")


def local_curve(confidence, residual):
    confidence = np.asarray(confidence, dtype=float)
    residual = np.asarray(residual, dtype=float)
    order = np.argsort(-confidence, kind="stable")
    score = confidence[order]
    risk = residual[order]
    starts = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    count = np.diff(np.r_[starts, len(score)])
    risk_sum = np.add.reduceat(risk, starts)
    coverage = np.r_[0.0, np.cumsum(count) / len(score)]
    generalized = np.r_[0.0, np.cumsum(risk_sum) / len(score)]
    return coverage, generalized, float(np.trapz(generalized, coverage))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    if git(args.repository, "rev-parse", "HEAD") != COMMIT or git(args.repository, "status", "--porcelain=v1"):
        raise SystemExit("reference checkout identity/cleanliness failure")
    identities = {}
    sources = {}
    for relative, (expected_blob, expected_sha) in EXPECTED.items():
        data = (args.repository / relative).read_bytes()
        blob = git(args.repository, "rev-parse", f"HEAD:{relative}")
        raw_sha = hash_bytes(data)
        if blob != expected_blob or raw_sha != expected_sha:
            raise SystemExit(f"reference source identity failure: {relative}")
        identities[relative] = {"git_blob": blob, "sha256": raw_sha, "bytes": len(data)}
        sources[relative] = data.decode("utf-8")
    generalized_risk_stats, function_span = extract_function(sources["fd_shifts/analysis/rc_stats_utils.py"], "generalized_risk_stats")
    scale = display_scale(sources["fd_shifts/analysis/rc_stats.py"])
    if scale != 1000:
        raise SystemExit("reference display scale mismatch")
    vectors = {
        "tie": ([0.9, 0.9, 0.2], [0.1, 0.5, 0.9]),
        "binary": ([0.8, 0.4, 0.1], [0.0, 1.0, 0.0]),
        "continuous": ([0.99, 0.7, 0.3, 0.2], [0.2, 0.8, 0.1, 0.6]),
        "boundary": ([0.5], [0.75]),
    }
    results = []
    for name, (confidence, residual) in vectors.items():
        stats = generalized_risk_stats(confids=np.asarray(confidence, dtype=float), residuals=np.asarray(residual, dtype=float))
        reference_display = float(-np.trapz(stats["risks"], stats["coverages"]) * scale)
        coverage, generalized, local_unscaled = local_curve(confidence, residual)
        reference_unscaled = reference_display / scale
        passed = bool(abs(reference_unscaled - local_unscaled) <= 1e-12)
        if not passed:
            raise SystemExit(f"reference vector mismatch: {name}")
        results.append({
            "case": name,
            "reference_coverages_desc": stats["coverages"].tolist(),
            "reference_generalized_risks_desc": stats["risks"].tolist(),
            "local_coverages_asc": coverage.tolist(),
            "local_generalized_risks_asc": generalized.tolist(),
            "reference_augrc_display": reference_display,
            "reference_augrc_unscaled": reference_unscaled,
            "local_augrc_unscaled": local_unscaled,
            "atol": 1e-12,
            "rtol": 0,
            "pass": passed,
        })
    payload = {
        "schema": "orientbench-r020-reference-probe-v1",
        "status": "PASS",
        "remote": "https://github.com/IML-DKFZ/fd-shifts.git",
        "commit": COMMIT,
        "detached": git(args.repository, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD",
        "identities": identities,
        "adapter": {
            "type": "AST_EXACT_FUNCTION_SPAN",
            "function": "generalized_risk_stats",
            "source_span_sha256": hash_bytes(function_span.encode("utf-8")),
            "AUC_DISPLAY_SCALE": scale,
        },
        "vectors": results,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": payload["status"], "vectors": len(results), "AUC_DISPLAY_SCALE": scale}, sort_keys=True))


if __name__ == "__main__":
    main()

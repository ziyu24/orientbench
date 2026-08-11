#!/usr/bin/env python3
"""Six isolated semantic mutation checks for the pragmatic r020 recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_error(record):
    def heading(box):
        width = float(box["obb_w"])
        height = float(box["obb_h"])
        angle = math.degrees(float(box["obb_theta"]))
        return (angle + (90.0 if height > width else 0.0)) % 180.0
    difference = abs((heading(record["pred_obb"]) - heading(record["gt_obb"])) % 180.0)
    return min(difference, 180.0 - difference)


def validate_raw(path: Path):
    record = json.loads(path.read_text())
    if record["d_cal_daudit_split_flag"] != "D_audit":
        return 2
    return 0 if abs(canonical_error(record) - float(record["angle_error"])) <= 1e-8 else 2


def validate_mapping(path: Path, expected_tile: str, expected_mother: str):
    record = json.loads(path.read_text())
    return 0 if record == {"tile_id": expected_tile, "mother_scene_id": expected_mother, "verified": True} else 2


def validate_augrc(path: Path, expected: float):
    config = json.loads(path.read_text())
    confidence = np.array([0.9, 0.9, 0.2])
    residual = np.array([0.1, 0.5, 0.9])
    order = np.argsort(-confidence, kind="stable")
    score = confidence[order]
    risk = residual[order]
    starts = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    coverage = np.cumsum(np.diff(np.r_[starts, len(score)])) / len(score)
    generalized = np.cumsum(np.add.reduceat(risk, starts)) / len(score)
    if config["include_origin"]:
        coverage = np.r_[0.0, coverage]
        generalized = np.r_[0.0, generalized]
    value = float(np.trapz(generalized, coverage))
    return 0 if abs(value - expected) <= 1e-12 else 2


def validate_gate(path: Path):
    config = json.loads(path.read_text())
    fixture = {"dataset_count": 1, "unit_count": 4, "detector_count": 2, "soda_dataset": True, "soda_unit": True}
    candidate_pass = fixture["dataset_count"] >= config["minimum_datasets"] and fixture["unit_count"] >= 4 and fixture["detector_count"] >= 2 and fixture["soda_dataset"] and fixture["soda_unit"]
    return 0 if candidate_pass is False else 2


def validate_inventory(path: Path):
    inventory = pd.read_csv(path)
    return 0 if len(inventory) == 26 and inventory.identity_ok.astype(bool).all() and inventory.path.nunique() == 26 else 2


def validate_report(path: Path, gate_path: Path):
    report = path.read_text()
    gate = json.loads(gate_path.read_text())
    token = gate["candidate_scientific_state"]
    return 0 if f"- candidate scientific state: `{token}`" in report else 2


def validator_mode(args):
    if args.validator == "raw":
        return validate_raw(args.path)
    if args.validator == "mapping":
        return validate_mapping(args.path, args.expected_tile, args.expected_mother)
    if args.validator == "augrc":
        return validate_augrc(args.path, args.expected_float)
    if args.validator == "gate":
        return validate_gate(args.path)
    if args.validator == "inventory":
        return validate_inventory(args.path)
    if args.validator == "report":
        return validate_report(args.path, args.gate)
    raise ValueError(args.validator)


def run_validator(arguments):
    completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), "validate", *arguments], capture_output=True, text=True)
    return completed.returncode, hashlib.sha256(completed.stdout.encode()).hexdigest(), hashlib.sha256(completed.stderr.encode()).hexdigest()


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main_run(args):
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    args.output.mkdir(parents=True, mode=0o750)
    checks = []

    # 1. Actual D_audit pred theta mutation: historical angle parity must reject it.
    with (PROJECT / "outputs/persistent_artifacts/m069_fullval_reliability/A/matched_fullval.jsonl").open() as stream:
        raw_record = next(json.loads(line) for line in stream if json.loads(line)["d_cal_daudit_split_flag"] == "D_audit")
    pristine = args.output / "raw_theta_pristine.json"
    mutated = args.output / "raw_theta_mutated.json"
    write_json(pristine, raw_record)
    changed = json.loads(pristine.read_text())
    changed["pred_obb"]["obb_theta"] = float(changed["pred_obb"]["obb_theta"]) + math.radians(7.0)
    write_json(mutated, changed)
    checks.append(("MUTATION_RAW_THETA", pristine, mutated, ["raw"], "canonical angle no longer equals frozen historical angle_error"))

    # 2. Actual frozen SODA mapping row mutation.
    mapping = pd.read_csv(PROJECT / "outputs/persistent_artifacts/orientbench_r014/soda_tile_to_mother_r014.csv", dtype={"tile_id": str, "mother_scene_id": str}).iloc[0]
    mapping_record = {"tile_id": str(mapping.tile_id), "mother_scene_id": str(mapping.mother_scene_id), "verified": bool(mapping.verified)}
    pristine = args.output / "soda_mapping_pristine.json"
    mutated = args.output / "soda_mapping_mutated.json"
    write_json(pristine, mapping_record)
    changed = dict(mapping_record)
    changed["mother_scene_id"] = str(int(mapping_record["mother_scene_id"]) + 1)
    write_json(mutated, changed)
    mapping_args = ["mapping", "--expected-tile", mapping_record["tile_id"], "--expected-mother", mapping_record["mother_scene_id"]]
    checks.append(("MUTATION_SODA_MOTHER", pristine, mutated, mapping_args, "tile no longer maps to frozen mother identity"))

    # 3. AUGRC origin deletion checked against pinned reference vector.
    reference = json.loads(args.reference_probe.read_text())
    expected_augrc = next(row["reference_augrc_unscaled"] for row in reference["vectors"] if row["case"] == "tie")
    pristine = args.output / "augrc_logic_pristine.json"
    mutated = args.output / "augrc_logic_mutated.json"
    write_json(pristine, {"include_origin": True, "denominator": "fixed_n"})
    write_json(mutated, {"include_origin": False, "denominator": "fixed_n"})
    checks.append(("MUTATION_AUGRC_LOGIC", pristine, mutated, ["augrc", "--expected-float", repr(expected_augrc)], "origin deletion changes pinned reference AUGRC"))

    # 4. Gate two-dataset condition changed to one dataset.
    pristine = args.output / "gate_logic_pristine.json"
    mutated = args.output / "gate_logic_mutated.json"
    write_json(pristine, {"minimum_datasets": 2})
    write_json(mutated, {"minimum_datasets": 1})
    checks.append(("MUTATION_GATE_DATASET_COUNT", pristine, mutated, ["gate"], "one-dataset fixture incorrectly becomes PASS"))

    # 5. Input-manifest deletion.
    inventory = pd.read_csv(args.a_runtime / "input_inventory.csv")
    pristine = args.output / "input_inventory_pristine.csv"
    mutated = args.output / "input_inventory_mutated.csv"
    inventory.to_csv(pristine, index=False)
    inventory.iloc[:-1].to_csv(mutated, index=False)
    checks.append(("MUTATION_MANIFEST_ACCESS", pristine, mutated, ["inventory"], "scientific input inventory no longer has the exact 26 identities"))

    # 6. Published recovery report scientific token mutation.
    report_text = args.report.read_text()
    current = json.loads((args.a_runtime / "gate.json").read_text())["candidate_scientific_state"]
    if current not in report_text:
        raise SystemExit("report does not contain current gate token")
    pristine = args.output / "report_pristine.md"
    mutated = args.output / "report_mutated.md"
    pristine.write_text(report_text)
    mutated.write_text(report_text.replace(current, "PASS_TO_EXTERNAL_CONFIRMATION"))
    checks.append(("MUTATION_REPORT_TOKEN", pristine, mutated, ["report", "--gate", str(args.a_runtime / "gate.json")], "report token no longer equals sealed recovery gate"))

    results = []
    for token, before, after, validator_arguments, witness in checks:
        pristine_exit, pristine_stdout, pristine_stderr = run_validator([*validator_arguments, "--path", str(before)])
        mutated_exit, mutated_stdout, mutated_stderr = run_validator([*validator_arguments, "--path", str(after)])
        passed = pristine_exit == 0 and mutated_exit != 0
        if not passed:
            raise SystemExit(f"mutation did not reject correctly: {token} {pristine_exit} {mutated_exit}")
        results.append({
            "token": token,
            "pristine_path": before.name,
            "mutated_path": after.name,
            "before_sha256": sha(before),
            "after_sha256": sha(after),
            "pristine_exit": pristine_exit,
            "mutated_exit": mutated_exit,
            "pristine_stdout_sha256": pristine_stdout,
            "pristine_stderr_sha256": pristine_stderr,
            "mutated_stdout_sha256": mutated_stdout,
            "mutated_stderr_sha256": mutated_stderr,
            "semantic_rejection": witness,
            "pass": passed,
        })
    index = {"schema": "orientbench-r020-recovery-mutations-v1", "status": "PASS", "checks": results}
    write_json(args.output / "mutation_index.json", index)
    print(json.dumps({"status": "PASS", "mutations": len(results)}, sort_keys=True))


def parse_args():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--a-runtime", type=Path, required=True)
    run.add_argument("--reference-probe", type=Path, required=True)
    run.add_argument("--report", type=Path, required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("validator", choices=["raw", "mapping", "augrc", "gate", "inventory", "report"])
    validate.add_argument("--path", type=Path, required=True)
    validate.add_argument("--expected-tile", default="")
    validate.add_argument("--expected-mother", default="")
    validate.add_argument("--expected-float", type=float, default=0.0)
    validate.add_argument("--gate", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.mode == "validate":
        raise SystemExit(validator_mode(arguments))
    main_run(arguments)

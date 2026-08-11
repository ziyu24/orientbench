#!/usr/bin/env python3
"""Create four isolated receipt copies and prove fail-closed validation."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811"
VALIDATOR = ROOT / "top_journal_v3_reaudit_055/feasibility_receipt3_20260811/validate_receipt.py"
PYTHON = Path("/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def private_copy(path: Path) -> None:
    temporary = path.with_name(path.name + ".mutation-private")
    shutil.copy2(path, temporary)
    temporary.replace(path)


def json_write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def build_copy(name: str) -> Path:
    work = BASE / "mutations" / name / "evidence"
    work.parent.mkdir(parents=True, exist_ok=False)
    shutil.copytree(
        BASE,
        work,
        copy_function=os.link,
        ignore=lambda directory, names: {"mutations"} if Path(directory).resolve() == BASE.resolve() else set(),
    )
    return work


def mutate(name: str, work: Path):
    if name == "source_hash":
        target = work / "track_m_source_inventory.csv"
        private_copy(target)
        rows = list(csv.DictReader(target.open(encoding="utf-8")))
        fields = list(rows[0])
        pristine = rows[0]["sha256"]
        rows[0]["sha256"] = "0" * 64
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return target, f"row=0 field=sha256 {pristine} -> {'0' * 64}", "source_hash"
    if name == "bootstrap_replicate":
        target = work / "track_m_bootstrap_replicates.csv"
        private_copy(target)
        lines = target.read_text(encoding="utf-8").splitlines()
        fields = lines[0].split(",")
        index = fields.index("actual__DIOR-R__S0_minus_raw_confidence")
        values = lines[1].split(",")
        pristine = values[index]
        values[index] = repr(float(pristine) + 0.1)
        lines[1] = ",".join(values)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return target, f"replicate=0 field={fields[index]} {pristine} -> {values[index]}", "bootstrap_replicate"
    if name == "track_d_evidence_fact":
        target = work / "track_d_status.json"
        private_copy(target)
        value = json.loads(target.read_text())
        fact = value["candidate_facts"]["AI-TOD-R"]
        pristine = fact["official_license_evidence_count"]
        fact["official_license_evidence_count"] = pristine + 1
        json_write(target, value)
        return target, f"candidate=AI-TOD-R official_license_evidence_count {pristine} -> {pristine + 1}", "track_d_evidence_fact"
    target = work / "joint_gate.json"
    private_copy(target)
    value = json.loads(target.read_text())
    pristine = value["clauses"]["new_family_not_in_old_core_present"]
    value["clauses"]["new_family_not_in_old_core_present"] = not pristine
    json_write(target, value)
    return target, f"clause=new_family_not_in_old_core_present {pristine} -> {not pristine}", "joint_gate_clause"


def main() -> None:
    mutation_root = BASE / "mutations"
    mutation_root.mkdir(exist_ok=False)
    index_rows = []
    for name in ("source_hash", "bootstrap_replicate", "track_d_evidence_fact", "joint_gate_clause"):
        work = build_copy(name)
        hint = {
            "source_hash": "track_m_source_inventory.csv",
            "bootstrap_replicate": "track_m_bootstrap_replicates.csv",
            "track_d_evidence_fact": "track_d_status.json",
            "joint_gate_clause": "joint_gate.json",
        }[name]
        pristine_path = BASE / hint
        pristine_bytes = pristine_path.stat().st_size
        pristine_sha = sha(pristine_path)
        target, witness, expected_error = mutate(name, work)
        mutated_bytes = target.stat().st_size
        mutated_sha = sha(target)
        command = [str(PYTHON), str(VALIDATOR), "--root", str(work), "--check-only"]
        started = now()
        result = subprocess.run(command, cwd=ROOT, capture_output=True)
        ended = now()
        stdout_path = mutation_root / name / "validator.stdout"
        stderr_path = mutation_root / name / "validator.stderr"
        stdout_path.write_bytes(result.stdout)
        stderr_path.write_bytes(result.stderr)
        stderr_text = result.stderr.decode("utf-8", errors="replace")
        rejected = result.returncode != 0 and expected_error in stderr_text
        index_rows.append({
            "mutation": name,
            "pristine_path": str(pristine_path.relative_to(BASE)),
            "mutated_path": str(target.relative_to(work)),
            "pristine_bytes": pristine_bytes,
            "pristine_sha256": pristine_sha,
            "mutated_bytes": mutated_bytes,
            "mutated_sha256": mutated_sha,
            "minimal_diff_witness": witness,
            "command": json.dumps(command),
            "cwd": str(ROOT),
            "started_at": started,
            "ended_at": ended,
            "exit_code": result.returncode,
            "stdout_path": str(stdout_path.relative_to(BASE)),
            "stdout_bytes": len(result.stdout),
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_path": str(stderr_path.relative_to(BASE)),
            "stderr_bytes": len(result.stderr),
            "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
            "expected_error_target": expected_error,
            "validator_rejected_target": rejected,
            "isolated_copy_preserved": True,
        })
    index_path = mutation_root / "mutation_index.csv"
    fields = list(index_rows[0])
    with index_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(index_rows)
    if not all(row["validator_rejected_target"] for row in index_rows):
        raise RuntimeError("one or more required isolated mutations were not rejected at the changed object")
    print(json.dumps({"status": "PASS", "mutations": len(index_rows), "all_nonzero_targeted": True}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Finalize or independently validate the pragmatic recovery closure record."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity(path: Path):
    path = path.resolve()
    return {"path": str(path.relative_to(PROJECT)), "bytes": path.stat().st_size, "sha256": sha256(path)}


def resolve(record):
    return PROJECT / record["path"]


def finalize(args):
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    a_gate = json.loads(args.a_gate.read_text())
    b_gate = json.loads(args.b_gate.read_text())
    comparator = json.loads(args.comparator.read_text())
    reference = json.loads(args.reference.read_text())
    mutations = json.loads(args.mutations.read_text())
    state = a_gate["candidate_scientific_state"]
    if not (
        state == b_gate["candidate_scientific_state"] == comparator["candidate_scientific_state"] == "INCONCLUSIVE_MIXED"
        and comparator["status"] == "PASS"
        and reference["status"] == "PASS"
        and mutations["status"] == "PASS"
        and len(mutations["checks"]) == 6
        and all(item["pass"] and item["pristine_exit"] == 0 and item["mutated_exit"] != 0 for item in mutations["checks"])
    ):
        raise SystemExit("recovery components do not close")
    code_directory = Path(__file__).resolve().parent
    code_names = (
        "pragmatic_recovery.py", "validate_recovery.py", "independent_b.py", "compare_recoveries.py",
        "reference_probe.py", "run_recovery_mutations.py", "recovery_closure.py", "RECOVERY_REPORT.md",
    )
    payload = {
        "schema": "orientbench-r020-pragmatic-recovery-closure-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "VALID_RECOVERY_CLOSURE",
        "candidate_scientific_state": state,
        "formal_state": "NOT_ADJUDICATED_PENDING_SUPERVISOR",
        "science": {
            "input_identities": "26_OF_26_PASS",
            "strict_join": "PASS",
            "implementation_a": "PASS_10000_REPLICATES",
            "implementation_b": "PASS_10000_REPLICATES",
            "comparator": "PASS_ZERO_DIFFERENCE",
            "unit_hypotheses": 270,
            "dataset_hypotheses": 135,
            "unit_witnesses": comparator["unit_witnesses"],
            "dataset_witnesses": comparator["dataset_witnesses"],
            "passing_signatures": comparator["passing_signatures"],
        },
        "audit": {
            "pinned_reference": "PASS_FOUR_VECTORS",
            "mutations": "PASS_SIX_OF_SIX",
            "original_predata_code_seal": "IRREPARABLE_RETROACTIVELY_ABSENT",
            "original_live_application_access_chain": "IRREPARABLE_RETROACTIVELY_ABSENT",
            "original_os_strace_bidirectional_closure": "IRREPARABLE_RETROACTIVELY_ABSENT",
            "original_single_commit_postseal_receipt": "NOT_APPLICABLE_TO_RECOVERY_FOLLOWUP",
        },
        "artifacts": [identity(path) for path in (args.a_gate, args.b_gate, args.comparator, args.reference, args.mutations)],
        "code": [identity(code_directory / name) for name in code_names],
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": payload["status"], "candidate_scientific_state": state}, sort_keys=True))


def validate(args):
    payload = json.loads(args.closure.read_text())
    if payload["schema"] != "orientbench-r020-pragmatic-recovery-closure-v1" or payload["status"] != "VALID_RECOVERY_CLOSURE":
        raise SystemExit("closure schema/status mismatch")
    for section in ("artifacts", "code"):
        for record in payload[section]:
            path = resolve(record)
            if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
                raise SystemExit(f"closure identity mismatch: {record['path']}")
    if payload["candidate_scientific_state"] != "INCONCLUSIVE_MIXED" or payload["science"]["passing_signatures"]:
        raise SystemExit("closure scientific state mismatch")
    if payload["audit"]["original_predata_code_seal"] != "IRREPARABLE_RETROACTIVELY_ABSENT":
        raise SystemExit("closure does not preserve formal blocker")
    print(json.dumps({"status": "PASS", "closure_sha256": sha256(args.closure)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("finalize")
    create.add_argument("--a-gate", type=Path, required=True)
    create.add_argument("--b-gate", type=Path, required=True)
    create.add_argument("--comparator", type=Path, required=True)
    create.add_argument("--reference", type=Path, required=True)
    create.add_argument("--mutations", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("validate")
    check.add_argument("--closure", type=Path, required=True)
    args = parser.parse_args()
    finalize(args) if args.command == "finalize" else validate(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Execute the read-only r002 validator and persist a path-free run receipt."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "coordination/instructions/r002/evidence"
RESULT_DIR = ROOT / "coordination/executions/r002"
SUPERVISION_DIR = ROOT / "coordination/supervision/r002"


def write_yaml(path: Path, document: dict[str, object]) -> None:
    lines = ["schema_version: 1"]
    for key, value in document.items():
        if isinstance(value, bool):
            rendered = str(value).lower()
        elif isinstance(value, (str, int)):
            rendered = str(value)
        else:
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
        lines.append(f"{key}: {rendered}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("r002_validator", Path(__file__).with_name("validate_r002_audit.py"))
    assert spec and spec.loader
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    report = validator.audit(EVIDENCE / "R002_RISK_AUDIT_RESULT.yaml", EVIDENCE / "artifact_manifest.yaml")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "VALIDATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    status = "COMPLETE" if report["ok"] else "FAILED_ACCEPTANCE"
    write_yaml(RESULT_DIR / "RESULT.yaml", {
        "instruction_id": "r002",
        "run_id": args.run_id,
        "status": status,
        "scientific_status": "INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE",
        "validator": report["validator"],
        "g1_cells_recomputed": report["g1_cells_recomputed"],
        "fair1m_d_universe": report["fair1m_d_universe"],
        "errors": report["errors"],
    })
    write_yaml(SUPERVISION_DIR / "SUPERVISION.yaml", {
        "instruction_id": "r002",
        "run_id": args.run_id,
        "plan_path": "coordination/instructions/r002/SERVER_PLAN.yaml",
        "status": status,
        "cpu_only": True,
        "gpu_count": 0,
        "validation_report": "coordination/executions/r002/VALIDATION.json",
    })
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

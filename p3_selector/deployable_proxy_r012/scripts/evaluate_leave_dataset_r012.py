#!/usr/bin/env python3
"""Guarded r012 source-only fit and target-audit evaluation entry point."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
A0 = ROOT / "outputs/persistent_artifacts/orientbench_r012/a0_preflight.json"


def main() -> int:
    status = json.loads(A0.read_text())["status"]
    if status != "PASS_A0_R012":
        print(f"NOT_RUN_PROVENANCE_GATE: {status}")
        return 2
    raise RuntimeError("A0 passed but the frozen evaluator implementation is unavailable")


if __name__ == "__main__":
    raise SystemExit(main())

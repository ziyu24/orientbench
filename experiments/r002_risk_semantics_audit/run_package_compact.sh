#!/usr/bin/env bash
set -euo pipefail
exec "${PYTHON:?}" "${ORIENTBENCH_ROOT:?}/experiments/r002_risk_semantics_audit/package_compact_scores.py"

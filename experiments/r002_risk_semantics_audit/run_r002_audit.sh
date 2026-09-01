#!/usr/bin/env bash
set -euo pipefail
export ORIENTBENCH_ROOT="${ORIENTBENCH_ROOT:?}"
export R002_RUNTIME="${R002_RUNTIME:?}"
export R002_CORRECTION_OUT="${R002_CORRECTION_OUT:?}"
export R002_DIOR_ANN="${R002_DIOR_ANN:?}"
export R002_FAIR_ANN="${R002_FAIR_ANN:?}"
export R002_SODA_ANN="${R002_SODA_ANN:?}"
exec "${PYTHON:?}" "$ORIENTBENCH_ROOT/experiments/r002_risk_semantics_audit/run_r002_audit.py"

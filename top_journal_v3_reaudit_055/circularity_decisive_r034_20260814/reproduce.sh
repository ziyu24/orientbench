#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
ENV_PY=/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python
CODE=top_journal_v3_reaudit_055/circularity_decisive_r034_20260814
OUT=outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814
"$ENV_PY" "$CODE/prepare_inputs.py"
"$ENV_PY" "$CODE/implementation_a.py" --output "$OUT/implementation_a" --replicates 10000 --workers 96
"$ENV_PY" "$CODE/implementation_b.py" --output "$OUT/implementation_b" --replicates 10000 --workers 96
"$ENV_PY" "$CODE/compare_ab.py" --a "$OUT/implementation_a" --b "$OUT/implementation_b" --output "$OUT/comparator"
"$ENV_PY" "$CODE/validate_r034.py" --root "$OUT" --output "$CODE/validation/validation.json" --workers 96
"$ENV_PY" "$CODE/run_mutations.py"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BROOT="$ROOT/top_journal_v3_reaudit_055/paper_B_psc_mechanism"
PY="/home/rspip/anaconda3/envs/mr_dev1x/bin/python"
LOG="$BROOT/logs/reproduce_B1_B3_078.log"

mkdir -p "$BROOT/logs"
exec > >(tee "$LOG") 2>&1

cd "$ROOT"
test -s "$BROOT/docs/b1_mechanism_preregistration.md"
test -s "$BROOT/reports/b1_protocol_frozen.json"
test -s "$BROOT/reports/b1_candidate_score_registry.csv"
test -s "$BROOT/reports/b1_hypothesis_registry.csv"

python "$BROOT/scripts/run_b2_toy_model.py"
for seed in 0 1 2; do
  CUDA_VISIBLE_DEVICES="$seed" "$PY" "$BROOT/scripts/dump_b3_fair1m_phase_vectors.py" --seed "$seed"
done
python "$BROOT/scripts/run_b3_real_interventions.py"
python "$BROOT/scripts/verify_b1_b3.py"

echo "B1_B3_REPRODUCTION_COMPLETE"

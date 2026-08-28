#!/usr/bin/env bash
set -euo pipefail

root=/home/rspip/cqc/pro/study/orientbench
base="$root/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1"
log="$base/g1_proposal_supervisor.log"
mkdir -p "$base"
exec >>"$log" 2>&1
while tmux has-session -t orientbench_r052_g1_train_proposals 2>/dev/null; do sleep 30; done
test -s "$base/train_proposal_export/predictions.pkl"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root"
python "$root/experiments/r052_cmr_admission/select_1024_train_proposals.py" \
  --predictions "$base/train_proposal_export/predictions.pkl" \
  --out "$base/frozen_1024_positive_proposals.json"

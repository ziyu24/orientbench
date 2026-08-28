#!/usr/bin/env bash
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
base="$root/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1"
mkdir -p "$base/formal_native_path_admission"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root"
python "$root/experiments/r052_cmr_admission/run_g1_native_path_admission.py" \
  --manifest "$base/frozen_1024_positive_proposals.json" \
  --out "$base/formal_native_path_admission/result.json" \
  >"$base/formal_native_path_admission/run.log" 2>&1

#!/usr/bin/env bash
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
out="$root/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/dynamic_g1"
mkdir -p "$out"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root"
export CUDA_VISIBLE_DEVICES=0,1,2,3
torchrun --master_port 29860 --nproc_per_node=4 "$root/experiments/r052_cmr_admission/run_dynamic_g1.py" >"$out/run.log" 2>&1
python "$root/experiments/r052_cmr_admission/summarize_dynamic_g1.py" \
  --dynamic-dir "$out" \
  --mutation "$root/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/correction_pre_nms_export_6000_uid_v3_rpn_provenance/uid_mutation_validation.json" \
  --out "$out/summary.json" >"$out/summary.log" 2>&1

#!/usr/bin/env bash
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
out="$root/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/correction_four_gpu_inference_smoke"
mkdir -p "$out"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root"
export CUDA_VISIBLE_DEVICES=0,1,2,3
torchrun --master_port 29857 --nproc_per_node=4 \
  "$root/experiments/r052_cmr_admission/run_four_gpu_inference_smoke.py" >"$out/run.log" 2>&1

#!/usr/bin/env bash
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
out="$root/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/correction_pre_nms_export"
mkdir -p "$out"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root"
export CUDA_VISIBLE_DEVICES=0,1,2,3
export R052_MAX_IMAGES=512
torchrun --master_port 29858 --nproc_per_node=4 \
  "$root/experiments/r052_cmr_admission/export_pre_nms_train_shard.py" >"$out/export.log" 2>&1
python "$root/experiments/r052_cmr_admission/select_1024_pre_nms_proposals.py" \
  --shard-dir "$out" --out "$out/frozen_1024_pre_nms_positive_proposals.json" \
  >"$out/select.log" 2>&1

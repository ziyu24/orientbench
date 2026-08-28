#!/usr/bin/env bash
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
out="$root/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/correction_cmr_joint_smoke_5"
mkdir -p "$out"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root"
export CUDA_VISIBLE_DEVICES=0,1,2,3
torchrun --master_port 29856 --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/train.py \
  "$root/configs/r052_cmr_admission/dota_orcnn_joint_cmr_smoke_correction.py" \
  --launcher pytorch --work-dir "$out" >"$out/train.log" 2>&1

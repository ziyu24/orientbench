#!/usr/bin/env bash
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
out="$root/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_cmr_smoke_20"
mkdir -p "$out"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
torchrun --master_port 29831 --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/train.py \
  "$root/configs/r051_cmr_obb/dota_orcnn_cmr_smoke_20.py" --launcher pytorch \
  >"$out/train.log" 2>&1

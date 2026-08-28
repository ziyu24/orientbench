#!/usr/bin/env bash
set -euo pipefail

root=/home/rspip/cqc/pro/study/orientbench
out="$root/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/train_proposal_export"
mkdir -p "$out"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root"
export CUDA_VISIBLE_DEVICES=0,1,2,3
torchrun --master_port 29853 --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/test.py \
  "$root/configs/r052_cmr_admission/dota_orcnn_train_proposals.py" \
  /home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth \
  --launcher pytorch --work-dir "$out" --out "$out/predictions.pkl" >"$out/test.log" 2>&1

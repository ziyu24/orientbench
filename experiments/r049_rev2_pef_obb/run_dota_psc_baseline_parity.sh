#!/usr/bin/env bash
set -euo pipefail
cd /home/rspip/cqc/pro/study/orientbench
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="${PWD}${PYTHONPATH:+:${PYTHONPATH}}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
exec torchrun --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/test.py \
  configs/r049_rev2_pef_obb/dota_psc_baseline_parity.py \
  /home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_5562_epoch_12.pth \
  --launcher pytorch \
  --work-dir outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g0/dota_psc_baseline_parity

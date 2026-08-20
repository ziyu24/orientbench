#!/usr/bin/env bash
set -euo pipefail
cd /home/rspip/cqc/pro/study/orientbench
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="${PWD}${PYTHONPATH:+:${PYTHONPATH}}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
exec torchrun --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/train.py \
  configs/r049_rev2_pef_obb/dota_psc_pef_smoke_500.py --launcher pytorch

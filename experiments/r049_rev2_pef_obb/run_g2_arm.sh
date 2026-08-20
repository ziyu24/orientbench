#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo 'usage: run_g2_arm.sh <config>' >&2
  exit 2
fi
cd /home/rspip/cqc/pro/study/orientbench
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="${PWD}${PYTHONPATH:+:${PYTHONPATH}}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
exec torchrun --master_port "${MASTER_PORT:-29500}" --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/train.py \
  "$1" --launcher pytorch

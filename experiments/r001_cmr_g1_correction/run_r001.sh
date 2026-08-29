#!/usr/bin/env bash
set -euo pipefail
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH=/home/rspip/cqc/pro/study/orientbench
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export TMPDIR=/home/rspip/cqc/pro/study/orientbench/runs/r001/tmp
mkdir -p "$TMPDIR"
python experiments/r001_cmr_g1_correction/run_r001.py

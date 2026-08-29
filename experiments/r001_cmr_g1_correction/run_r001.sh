#!/usr/bin/env bash
set -euo pipefail
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH=/home/rspip/cqc/pro/study/orientbench
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export TMPDIR=/home/rspip/cqc/pro/study/orientbench/runs/r001/tmp
mkdir -p "$TMPDIR"
export NUMBA_DISABLE_JIT=1
export NUMBA_CACHE_DIR="$TMPDIR/numba"
export CUDA_CACHE_PATH="$TMPDIR/cuda"
export XDG_CACHE_HOME="$TMPDIR/xdg-cache"
export JOBLIB_TEMP_FOLDER="$TMPDIR/joblib"
mkdir -p "$NUMBA_CACHE_DIR" "$CUDA_CACHE_PATH" "$XDG_CACHE_HOME" "$JOBLIB_TEMP_FOLDER"
python experiments/r001_cmr_g1_correction/run_r001.py

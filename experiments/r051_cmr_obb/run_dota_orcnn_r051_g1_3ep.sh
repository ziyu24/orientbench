#!/usr/bin/env bash
# Run exactly one frozen r051 G1 arm on all four GPUs.  The caller supplies a
# project-local config basename (cmr, direct_dist, or single_roi_quality).
set -euo pipefail

case "${1:-}" in
  cmr) config=dota_orcnn_cmr_frozenhost_3ep.py; arm=cmr ;;
  direct_dist) config=dota_orcnn_direct_dist_frozenhost_3ep.py; arm=direct_dist ;;
  single_roi_quality) config=dota_orcnn_single_roi_quality_frozenhost_3ep.py; arm=single_roi_quality ;;
  *) echo 'usage: run_dota_orcnn_r051_g1_3ep.sh {cmr|direct_dist|single_roi_quality}' >&2; exit 64 ;;
esac

root=/home/rspip/cqc/pro/study/orientbench
out="$root/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_${arm}_frozenhost_3ep"
mkdir -p "$out"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
torchrun --master_port 29833 --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/train.py \
  "$root/configs/r051_cmr_obb/$config" --launcher pytorch \
  >"$out/train.log" 2>&1

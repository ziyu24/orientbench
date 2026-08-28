#!/usr/bin/env bash
# Persist raw val predictions for one completed frozen r051 G1 arm.
set -euo pipefail

case "${1:-}" in
  cmr) config=dota_orcnn_cmr_frozenhost_3ep.py; arm=cmr ;;
  direct_dist) config=dota_orcnn_direct_dist_frozenhost_3ep.py; arm=direct_dist ;;
  single_roi_quality) config=dota_orcnn_single_roi_quality_frozenhost_3ep.py; arm=single_roi_quality ;;
  *) echo 'usage: run_dota_orcnn_r051_g1_export.sh {cmr|direct_dist|single_roi_quality}' >&2; exit 64 ;;
esac

root=/home/rspip/cqc/pro/study/orientbench
run_dir="$root/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_${arm}_frozenhost_3ep"
checkpoint="$run_dir/epoch_3.pth"
out="$run_dir/evaluation"
mkdir -p "$out"
test -s "$checkpoint"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
torchrun --master_port 29834 --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/test.py \
  "$root/configs/r051_cmr_obb/$config" "$checkpoint" --launcher pytorch \
  --work-dir "$out" --out "$out/predictions.pkl" >"$out/test.log" 2>&1

if [ "$arm" = cmr ]; then
  python "$root/experiments/r051_cmr_obb/validate_cmr_provenance.py" \
    --predictions "$out/predictions.pkl" --out "$out/provenance_validation.txt" \
    >"$out/provenance_validation.log" 2>&1
fi

#!/usr/bin/env bash
# Export the exact final CMR detections after the G1 smoke.  This is kept
# separate from training so the persisted prediction pickle can be passed to
# the independent provenance mutation validator without rerunning training.
set -euo pipefail

root=/home/rspip/cqc/pro/study/orientbench
run_dir="$root/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_cmr_smoke_20"
checkpoint="$run_dir/epoch_1.pth"
out="$run_dir/evaluation"
mkdir -p "$out"
test -s "$checkpoint"

source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
torchrun --master_port 29832 --nproc_per_node=4 \
  /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/test.py \
  "$root/configs/r051_cmr_obb/dota_orcnn_cmr_smoke_20.py" "$checkpoint" \
  --launcher pytorch --work-dir "$out" --out "$out/predictions.pkl" \
  >"$out/test.log" 2>&1

python "$root/experiments/r051_cmr_obb/validate_cmr_provenance.py" \
  --predictions "$out/predictions.pkl" --out "$out/provenance_validation.txt" \
  >"$out/provenance_validation.log" 2>&1

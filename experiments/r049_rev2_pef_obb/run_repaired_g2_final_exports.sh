#!/usr/bin/env bash
# Final epoch-12 export only; no best-checkpoint selection or metric tuning.
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
base="${1:-$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_repaired_percandidate}"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root${PYTHONPATH:+:${PYTHONPATH}}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
declare -A configs=(
  [dota_psc_cont]=configs/r049_rev2_pef_obb/dota_psc_cont_rotated_grid_full.py
  [dota_psc_direct_dist_residual]=configs/r049_rev2_pef_obb/dota_psc_direct_dist_residual_full.py
  [dota_psc_scalar_quality]=configs/r049_rev2_pef_obb/dota_psc_scalar_quality_rotated_grid_full.py
  [dota_psc_pef]=configs/r049_rev2_pef_obb/dota_psc_pef_rotated_grid_full.py
)
for arm in dota_psc_cont dota_psc_direct_dist_residual dota_psc_scalar_quality dota_psc_pef; do
  out="$base/evaluation/$arm"; mkdir -p "$out"
  # The cleanup retains an explicitly epoch-12 best checkpoint when it is
  # byte-for-byte the final-epoch model but removes duplicate resume state.
  # Never select an earlier best checkpoint for the frozen final-epoch export.
  checkpoint="$base/$arm/epoch_12.pth"
  if [ ! -f "$checkpoint" ]; then
    checkpoint="$base/$arm/best_dota_mAP_epoch_12.pth"
  fi
  test -f "$checkpoint"
  torchrun --master_port $((29900 + ${#arm})) --nproc_per_node=4 \
    /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/test.py \
    "${configs[$arm]}" "$checkpoint" --launcher pytorch --work-dir "$out" --out "$out/predictions.pkl" \
    --cfg-options val_evaluator.iou_thrs='[0.5,0.75]' test_evaluator.iou_thrs='[0.5,0.75]' \
    >"$out/test.log" 2>&1
done
mkdir -p "$base/metrics"
CUDA_VISIBLE_DEVICES='' python "$root/experiments/r049_rev2_pef_obb/build_repaired_g2_metrics.py" --base "$base" --out "$base/metrics" \
  >"$base/metrics/build_metrics.log" 2>&1
CUDA_VISIBLE_DEVICES='' python "$root/experiments/r049_rev2_pef_obb/adjudicate_repaired_g2.py" --base "$base" \
  >"$base/metrics/adjudicate.log" 2>&1

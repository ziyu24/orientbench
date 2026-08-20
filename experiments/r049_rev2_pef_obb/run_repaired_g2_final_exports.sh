#!/usr/bin/env bash
# Final epoch-12 export only; no best-checkpoint selection or metric tuning.
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
base="${1:-$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_repaired_percandidate}"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root${PYTHONPATH:+:${PYTHONPATH}}"
export CUDA_VISIBLE_DEVICES=0,1,2,3
declare -A configs=(
  [dota_psc_cont]=configs/r049_rev2_pef_obb/dota_psc_cont_repaired_full.py
  [dota_psc_direct_dist]=configs/r049_rev2_pef_obb/dota_psc_direct_dist_repaired_full.py
  [dota_psc_scalar_quality]=configs/r049_rev2_pef_obb/dota_psc_scalar_quality_repaired_full.py
  [dota_psc_pef]=configs/r049_rev2_pef_obb/dota_psc_pef_repaired_full.py
)
for arm in dota_psc_cont dota_psc_direct_dist dota_psc_scalar_quality dota_psc_pef; do
  out="$base/evaluation/$arm"; mkdir -p "$out"
  torchrun --master_port $((29900 + ${#arm})) --nproc_per_node=4 \
    /home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/test.py \
    "${configs[$arm]}" "$base/$arm/epoch_12.pth" --launcher pytorch --work-dir "$out" --out "$out/predictions.pkl" \
    --cfg-options val_evaluator.iou_thrs='[0.5,0.75]' test_evaluator.iou_thrs='[0.5,0.75]' \
    >"$out/test.log" 2>&1
done
CUDA_VISIBLE_DEVICES='' python "$root/experiments/r049_rev2_pef_obb/build_repaired_g2_metrics.py" --base "$base" --out "$base/metrics" \
  >"$base/metrics/build_metrics.log" 2>&1
CUDA_VISIBLE_DEVICES='' python "$root/experiments/r049_rev2_pef_obb/adjudicate_repaired_g2.py" --base "$base" \
  >"$base/metrics/adjudicate.log" 2>&1

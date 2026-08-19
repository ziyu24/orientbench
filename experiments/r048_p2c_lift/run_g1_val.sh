#!/usr/bin/env bash
# Val-only metric and frozen-jitter evaluation.  No T_cal/test/audit source is read.
set -euo pipefail
root="outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819"
formal="$root/formal_revised"
out="$root/g1_val_revised"
mkdir -p "$out"
eval_one() {
  local tag="$1" kind="$2" checkpoint="$3" jitter="${4:-0}"
  local hid="${5:-384}" layers="${6:-3}"
  CUDA_VISIBLE_DEVICES=3 python experiments/r048_p2c_lift/evaluate_g1_val.py --kind "$kind" --checkpoint "$checkpoint" --jitter "$jitter" --hid "$hid" --layers "$layers" --out "$out/${tag}.json" >"$out/${tag}.log" 2>&1
}
eval_one p2c_small P2C_LIFT "$formal/p2c_small/best.pt" 0 256 2
eval_one p2c_base P2C_LIFT "$formal/p2c_base/best.pt" 0 384 3
eval_one p2c_wide P2C_LIFT "$formal/p2c_wide/best.pt" 0 512 3
eval_one whole_crop_binary WHOLE_CROP_BINARY "$formal/whole_crop_binary/best.pt"
eval_one concat_endpoint_binary CONCAT_ENDPOINT_BINARY "$formal/concat_endpoint_binary/best.pt"
eval_one headpoint_2d HEADPOINT_2D "$formal/headpoint_2d/best.pt"
eval_one direct_s1_vm DIRECT_S1_VM "$formal/direct_s1_vm/best.pt"
for j in 5 10 15; do
  eval_one "p2c_small_jitter_${j}" P2C_LIFT "$formal/p2c_small/best.pt" "$j" 256 2
  eval_one "whole_crop_binary_jitter_${j}" WHOLE_CROP_BINARY "$formal/whole_crop_binary/best.pt" "$j"
done

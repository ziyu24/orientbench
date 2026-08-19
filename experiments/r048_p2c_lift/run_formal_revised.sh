#!/usr/bin/env bash
# Frozen r048 capacity menu and fair-baseline schedule.  Each invocation uses
# all four GPUs and emits only a per-run log under the persistent artifact root.
set -euo pipefail
root="outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/formal_revised"
run() {
  local name="$1"; shift
  mkdir -p "$root/$name"
  torchrun --standalone --nproc_per_node=4 experiments/r048_p2c_lift/train_v2.py "$@" --epochs 30 --out "$root/$name" >"$root/$name/train.log" 2>&1
}
run p2c_base --kind P2C_LIFT --hid 384 --layers 3 --w-vector 0.25 --w-equiv 0.5
run p2c_wide --kind P2C_LIFT --hid 512 --layers 3 --w-vector 0.5 --w-equiv 0.5
run whole_crop_binary --kind WHOLE_CROP_BINARY --hid 384 --layers 3
run concat_endpoint_binary --kind CONCAT_ENDPOINT_BINARY --hid 384 --layers 3
run headpoint_2d --kind HEADPOINT_2D --hid 384 --layers 3
run direct_s1_vm --kind DIRECT_S1_VM --hid 384 --layers 3

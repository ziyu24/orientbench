#!/usr/bin/env bash
# Same r048 dispatch, fresh output namespace; no delete/overwrite of prior runs.
set -euo pipefail
root="outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/formal_sheetfixed"
run() {
  local name="$1"; shift
  mkdir -p "$root/$name"
  torchrun --standalone --nproc_per_node=4 experiments/r048_p2c_lift/train_v2.py "$@" --epochs 30 --out "$root/$name" >"$root/$name/train.log" 2>&1
}
# Run fair augmented baselines first so the frozen first-epoch P2C stop is
# evaluated against a real same-contract reference.
run whole_crop_binary --kind WHOLE_CROP_BINARY --hid 384 --layers 3
run concat_endpoint_binary --kind CONCAT_ENDPOINT_BINARY --hid 384 --layers 3
run headpoint_2d --kind HEADPOINT_2D --hid 384 --layers 3
run direct_s1_vm --kind DIRECT_S1_VM --hid 384 --layers 3
ref=$(python - <<'PY'
import glob,json
print(max(json.load(open(p))['best_accuracy'] for p in glob.glob('outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/formal_sheetfixed/*/summary.json')))
PY
)
run p2c_small --kind P2C_LIFT --hid 256 --layers 2 --w-vector 0.25 --w-equiv 0.25 --early-stop-baseline "$ref"
run p2c_base --kind P2C_LIFT --hid 384 --layers 3 --w-vector 0.25 --w-equiv 0.5 --early-stop-baseline "$ref"
run p2c_wide --kind P2C_LIFT --hid 512 --layers 3 --w-vector 0.5 --w-equiv 0.5 --early-stop-baseline "$ref"

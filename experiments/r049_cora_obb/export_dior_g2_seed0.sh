#!/usr/bin/env bash
# Export the three frozen DIOR G2 arms after successful training.  Each model
# is evaluated on the same r043 test endpoint, four ranks, and writes only its
# project-persistent raw prediction pickle plus a compact command log.
set -euo pipefail

ROOT=/home/rspip/cqc/pro/study/orientbench
THIRD_PARTY=/home/rspip/cqc/pro/study/third_party
OUT="$ROOT/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2"
RUNTIME="$ROOT/experiments/r049_cora_obb/runtime_compat"
export PYTHONNOUSERSITE=1
export PYTHONPATH="$ROOT:$RUNTIME"
mkdir -p "$OUT/raw_predictions" "$OUT/export_logs"

run_export() {
  local arm="$1"
  local cfg="$2"
  local run_dir="$OUT/$arm"
  local ckpt
  ckpt="$(find "$run_dir" -maxdepth 2 -type f -name 'best_dota_mAP_epoch_*.pth' | sort | tail -n 1)"
  test -n "$ckpt"
  conda run --no-capture-output -n pcp-obb torchrun --standalone --nproc_per_node=4 \
    "$THIRD_PARTY/mmrotate_1x/tools/test.py" "$cfg" "$ckpt" --launcher pytorch \
    > "$OUT/export_logs/${arm}.log" 2>&1
}

run_export dior_cont_seed0_fp32 "$ROOT/configs/r049_cora_obb/dior_cont_seed0_export.py"
run_export dior_vm_nll_seed0_fp32 "$ROOT/configs/r049_cora_obb/dior_vm_nll_seed0_export.py"
run_export dior_cora_seed0_fp32 "$ROOT/configs/r049_cora_obb/dior_cora_seed0_export.py"

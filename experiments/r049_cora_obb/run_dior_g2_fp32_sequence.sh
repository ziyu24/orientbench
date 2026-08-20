#!/usr/bin/env bash
# Frozen r049 DIOR seed0 executor: CONT is already running when this starts.
# It starts VM-NLL and CORA only after the predecessor exits cleanly, and stops
# the sequence on an explicit non-finite loss/gradient record.
set -euo pipefail

ROOT=/home/rspip/cqc/pro/study/orientbench
OUT_ROOT="$ROOT/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2"
RUNTIME="$ROOT/experiments/r049_cora_obb/runtime_compat"
export PYTHONNOUSERSITE=1
export PYTHONPATH="$ROOT:$RUNTIME"

while tmux has-session -t orientbench-r049-dior-cont-s0-fp32 2>/dev/null; do
  sleep 30
done

run_arm() {
  local name="$1"
  local config="$2"
  local out="$OUT_ROOT/$name"
  mkdir -p "$out"
  conda run --no-capture-output -n pcp-obb torchrun --standalone --nproc_per_node=4 \
    /home/rspip/cqc/pro/study/third_party/mmrotate_1x/tools/train.py "$config" \
    --launcher pytorch --work-dir "$out" > "$out/train.log" 2>&1
  if grep -En 'grad_norm: (nan|inf)|loss: (nan|inf)|loss_bbox: (nan|inf)' "$out/train.log"; then
    exit 41
  fi
}

run_arm dior_vm_nll_seed0_fp32 "$ROOT/configs/r049_cora_obb/dior_vm_nll_seed0_3e.py"
run_arm dior_cora_seed0_fp32 "$ROOT/configs/r049_cora_obb/dior_cora_seed0_3e.py"

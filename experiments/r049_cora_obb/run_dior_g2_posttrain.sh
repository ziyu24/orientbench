#!/usr/bin/env bash
# Detached r049 supervisor: after the ordered training driver has *verified*
# all three finite three-epoch arms, export the three frozen prediction sets,
# build matched rows, and issue the deterministic DIOR gate.  It deliberately
# does not launch SODA or any new seed; that requires a DIOR PASS artifact.
set -euo pipefail

ROOT=/home/rspip/cqc/pro/study/orientbench
OUT="$ROOT/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2"
export PYTHONNOUSERSITE=1
export PYTHONPATH="$ROOT:$ROOT/experiments/r049_cora_obb/runtime_compat"

while tmux has-session -t orientbench-r049-dior-g2-driver 2>/dev/null; do
  sleep 30
done

for arm in dior_cont_seed0_fp32 dior_vm_nll_seed0_fp32 dior_cora_seed0_fp32; do
  log="$OUT/$arm/train.log"
  test -f "$log"
  rg -q 'Epoch\(val\) \[3\]\[2935/2935\].*dota/AP50:' "$log"
  if rg -q 'grad_norm: (nan|inf)|loss: (nan|inf)|loss_bbox: (nan|inf)|Traceback|CUDA out of memory' "$log"; then
    echo "posttrain supervisor refuses incomplete/nonfinite arm: $arm" >&2
    exit 41
  fi
  find "$OUT/$arm" -type f -name 'best_dota_mAP_epoch_*.pth' | grep -q .
done

"$ROOT/experiments/r049_cora_obb/export_dior_g2_seed0.sh"
conda run --no-capture-output -n pcp-obb python \
  "$ROOT/experiments/r049_cora_obb/build_dior_g2_metrics.py"
conda run --no-capture-output -n pcp-obb python \
  "$ROOT/experiments/r049_cora_obb/adjudicate_dior_g2_seed0.py"

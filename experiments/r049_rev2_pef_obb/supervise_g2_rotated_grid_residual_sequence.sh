#!/usr/bin/env bash
# Continue the final G2 only after the repaired residual direct-distribution arm.
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
session=orientbench_r049rev2_grid
base="$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid"

wait_normal() {
  local d="$1" log="$1/train.log" pattern="mmrotate/.mim/tools/train.py.*${1##*/}"
  local seen=0
  for _ in $(seq 1 24); do
    if pgrep -f "$pattern" >/dev/null; then seen=1; break; fi
    if grep -q 'Saving checkpoint at 12 epochs' "$log" 2>/dev/null; then break; fi
    sleep 5
  done
  if [ "$seen" -eq 1 ]; then while pgrep -f "$pattern" >/dev/null; do sleep 30; done; fi
  grep -q 'Saving checkpoint at 12 epochs' "$log" && ! grep -qiE 'Traceback|ChildFailedError|RuntimeError|OutOfMemory' "$log"
}

run_arm() {
  mkdir -p "$2"
  tmux send-keys -t "$session" "MASTER_PORT=29821 bash $root/experiments/r049_rev2_pef_obb/run_g2_arm.sh $1 > $2/train.log 2>&1" Enter
}

if wait_normal "$base/dota_psc_direct_dist_residual"; then
  run_arm configs/r049_rev2_pef_obb/dota_psc_scalar_quality_rotated_grid_full.py "$base/dota_psc_scalar_quality"
else
  echo DIRECT_DIST_RESIDUAL_ABNORMAL; exit 1
fi
if wait_normal "$base/dota_psc_scalar_quality"; then
  run_arm configs/r049_rev2_pef_obb/dota_psc_pef_rotated_grid_full.py "$base/dota_psc_pef"
else
  echo SCALAR_QUALITY_ABNORMAL; exit 1
fi
if wait_normal "$base/dota_psc_pef"; then
  tmux send-keys -t "$session" "bash $root/experiments/r049_rev2_pef_obb/run_repaired_g2_final_exports.sh $base > $base/final_exports.log 2>&1" Enter
  echo PEF_NORMAL_FINAL_EXPORTS_STARTED
else
  echo PEF_ABNORMAL; exit 1
fi

#!/usr/bin/env bash
# Wait for the already-launched r49 PEF full arm, then perform only frozen export.
set -euo pipefail

root=/home/rspip/cqc/pro/study/orientbench
base="$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid"
log="$base/dota_psc_pef/train.log"
pattern='mmrotate/.mim/tools/train.py.*dota_psc_pef_rotated_grid_full.py'

while pgrep -f "$pattern" >/dev/null; do sleep 60; done

grep -q 'Saving checkpoint at 12 epochs' "$log"
! grep -qiE 'Traceback|ChildFailedError|RuntimeError|OutOfMemory|NCCL.*error' "$log"
bash "$root/experiments/r049_rev2_pef_obb/run_repaired_g2_final_exports.sh" "$base" \
  >"$base/final_exports.log" 2>&1

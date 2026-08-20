#!/usr/bin/env bash
# Sequential four-GPU G2 rerun after the repaired per-candidate G1 admission.
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
session=orientbench_r049rev2_repaired
base="$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_repaired_percandidate"

wait_for_normal_arm() {
  local run_dir="$1" log="$1/train.log" pattern="mmrotate/.mim/tools/train.py.*${1##*/}"
  local seen=0
  for _ in $(seq 1 24); do
    if pgrep -f "$pattern" >/dev/null; then seen=1; break; fi
    if grep -q 'Saving checkpoint at 12 epochs' "$log" 2>/dev/null; then break; fi
    sleep 5
  done
  if [ "$seen" -eq 1 ]; then while pgrep -f "$pattern" >/dev/null; do sleep 30; done; fi
  grep -q 'Saving checkpoint at 12 epochs' "$log" && ! grep -qiE 'Traceback|ChildFailedError|RuntimeError|OutOfMemory' "$log"
}
run_next() {
  local config="$1" run_dir="$2"
  mkdir -p "$run_dir"
  tmux send-keys -t "$session" "MASTER_PORT=29801 bash $root/experiments/r049_rev2_pef_obb/run_g2_arm.sh $config > $run_dir/train.log 2>&1" Enter
}

if wait_for_normal_arm "$base/dota_psc_cont"; then
  run_next configs/r049_rev2_pef_obb/dota_psc_direct_dist_repaired_full.py "$base/dota_psc_direct_dist"
else echo CONT_ABNORMAL; exit 1; fi
if wait_for_normal_arm "$base/dota_psc_direct_dist"; then
  run_next configs/r049_rev2_pef_obb/dota_psc_scalar_quality_repaired_full.py "$base/dota_psc_scalar_quality"
else echo DIRECT_DIST_ABNORMAL; exit 1; fi
if wait_for_normal_arm "$base/dota_psc_scalar_quality"; then
  run_next configs/r049_rev2_pef_obb/dota_psc_pef_repaired_full.py "$base/dota_psc_pef"
else echo SCALAR_QUALITY_ABNORMAL; exit 1; fi
if wait_for_normal_arm "$base/dota_psc_pef"; then echo PEF_NORMAL_ALL_G2_ARMS_COMPLETE
else echo PEF_ABNORMAL; exit 1; fi

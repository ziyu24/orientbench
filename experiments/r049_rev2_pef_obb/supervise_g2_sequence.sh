#!/usr/bin/env bash
# Continue the frozen G2 arms only after the preceding four-GPU job records a
# normal 12-epoch terminal checkpoint.  Any abnormal termination is recorded
# and leaves the next arm unstarted for a targeted repair.
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
session=orientbench_r049rev2
base="$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2"

wait_for_normal_arm() {
  local run_dir="$1"
  local log="$run_dir/train.log"
  local pattern="mmrotate/.mim/tools/train.py.*${run_dir##*/}"
  # A tmux send-keys launch is asynchronous.  Do not interpret the short
  # interval before torchrun is visible as a failed training arm.
  local seen=0
  for _ in $(seq 1 18); do
    if pgrep -f "$pattern" >/dev/null; then seen=1; break; fi
    if grep -q 'Saving checkpoint at 12 epochs' "$log" 2>/dev/null; then break; fi
    sleep 5
  done
  if [ "$seen" -eq 1 ]; then
    while pgrep -f "$pattern" >/dev/null; do sleep 30; done
  fi
  grep -q 'Saving checkpoint at 12 epochs' "$log" && ! grep -qiE 'Traceback|ChildFailedError|RuntimeError' "$log"
}

run_next() {
  local config="$1" run_dir="$2"
  tmux send-keys -t "$session" "bash $root/experiments/r049_rev2_pef_obb/run_g2_arm.sh $config > $run_dir/train.log 2>&1" Enter
}

if wait_for_normal_arm "$base/dota_psc_cont"; then
  run_next configs/r049_rev2_pef_obb/dota_psc_direct_dist_full.py "$base/dota_psc_direct_dist"
else
  echo "CONT_ABNORMAL"; exit 1
fi
if wait_for_normal_arm "$base/dota_psc_direct_dist"; then
  run_next configs/r049_rev2_pef_obb/dota_psc_scalar_quality_full.py "$base/dota_psc_scalar_quality"
else
  echo "DIRECT_DIST_ABNORMAL"; exit 1
fi
if wait_for_normal_arm "$base/dota_psc_scalar_quality"; then
  run_next configs/r049_rev2_pef_obb/dota_psc_pef_full.py "$base/dota_psc_pef"
else
  echo "SCALAR_QUALITY_ABNORMAL"; exit 1
fi
if wait_for_normal_arm "$base/dota_psc_pef"; then
  tmux send-keys -t "$session" "bash $root/experiments/r049_rev2_pef_obb/run_g2_final_exports.sh > $base/final_exports.log 2>&1" Enter
  echo "PEF_NORMAL_FINAL_EXPORTS_STARTED"
else
  echo "PEF_ABNORMAL"; exit 1
fi

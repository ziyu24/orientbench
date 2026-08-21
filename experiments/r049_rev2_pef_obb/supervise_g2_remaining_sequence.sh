#!/usr/bin/env bash
# Resume r49 G2 after the disk-space interruption without changing the frozen arm order.
set -euo pipefail

root=/home/rspip/cqc/pro/study/orientbench
train_session=orientbench_r049rev2_grid
base="$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid"

wait_normal() {
  local name="$1"
  local log="$base/$name/train.log"
  local pattern="mmrotate/.mim/tools/train.py.*${name}"
  local seen=0
  for _ in $(seq 1 24); do
    if pgrep -f "$pattern" >/dev/null; then seen=1; break; fi
    if grep -q 'Saving checkpoint at 12 epochs' "$log" 2>/dev/null; then break; fi
    sleep 5
  done
  if [ "$seen" -eq 1 ]; then
    while pgrep -f "$pattern" >/dev/null; do sleep 30; done
  fi
  grep -q 'Saving checkpoint at 12 epochs' "$log" &&
    ! grep -qiE 'Traceback|ChildFailedError|RuntimeError|OutOfMemory' "$log"
}

run_arm() {
  local config="$1" name="$2"
  mkdir -p "$base/$name"
  tmux send-keys -t "$train_session" \
    "MASTER_PORT=29821 bash $root/experiments/r049_rev2_pef_obb/run_g2_arm.sh $config > $base/$name/train.log 2>&1" Enter
}

wait_scalar_admission() {
  local log="$base/dota_psc_scalar_quality/train.log"
  local pattern='mmrotate/.mim/tools/train.py.*dota_psc_scalar_quality_rotated_grid_full.py'
  while pgrep -f "$pattern" >/dev/null; do
    local line value
    line=$(grep 'Epoch(val) \[1\].*dota/mAP:' "$log" 2>/dev/null | tail -n 1 || true)
    if [ -n "$line" ]; then
      value=$(printf '%s\n' "$line" | sed -n 's/.*dota\/mAP: \([0-9.]*\).*/\1/p')
      if awk "BEGIN { exit !($value >= 0.005) }"; then
        return 0
      fi
      tmux send-keys -t "$train_session" C-c
      echo "SCALAR_QUALITY_EPOCH1_ADMISSION_FAILED mAP=$value"
      return 1
    fi
    sleep 20
  done
  return 1
}

if ! wait_scalar_admission; then
  exit 1
fi
if ! wait_normal dota_psc_scalar_quality; then
  echo "SCALAR_QUALITY_ABNORMAL"
  exit 1
fi
run_arm configs/r049_rev2_pef_obb/dota_psc_pef_rotated_grid_full.py dota_psc_pef
if ! wait_normal dota_psc_pef; then
  echo "PEF_ABNORMAL"
  exit 1
fi
tmux send-keys -t "$train_session" \
  "bash $root/experiments/r049_rev2_pef_obb/run_repaired_g2_final_exports.sh $base > $base/final_exports.log 2>&1" Enter
echo "PEF_NORMAL_FINAL_EXPORTS_STARTED"

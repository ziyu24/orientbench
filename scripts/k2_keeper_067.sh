#!/usr/bin/env bash
# k2_keeper_067.sh — keep exactly one k2_driver_067 alive until go/no-go decision exists.
# On driver death (before decision): kill orphaned K2 torchrun (project-only), relaunch driver (resumable).
PY=/home/rspip/anaconda3/envs/mr_dev1x/bin/python
ROOT=/home/rspip/cqc/pro/study/orientbench
DEC="$ROOT/top_journal_v3_reaudit_055/reports/k2_go_no_go_decision_067.csv"
LOGD="$ROOT/top_journal_v3_reaudit_055/logs/k2_angle_coder"
KLOG="$LOGD/k2_keeper_067.log"
cd "$ROOT"
while true; do
  if [ -f "$DEC" ]; then echo "[$(date '+%F %T')] go/no-go decision present -> keeper exit" >> "$KLOG"; break; fi
  if ! pgrep -f 'k2_driver_067.py' | grep -qv grep 2>/dev/null; then
    if ! ps -eo args | grep -q '[k]2_driver_067.py'; then
      echo "[$(date '+%F %T')] driver dead, decision absent -> cleaning orphan K2 runs + relaunching" >> "$KLOG"
      for pid in $(pgrep -f 'work_dirs/k2/' 2>/dev/null); do kill -9 "$pid" 2>/dev/null; done
      sleep 5
      setsid $PY scripts/k2_driver_067.py >> "$LOGD/k2_driver_067.out" 2>&1 < /dev/null &
      sleep 10
    fi
  fi
  sleep 300
done

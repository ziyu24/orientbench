#!/usr/bin/env bash
# run_k2_queue_2jobs_each_4gpu_067.sh — keeper: keep watch_k2_queue_2x4gpu_067.py alive until
# go/no-go decision exists. 2 concurrent jobs, each 4-GPU (handled inside the watcher/job_runner).
# On watcher death (before decision): clean orphaned K2 runs (project-only) + relaunch (resumable).
PY=/home/rspip/anaconda3/envs/mr_dev1x/bin/python
ROOT=/home/rspip/cqc/pro/study/orientbench
DEC="$ROOT/top_journal_v3_reaudit_055/reports/k2_go_no_go_decision_067.csv"
LOGD="$ROOT/top_journal_v3_reaudit_055/logs/k2_angle_coder"
KLOG="$LOGD/k2_keeper_067.log"
cd "$ROOT"
while true; do
  if [ -f "$DEC" ]; then echo "[$(date '+%F %T')] go/no-go present -> keeper exit" >> "$KLOG"; break; fi
  if ! ps -eo args | grep -q '[w]atch_k2_queue_2x4gpu_067.py'; then
    echo "[$(date '+%F %T')] watcher down, decision absent -> clean orphan K2 + relaunch" >> "$KLOG"
    for pid in $(pgrep -f 'work_dirs/k2/' 2>/dev/null); do kill -9 "$pid" 2>/dev/null; done
    sleep 5
    setsid $PY scripts/watch_k2_queue_2x4gpu_067.py >> "$LOGD/watch_k2_067.out" 2>&1 < /dev/null &
    sleep 15
  fi
  sleep 300
done

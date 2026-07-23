#!/usr/bin/env bash
# run_m069.sh — keeper for the command-069 orchestrator. Keeps m069_master.py alive (resumable) until
# both final sentinels exist: 068_submission_freeze_gate.csv AND psc_phase1_split_gate_decision.csv.
# On master death before completion, relaunch (master skips done sentinels). Never touches other projects.
ROOT=/home/rspip/cqc/pro/study/orientbench
PY=/home/rspip/anaconda3/envs/mr_dev1x/bin/python
REP=$ROOT/top_journal_v3_reaudit_055/reports
LOGD=$ROOT/top_journal_v3_reaudit_055/logs/m069
mkdir -p "$LOGD"
KLOG=$LOGD/keeper.log
FREEZE=$REP/068_submission_freeze_gate.csv
PHASE1=$REP/psc_phase1_split_gate_decision.csv
log(){ echo "[$(date '+%F %T')] $*" >> "$KLOG"; }
log "KEEPER START"
while true; do
  # done when both final sentinels present
  if [ -s "$FREEZE" ] && [ -s "$PHASE1" ]; then
    log "COMPLETE: freeze gate + phase1 decision present -> keeper exit"
    break
  fi
  if ! pgrep -f "scripts/m069_master.py" >/dev/null 2>&1; then
    log "launch m069_master.py"
    cd "$ROOT"
    nohup "$PY" scripts/m069_master.py >> "$LOGD/master_nohup.out" 2>&1 &
    sleep 10
  fi
  sleep 60
done
log "KEEPER END"

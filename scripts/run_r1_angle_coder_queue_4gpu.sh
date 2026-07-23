#!/usr/bin/env bash
# run_r1_angle_coder_queue_4gpu.sh — launch ONE R1 run on 4 GPUs (DDP world_size=4).
# Usage: bash scripts/run_r1_angle_coder_queue_4gpu.sh <config.py> <work_dir> <seed> <run_id> [master_port]
# 4-GPU mandatory (no 1/2-GPU fallback). Writes its own log. Returns train.py exit code.
set -uo pipefail
CFG="$1"; WD="$2"; SEED="$3"; RID="$4"; PORT="${5:-29510}"
ROOT=/home/rspip/cqc/pro/study/orientbench
PY=/home/rspip/anaconda3/envs/mr_dev1x/bin/python
# expose project-local ext modules (e.g. orientbench_ext.dcl_coder) to train.py
export PYTHONPATH="$ROOT/top_journal_v3_reaudit_055:${PYTHONPATH:-}"
TR=/home/rspip/cqc/pro/study/ai4rs_clone/tools/train.py
[ -f "$TR" ] || TR=/home/rspip/cqc/pro/study/third_party/mmrotate_1x/tools/train.py
LOG="$ROOT/top_journal_v3_reaudit_055/logs/r1_angle_coder/${RID}.log"
mkdir -p "$WD" "$(dirname "$LOG")"
# Auto-resume: if this work_dir already holds a checkpoint (e.g. seed1 crashed at epoch 8
# via NCCL watchdog), resume from it instead of restarting from scratch.
RESUME=""
if [ -f "$WD/last_checkpoint" ]; then RESUME="--resume"; echo "[$(date '+%F %T')] RESUME detected in $WD" | tee -a "$LOG"; fi
# NCCL robustness: the seed1 crash was a watchdog heartbeat timeout (600s) caused by a
# collective stalling while a co-tenant project (D17) saturated a GPU. Raise the heartbeat
# and collective timeouts so transient contention does not abort a healthy run.
export TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC=3600
export TORCH_NCCL_BLOCKING_WAIT=0
export TORCH_NCCL_ASYNC_ERROR_HANDLING=1
export NCCL_TIMEOUT=3600
# reduce CUDA fragmentation under GPU co-tenancy (the OOM error hint)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "[$(date '+%F %T')] LAUNCH $RID 4-GPU seed=$SEED resume='$RESUME' cfg=$CFG" | tee -a "$LOG"
CUDA_VISIBLE_DEVICES=0,1,2,3 $PY -m torch.distributed.run \
  --nproc_per_node=4 --master_port="$PORT" \
  "$TR" "$CFG" --launcher pytorch --work-dir "$WD" $RESUME \
  --cfg-options randomness.seed="$SEED" >> "$LOG" 2>&1
RC=$?
echo "[$(date '+%F %T')] EXIT $RID rc=$RC" | tee -a "$LOG"
exit $RC

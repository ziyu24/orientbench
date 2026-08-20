#!/usr/bin/env bash
# Promote only a normal, finite 500-iteration G1 smoke into the isolated G2.
set -euo pipefail
root=/home/rspip/cqc/pro/study/orientbench
g1="$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g1/dota_psc_pef_batched_rotated_grid_static_smoke_500"
g2="$root/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid"
log="$g1/train.log"
while ! grep -q 'Saving checkpoint at 1 epochs' "$log" 2>/dev/null; do
  if grep -qiE 'Traceback|ChildFailedError|RuntimeError|OutOfMemory|grad_norm: (nan|inf)' "$log" 2>/dev/null; then echo G1_ABNORMAL; exit 1; fi
  sleep 30
done
if grep -qiE 'Traceback|ChildFailedError|RuntimeError|OutOfMemory|grad_norm: (nan|inf)' "$log"; then echo G1_ABNORMAL; exit 1; fi
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}" CUDA_VISIBLE_DEVICES=0 python "$root/experiments/r049_rev2_pef_obb/verify_rotated_grid_gradients.py" \
  --config "$root/configs/r049_rev2_pef_obb/dota_psc_pef_batched_rotated_grid_static_smoke_500.py" \
  --out "$g1/full_model_gradient.json" >"$g1/full_model_gradient.log" 2>&1
tmux has-session -t =orientbench_r049rev2_grid 2>/dev/null && tmux kill-session -t =orientbench_r049rev2_grid || true
tmux has-session -t =orientbench_r049rev2_grid_supervisor 2>/dev/null && tmux kill-session -t =orientbench_r049rev2_grid_supervisor || true
mkdir -p "$g2/dota_psc_cont"
tmux new-session -d -s orientbench_r049rev2_grid -c "$root"
tmux send-keys -t orientbench_r049rev2_grid "MASTER_PORT=29821 bash experiments/r049_rev2_pef_obb/run_g2_arm.sh configs/r049_rev2_pef_obb/dota_psc_cont_rotated_grid_full.py > $g2/dota_psc_cont/train.log 2>&1" Enter
tmux new-session -d -s orientbench_r049rev2_grid_supervisor -c "$root"
tmux send-keys -t orientbench_r049rev2_grid_supervisor "bash experiments/r049_rev2_pef_obb/supervise_g2_rotated_grid_sequence.sh > $g2/supervisor.log 2>&1" Enter
echo G1_NORMAL_G2_STARTED

#!/usr/bin/env bash
# Persistent r051 G1 supervisor.  It waits for the already-running single-RoI
# arm, then runs the two OOM-interrupted arms one at a time on all four GPUs,
# exports raw predictions, and produces the immutable G1 decision package.
set -euo pipefail

root=/home/rspip/cqc/pro/study/orientbench
base="$root/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1"
log="$base/g1_supervisor.log"
exec >>"$log" 2>&1
echo "$(date -Is) supervisor started"

while tmux has-session -t orientbench_r051_g1_single_roi_quality 2>/dev/null; do
  sleep 30
done
test -s "$base/dota_orcnn_single_roi_quality_frozenhost_3ep/epoch_3.pth"
echo "$(date -Is) single_roi_quality completed; starting CMR serial recovery"

R051_MASTER_PORT=29833 bash "$root/experiments/r051_cmr_obb/run_dota_orcnn_r051_g1_3ep.sh" cmr
test -s "$base/dota_orcnn_cmr_frozenhost_3ep/epoch_3.pth"
echo "$(date -Is) CMR completed; starting DIRECT_DIST serial recovery"

R051_MASTER_PORT=29834 bash "$root/experiments/r051_cmr_obb/run_dota_orcnn_r051_g1_3ep.sh" direct_dist
test -s "$base/dota_orcnn_direct_dist_frozenhost_3ep/epoch_3.pth"
echo "$(date -Is) all G1 arms completed; exporting raw predictions"

bash "$root/experiments/r051_cmr_obb/run_dota_orcnn_r051_g1_export.sh" single_roi_quality
bash "$root/experiments/r051_cmr_obb/run_dota_orcnn_r051_g1_export.sh" cmr
bash "$root/experiments/r051_cmr_obb/run_dota_orcnn_r051_g1_export.sh" direct_dist

source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}"
python "$root/experiments/r051_cmr_obb/build_g1_metrics.py" --base "$base" --out "$base/metrics"
python "$root/experiments/r051_cmr_obb/adjudicate_g1.py" --base "$base"
echo "$(date -Is) G1 supervisor completed"

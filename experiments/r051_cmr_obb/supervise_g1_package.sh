#!/usr/bin/env bash
# Persistent final evidence packager.  It deliberately does not decide G2: the
# frozen gate file is the only authority for that branch.
set -euo pipefail

root=/home/rspip/cqc/pro/study/orientbench
base="$root/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1"
log="$base/g1_package_supervisor.log"
exec >>"$log" 2>&1
echo "$(date -Is) evidence-packager started"

while tmux has-session -t orientbench_r051_g1_supervisor 2>/dev/null; do
  sleep 30
done

test -s "$base/metrics/g1_gate.json"
source /home/rspip/cqc/data/install/yes/bin/activate pcp-obb
export PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}"
python "$root/experiments/r051_cmr_obb/package_g1_evidence.py" --base "$base"
echo "$(date -Is) evidence-packager completed"

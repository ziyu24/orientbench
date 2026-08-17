#!/usr/bin/env bash
set -euo pipefail
root='/home/rspip/cqc/pro/study/orientbench'
unit="$root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/units/unit_010_lsknet_dior"
log="$unit/parity/supervisor.log"
while tmux has-session -t orientbench-r041-lsknet 2>/dev/null; do
  date --iso-8601=seconds >> "$log"
  sleep 30
done
if [[ -s "$unit/parity/identity.pkl" ]]; then
  printf '%s identity_complete_ready_for_parity_check\n' "$(date --iso-8601=seconds)" >> "$log"
else
  printf '%s identity_missing_unit_failure\n' "$(date --iso-8601=seconds)" >> "$log"
fi

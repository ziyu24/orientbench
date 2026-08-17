#!/usr/bin/env bash
set -euo pipefail
root='/home/rspip/cqc/pro/study/orientbench'
unit="$root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/units/unit_022_psc_dior"
log="$unit/views/supervisor.log"
while tmux has-session -t orientbench-r041-psc-v 2>/dev/null; do
  date --iso-8601=seconds >> "$log"
  sleep 30
done
if [[ -s "$unit/views/vflip.pkl" ]]; then
  printf '%s vflip_complete_unit_ready_for_normalization\n' "$(date --iso-8601=seconds)" >> "$log"
else
  printf '%s vflip_missing_unit_failure\n' "$(date --iso-8601=seconds)" >> "$log"
fi

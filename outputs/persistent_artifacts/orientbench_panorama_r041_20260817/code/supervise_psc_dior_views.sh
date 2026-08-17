#!/usr/bin/env bash
set -euo pipefail
root='/home/rspip/cqc/pro/study/orientbench'
unit="$root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/units/unit_022_psc_dior"
log="$unit/views/supervisor.log"
while tmux has-session -t orientbench-r041-psc-h 2>/dev/null; do
  date --iso-8601=seconds >> "$log"
  sleep 30
done
if [[ ! -s "$unit/views/hflip.pkl" ]]; then
  printf '%s hflip_missing_no_vflip\n' "$(date --iso-8601=seconds)" >> "$log"
  exit 0
fi
printf '%s hflip_complete_starting_vflip\n' "$(date --iso-8601=seconds)" >> "$log"
tmux new-session -d -s orientbench-r041-psc-v "cd '$root' && CUDA_VISIBLE_DEVICES=0 PYTHONNOUSERSITE=1 conda run --no-capture-output -n pcp-obb bash -lc 'cd /home/rspip/cqc/pro/study/third_party/mmrotate_1x && PYTHONNOUSERSITE=1 python tools/test.py $root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/code/psc_dior_vflip.py /home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth --out $unit/views/vflip.pkl --work-dir $unit/views' > '$unit/views/vflip.log' 2>&1"

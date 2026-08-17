#!/usr/bin/env bash
set -euo pipefail
root='/home/rspip/cqc/pro/study/orientbench'
unit="$root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/units/unit_010_lsknet_dior"
log="$unit/views/supervisor.log"
while tmux has-session -t orientbench-r041-lsk-h 2>/dev/null; do
  date --iso-8601=seconds >> "$log"
  sleep 30
done
if [[ ! -s "$unit/views/hflip.pkl" ]]; then
  printf '%s hflip_missing_no_vflip\n' "$(date --iso-8601=seconds)" >> "$log"
  exit 0
fi
printf '%s hflip_complete_starting_vflip\n' "$(date --iso-8601=seconds)" >> "$log"
tmux new-session -d -s orientbench-r041-lsk-v "cd '$root' && CUDA_VISIBLE_DEVICES=1 PYTHONNOUSERSITE=1 conda run --no-capture-output -n pcp-obb-soda bash -lc 'cd /home/rspip/cqc/pro/study/third_party/Fourier-Angle-Alignment && PYTHONNOUSERSITE=1 PYTHONPATH=\$PWD python tools/test.py $root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/code/lsknet_dior_vflip.py /home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/DIOR_trainval_test/best_mAP_7187_epoch_12.pth --out $unit/views/vflip.pkl --work-dir $unit/views' > '$unit/views/vflip.log' 2>&1"
while tmux has-session -t orientbench-r041-lsk-v 2>/dev/null; do
  date --iso-8601=seconds >> "$log"
  sleep 30
done
if [[ -s "$unit/views/vflip.pkl" ]]; then
  printf '%s vflip_complete_ready_for_normalization\n' "$(date --iso-8601=seconds)" >> "$log"
else
  printf '%s vflip_missing_unit_failure\n' "$(date --iso-8601=seconds)" >> "$log"
fi

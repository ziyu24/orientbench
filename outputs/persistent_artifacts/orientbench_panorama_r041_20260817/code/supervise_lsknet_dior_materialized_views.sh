#!/usr/bin/env bash
set -euo pipefail
root='/home/rspip/cqc/pro/study/orientbench'
unit="$root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/units/unit_010_lsknet_dior"
log="$unit/views/supervisor.log"
while tmux has-session -t orientbench-r041-lsk-material-h 2>/dev/null; do
  date --iso-8601=seconds >> "$log"
  sleep 30
done
if [[ $(find "$root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/input_views/dior_hflip_png" -maxdepth 1 -type l | wc -l) -ne 11738 ]]; then
  printf '%s hflip_materialization_incomplete\n' "$(date --iso-8601=seconds)" >> "$log"
  exit 0
fi
printf '%s hflip_materialization_complete_starting_inference\n' "$(date --iso-8601=seconds)" >> "$log"
tmux new-session -d -s orientbench-r041-lsk-h "cd '$root' && CUDA_VISIBLE_DEVICES=1 PYTHONNOUSERSITE=1 conda run --no-capture-output -n pcp-obb-soda bash -lc 'cd /home/rspip/cqc/pro/study/third_party/Fourier-Angle-Alignment && PYTHONNOUSERSITE=1 PYTHONPATH=\$PWD python tools/test.py $root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/code/lsknet_dior_hflip.py /home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/DIOR_trainval_test/best_mAP_7187_epoch_12.pth --out $unit/views/hflip.pkl --work-dir $unit/views' >> '$unit/views/hflip.log' 2>&1"
exec "$root/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/code/supervise_lsknet_dior_views.sh"

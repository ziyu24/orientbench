#!/bin/bash
ENV=/home/rspip/anaconda3/envs/mr_dev1x
CK22=/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth
CK10=/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/DIOR_trainval_test/best_mAP_7187_epoch_12.pth
run() { CUDA_VISIBLE_DEVICES=0,1,2,3 OMP_NUM_THREADS=6 $ENV/bin/python -m torch.distributed.run --nproc_per_node=4 --master_port=$3 $ENV/lib/python3.10/site-packages/mmdet/.mim/tools/test.py measure_fix_v2/configs/tta_$1.py $2 --launcher pytorch ; }
P=29970
for tf in identity hflip vflip; do run DIOR-R_22_$tf $CK22 $P; P=$((P+1)); done
for tf in identity hflip vflip; do run DIOR-R_10_$tf $CK10 $P; P=$((P+1)); done
echo TTA_DRIVER_DONE

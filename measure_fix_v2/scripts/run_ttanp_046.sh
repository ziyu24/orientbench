#!/bin/bash
ENV=/home/rspip/anaconda3/envs/mr_dev1x
CK61=/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/best_mAP_5489_epoch_32.pth
CK4=/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/best_mAP_7295_epoch_09.pth
run(){ CUDA_VISIBLE_DEVICES=0,1,2,3 OMP_NUM_THREADS=6 $ENV/bin/python -m torch.distributed.run --nproc_per_node=4 --master_port=$3 $ENV/lib/python3.10/site-packages/mmdet/.mim/tools/test.py measure_fix_v2/configs/ttanp_$1.py $2 --launcher pytorch; }
P=29995
for tf in identity hflip vflip; do run DIOR-R_61_$tf $CK61 $P; P=$((P+1)); done
for tf in identity hflip vflip; do run SODA-A_4_$tf $CK4 $P; P=$((P+1)); done
echo TTANP_DONE

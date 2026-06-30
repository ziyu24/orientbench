#!/bin/bash
ENV=/home/rspip/anaconda3/envs/mr_dev1x
CK5=/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/FAIR1M_train_only_val/best_mAP_5900_epoch_12.pth
P=29991
for tf in identity hflip vflip; do CUDA_VISIBLE_DEVICES=0,1,2,3 OMP_NUM_THREADS=6 $ENV/bin/python -m torch.distributed.run --nproc_per_node=4 --master_port=$P $ENV/lib/python3.10/site-packages/mmdet/.mim/tools/test.py measure_fix_v2/configs/ttanp_FAIR1M-v1.0_5_$tf.py $CK5 --launcher pytorch; P=$((P+1)); done
echo TTANP5_DONE

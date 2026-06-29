#!/bin/bash
ENV=/home/rspip/anaconda3/envs/mr_dev1x
CK10=/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/DIOR_trainval_test/best_mAP_7187_epoch_12.pth
P=29980
for tf in identity hflip vflip; do
  CUDA_VISIBLE_DEVICES=0,1,2,3 OMP_NUM_THREADS=6 $ENV/bin/python -m torch.distributed.run --nproc_per_node=4 --master_port=$P $ENV/lib/python3.10/site-packages/mmdet/.mim/tools/test.py measure_fix_v2/configs/tta_DIOR-R_10_$tf.py $CK10 --launcher pytorch
  P=$((P+1))
done
echo TTA10_DONE

#!/bin/bash
ENV=/home/rspip/anaconda3/envs/mr_dev1x
CKS=/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/best_mAP_5991_epoch_12.pth
CKF=/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/best_mAP_3462_epoch_12.pth
run(){ CUDA_VISIBLE_DEVICES=0,1,2,3 OMP_NUM_THREADS=6 $ENV/bin/python -m torch.distributed.run --nproc_per_node=4 --master_port=$3 $ENV/lib/python3.10/site-packages/mmdet/.mim/tools/test.py measure_fix_v2/configs/ttacov_$1.py $2 --launcher pytorch; }
P=29990
run FAIR1M-v1.0_24_hflip $CKF $P; P=$((P+1))
run FAIR1M-v1.0_24_vflip $CKF $P; P=$((P+1))
run SODA-A_23_hflip $CKS $P; P=$((P+1))
run SODA-A_23_vflip $CKS $P; P=$((P+1))
echo TTACOV_DONE

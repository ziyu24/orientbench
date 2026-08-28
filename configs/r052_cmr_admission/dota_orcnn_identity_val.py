_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py'

# Frozen r052 G0 identity-parity evaluation.  This config changes no host
# model, split, checkpoint, or metric and is deliberately separate from r051.
_data_root = '/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/'
val_dataloader = dict(dataset=dict(data_root=_data_root))
test_dataloader = dict(dataset=dict(data_root=_data_root))
val_evaluator = dict(type='DOTAMetric', metric='mAP', iou_thrs=[.5])
test_evaluator = dict(type='DOTAMetric', metric='mAP', iou_thrs=[.5])
load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth'
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g0/identity_val'

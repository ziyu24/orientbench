_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py'

_data_root = '/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/'
custom_imports = dict(imports=['experiments.r052_cmr_admission.joint_api',
                               'experiments.r052_cmr_admission.joint_roi_head'],
                      allow_failed_imports=False)
train_dataloader = dict(dataset=dict(data_root=_data_root), batch_size=1)
val_cfg = None
val_dataloader = None
val_evaluator = None
model = dict(roi_head=dict(type='R052JointRoIHead', r052_mode='cmr',
                           r052_loss_weight=.15, r052_num_classes=15))
load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth'
train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=20, val_interval=1000000)
model_wrapper_cfg = dict(type='MMDistributedDataParallel', find_unused_parameters=True)
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/cmr_joint_smoke_20'

_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py'

custom_imports = dict(
    imports=['experiments.r051_cmr_obb.cmr_core',
             'experiments.r051_cmr_obb.cmr_rpn',
             'experiments.r051_cmr_obb.cmr_roi_head',
             'experiments.r051_cmr_obb.freeze_hook'],
    allow_failed_imports=False)

_data_root = '/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/'
train_dataloader = dict(dataset=dict(data_root=_data_root))
val_dataloader = dict(dataset=dict(data_root=_data_root))
test_dataloader = dict(dataset=dict(data_root=_data_root))

model = dict(
    rpn_head=dict(type='CMRProvenanceOrientedRPNHead'),
    roi_head=dict(type='CMRStandardRoIHead', cmr_loss_weight=.15,
                  cmr_num_classes=15))

load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth'
train_cfg = dict(type='EpochBasedTrainLoop', max_epochs=3, val_interval=1)
custom_hooks = [dict(type='CMRFreezeHostHook')]
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_cmr_frozenhost_3ep'

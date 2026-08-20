_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DOTA10_train_val/config.py'

custom_imports = dict(
    imports=['experiments.r049_rev2_pef_obb.checkpoint_compat'],
    allow_failed_imports=False)

# The archived portable config points at a retired split alias.  This is the
# existing DOTA-v1.0 train/val asset used by the valid July PSC runs; it is a
# path-only repair and does not alter the detector recipe or evaluator.
data_root = '/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/'

train_dataloader = dict(dataset=dict(data_root=data_root))
val_dataloader = dict(dataset=dict(data_root=data_root))
test_dataloader = dict(dataset=dict(data_root=data_root))

load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_5562_epoch_12.pth'
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g0/dota_psc_baseline_parity'

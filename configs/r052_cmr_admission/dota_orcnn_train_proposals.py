_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py'

# G1 reads DOTA train only.  The proposal export is a deterministic baseline
# inference pass: no augmentation, no validation data, no hyperparameter use.
_data_root = '/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/'
test_dataloader = dict(
    dataset=dict(
        data_root=_data_root,
        ann_file='train/annfiles/',
        data_prefix=dict(img_path='train/images/')))
test_evaluator = dict(type='DOTAMetric', metric='mAP', iou_thrs=[.5])
load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth'
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/train_proposal_export'

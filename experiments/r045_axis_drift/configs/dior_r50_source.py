_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/cell03_orcnn_dior_sgd_lr020.py'

test_dataloader = dict(
    batch_size=1,
    num_workers=2,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type='DOTADataset',
        data_root='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_dior_subset',
        ann_file='annfiles',
        data_prefix=dict(img_path='images'),
        img_suffix='jpg',
        test_mode=True,
        filter_cfg=None,
        pipeline=[
            dict(type='mmdet.LoadImageFromFile', backend_args=None),
            dict(type='mmdet.Resize', scale=(1024, 1024), keep_ratio=True),
            dict(type='mmdet.PackDetInputs', meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'scale_factor', 'flip', 'flip_direction')),
        ]))
test_evaluator = dict(
    _delete_=True,
    type='mmdet.DumpDetResults',
    out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_predictions/dior_r50.pkl')
load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/best_dota_mAP_epoch_11.pth'
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_work/dior_r50'

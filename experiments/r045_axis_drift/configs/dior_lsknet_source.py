_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/DIOR_trainval_test/config.py'

data = dict(
    samples_per_gpu=1,
    workers_per_gpu=2,
    test=dict(
        ann_file='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_dior_subset/annfiles/',
        img_prefix='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_dior_subset/images/',
        pipeline=[
            dict(type='LoadImageFromFile'),
            dict(type='MultiScaleFlipAug', img_scale=(1024, 1024), flip=False, transforms=[
                dict(type='RResize'),
                dict(type='Normalize', mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True),
                dict(type='Pad', size_divisor=32),
                dict(type='DefaultFormatBundle'),
                dict(type='Collect', keys=['img'])]),
        ]))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_work/dior_lsknet'

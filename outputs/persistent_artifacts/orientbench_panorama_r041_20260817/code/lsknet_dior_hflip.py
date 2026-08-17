_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/DIOR_trainval_test/config.py'

data = dict(
    test=dict(
        ann_file='/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test/',
        img_prefix='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/input_views/dior_hflip_png/',
        pipeline=[
            dict(type='LoadImageFromFile'),
            dict(type='MultiScaleFlipAug', img_scale=(1024, 1024), flip=False, transforms=[
                     dict(type='RResize'),
                     dict(type='Normalize', mean=[123.675, 116.28, 103.53],
                          std=[58.395, 57.12, 57.375], to_rgb=True),
                     dict(type='Pad', size_divisor=32),
                     dict(type='DefaultFormatBundle'),
                     dict(type='Collect', keys=['img'])]),
        ],
        version='le90'))

_base_ = [
    '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py'
]

data_root = '/home/rspip/cqc/data/dataset/fair1m1.0/split/'

train_pipeline = [
    dict(type='mmdet.LoadImageFromFile'),
    dict(type='mmdet.LoadAnnotations', with_bbox=True, box_type='qbox'),
    dict(type='ConvertBoxType', box_type_mapping=dict(gt_bboxes='rbox')),
    dict(type='mmdet.Resize', scale=(1024, 1024), keep_ratio=True),
    dict(type='mmdet.RandomFlip', prob=0.75,
         direction=['horizontal', 'vertical', 'diagonal']),
    dict(type='mmdet.PackDetInputs'),
]
val_pipeline = [
    dict(type='mmdet.LoadImageFromFile'),
    dict(type='mmdet.Resize', scale=(1024, 1024), keep_ratio=True),
    dict(type='mmdet.LoadAnnotations', with_bbox=True, box_type='qbox'),
    dict(type='ConvertBoxType', box_type_mapping=dict(gt_bboxes='rbox')),
    dict(type='mmdet.PackDetInputs',
         meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'scale_factor')),
]

train_dataloader = dict(
    batch_size=1,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    batch_sampler=None,
    dataset=dict(
        _delete_=True,
        type='FAIRDataset',
        data_root=data_root,
        ann_file='train_80/annfiles/',
        data_prefix=dict(img_path='train_80/images/'),
        filter_cfg=dict(filter_empty_gt=True),
        pipeline=train_pipeline))
val_dataloader = dict(
    batch_size=1,
    num_workers=4,
    persistent_workers=True,
    drop_last=False,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        _delete_=True,
        type='FAIRDataset',
        data_root=data_root,
        ann_file='val_20/annfiles/',
        data_prefix=dict(img_path='val_20/images/'),
        test_mode=True,
        pipeline=val_pipeline))
test_dataloader = val_dataloader
val_evaluator = dict(_delete_=True, type='DOTAMetric', metric='mAP')
test_evaluator = val_evaluator

default_hooks = dict(
    checkpoint=dict(type='CheckpointHook', interval=1, max_keep_ckpts=1,
                    save_best='dota/mAP'),
    logger=dict(type='LoggerHook', interval=50))
train_cfg = dict(type='EpochBasedTrainLoop', max_epochs=12, val_interval=1)
randomness = dict(seed=0, deterministic=False)
work_dir = None
load_from = None
resume = False

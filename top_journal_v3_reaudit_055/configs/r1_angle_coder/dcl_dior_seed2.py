angle_version = 'le90'
backend_args = None
custom_imports = dict(
    allow_failed_imports=False, imports=[
        'orientbench_ext.dcl_coder',
    ])
data_root = '/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/'
dataset_type = 'DOTADataset'
default_hooks = dict(
    checkpoint=dict(
        interval=1, max_keep_ckpts=1, save_best='auto', type='CheckpointHook'),
    logger=dict(interval=50, type='LoggerHook'),
    param_scheduler=dict(type='ParamSchedulerHook'),
    sampler_seed=dict(type='DistSamplerSeedHook'),
    timer=dict(type='IterTimerHook'),
    visualization=dict(type='mmdet.DetVisualizationHook'))
default_scope = 'mmrotate'
env_cfg = dict(
    cudnn_benchmark=False,
    dist_cfg=dict(backend='nccl'),
    mp_cfg=dict(mp_start_method='fork', opencv_num_threads=0))
launcher = 'pytorch'
load_from = None
log_level = 'INFO'
log_processor = dict(by_epoch=True, type='LogProcessor', window_size=50)
metainfo = dict(
    classes=(
        'airplane',
        'airport',
        'baseballfield',
        'basketballcourt',
        'bridge',
        'chimney',
        'dam',
        'Expressway-Service-area',
        'Expressway-toll-station',
        'golffield',
        'groundtrackfield',
        'harbor',
        'overpass',
        'ship',
        'stadium',
        'storagetank',
        'tenniscourt',
        'trainstation',
        'vehicle',
        'windmill',
    ))
model = dict(
    backbone=dict(
        depth=50,
        frozen_stages=1,
        init_cfg=dict(checkpoint='torchvision://resnet50', type='Pretrained'),
        norm_cfg=dict(requires_grad=True, type='BN'),
        norm_eval=True,
        num_stages=4,
        out_indices=(
            0,
            1,
            2,
            3,
        ),
        style='pytorch',
        type='mmdet.ResNet'),
    bbox_head=dict(
        anchor_generator=dict(
            angle_version=None,
            octave_base_scale=4,
            ratios=[
                1.0,
                0.5,
                2.0,
            ],
            scales_per_octave=3,
            strides=[
                8,
                16,
                32,
                64,
                128,
            ],
            type='FakeRotatedAnchorGenerator'),
        angle_coder=dict(angle_version='le90', omega=1, type='DCLCoder'),
        bbox_coder=dict(
            angle_version='le90',
            edge_swap=True,
            norm_factor=None,
            proj_xy=True,
            target_means=(
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ),
            target_stds=(
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ),
            type='DeltaXYWHTRBBoxCoder'),
        feat_channels=256,
        in_channels=256,
        loss_angle=dict(
            loss_weight=0.8, type='mmdet.CrossEntropyLoss', use_sigmoid=True),
        loss_bbox=dict(loss_weight=0.5, type='mmdet.L1Loss'),
        loss_cls=dict(
            alpha=0.25,
            gamma=2.0,
            loss_weight=1.0,
            type='mmdet.FocalLoss',
            use_sigmoid=True),
        num_classes=20,
        stacked_convs=4,
        type='AngleBranchRetinaHead',
        use_normalized_angle_feat=False),
    data_preprocessor=dict(
        bgr_to_rgb=True,
        boxtype2tensor=False,
        mean=[
            123.675,
            116.28,
            103.53,
        ],
        pad_size_divisor=32,
        std=[
            58.395,
            57.12,
            57.375,
        ],
        type='mmdet.DetDataPreprocessor'),
    neck=dict(
        add_extra_convs='on_input',
        in_channels=[
            256,
            512,
            1024,
            2048,
        ],
        num_outs=5,
        out_channels=256,
        start_level=1,
        type='mmdet.FPN'),
    test_cfg=dict(
        max_per_img=2000,
        min_bbox_size=0,
        nms=dict(iou_threshold=0.1, type='nms_rotated'),
        nms_pre=2000,
        score_thr=0.05),
    train_cfg=dict(
        allowed_border=-1,
        assigner=dict(
            ignore_iof_thr=-1,
            iou_calculator=dict(type='RBboxOverlaps2D'),
            min_pos_iou=0,
            neg_iou_thr=0.4,
            pos_iou_thr=0.5,
            type='mmdet.MaxIoUAssigner'),
        debug=False,
        pos_weight=-1,
        sampler=dict(type='mmdet.PseudoSampler')),
    type='mmdet.RetinaNet')
optim_wrapper = dict(
    clip_grad=dict(max_norm=35, norm_type=2),
    optimizer=dict(lr=0.005, momentum=0.9, type='SGD', weight_decay=0.0001),
    type='AmpOptimWrapper')
param_scheduler = [
    dict(
        begin=0,
        by_epoch=False,
        end=500,
        start_factor=0.3333333333333333,
        type='LinearLR'),
    dict(
        begin=0,
        by_epoch=True,
        end=12,
        gamma=0.1,
        milestones=[
            8,
            11,
        ],
        type='MultiStepLR'),
]
randomness = dict(deterministic=False, seed=2)
resume = False
test_cfg = dict(type='TestLoop')
test_dataloader = dict(
    batch_size=1,
    dataset=dict(
        ann_file='annfiles_dotaformat/test/',
        data_prefix=dict(img_path='dotaformat_images/test/'),
        data_root=
        '/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/',
        img_suffix='jpg',
        metainfo=dict(
            classes=(
                'airplane',
                'airport',
                'baseballfield',
                'basketballcourt',
                'bridge',
                'chimney',
                'dam',
                'Expressway-Service-area',
                'Expressway-toll-station',
                'golffield',
                'groundtrackfield',
                'harbor',
                'overpass',
                'ship',
                'stadium',
                'storagetank',
                'tenniscourt',
                'trainstation',
                'vehicle',
                'windmill',
            )),
        pipeline=[
            dict(backend_args=None, type='mmdet.LoadImageFromFile'),
            dict(keep_ratio=True, scale=(
                1024,
                1024,
            ), type='mmdet.Resize'),
            dict(
                box_type='qbox', type='mmdet.LoadAnnotations', with_bbox=True),
            dict(
                box_type_mapping=dict(gt_bboxes='rbox'),
                type='ConvertBoxType'),
            dict(
                meta_keys=(
                    'img_id',
                    'img_path',
                    'ori_shape',
                    'img_shape',
                    'scale_factor',
                ),
                type='mmdet.PackDetInputs'),
        ],
        test_mode=True,
        type='DOTADataset'),
    drop_last=False,
    num_workers=20,
    persistent_workers=True,
    sampler=dict(shuffle=False, type='DefaultSampler'))
test_evaluator = dict(metric='mAP', type='DOTAMetric')
test_pipeline = [
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(keep_ratio=True, scale=(
        1024,
        1024,
    ), type='mmdet.Resize'),
    dict(
        meta_keys=(
            'img_id',
            'img_path',
            'ori_shape',
            'img_shape',
            'scale_factor',
        ),
        type='mmdet.PackDetInputs'),
]
train_cfg = dict(max_epochs=12, type='EpochBasedTrainLoop', val_interval=1)
train_dataloader = dict(
    batch_sampler=None,
    batch_size=1,
    dataset=dict(
        ann_file='annfiles_dotaformat/trainval/',
        data_prefix=dict(img_path='dotaformat_images/trainval/'),
        data_root=
        '/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/',
        filter_cfg=dict(filter_empty_gt=True),
        img_suffix='jpg',
        metainfo=dict(
            classes=(
                'airplane',
                'airport',
                'baseballfield',
                'basketballcourt',
                'bridge',
                'chimney',
                'dam',
                'Expressway-Service-area',
                'Expressway-toll-station',
                'golffield',
                'groundtrackfield',
                'harbor',
                'overpass',
                'ship',
                'stadium',
                'storagetank',
                'tenniscourt',
                'trainstation',
                'vehicle',
                'windmill',
            )),
        pipeline=[
            dict(backend_args=None, type='mmdet.LoadImageFromFile'),
            dict(
                box_type='qbox', type='mmdet.LoadAnnotations', with_bbox=True),
            dict(
                box_type_mapping=dict(gt_bboxes='rbox'),
                type='ConvertBoxType'),
            dict(keep_ratio=True, scale=(
                1024,
                1024,
            ), type='mmdet.Resize'),
            dict(
                direction=[
                    'horizontal',
                    'vertical',
                    'diagonal',
                ],
                prob=0.75,
                type='mmdet.RandomFlip'),
            dict(type='mmdet.PackDetInputs'),
        ],
        type='DOTADataset'),
    num_workers=20,
    persistent_workers=True,
    sampler=dict(shuffle=True, type='DefaultSampler'))
train_pipeline = [
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(box_type='qbox', type='mmdet.LoadAnnotations', with_bbox=True),
    dict(box_type_mapping=dict(gt_bboxes='rbox'), type='ConvertBoxType'),
    dict(keep_ratio=True, scale=(
        1024,
        1024,
    ), type='mmdet.Resize'),
    dict(
        direction=[
            'horizontal',
            'vertical',
            'diagonal',
        ],
        prob=0.75,
        type='mmdet.RandomFlip'),
    dict(type='mmdet.PackDetInputs'),
]
val_cfg = dict(type='ValLoop')
val_dataloader = dict(
    batch_size=1,
    dataset=dict(
        ann_file='annfiles_dotaformat/test/',
        data_prefix=dict(img_path='dotaformat_images/test/'),
        data_root=
        '/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/',
        img_suffix='jpg',
        metainfo=dict(
            classes=(
                'airplane',
                'airport',
                'baseballfield',
                'basketballcourt',
                'bridge',
                'chimney',
                'dam',
                'Expressway-Service-area',
                'Expressway-toll-station',
                'golffield',
                'groundtrackfield',
                'harbor',
                'overpass',
                'ship',
                'stadium',
                'storagetank',
                'tenniscourt',
                'trainstation',
                'vehicle',
                'windmill',
            )),
        pipeline=[
            dict(backend_args=None, type='mmdet.LoadImageFromFile'),
            dict(keep_ratio=True, scale=(
                1024,
                1024,
            ), type='mmdet.Resize'),
            dict(
                box_type='qbox', type='mmdet.LoadAnnotations', with_bbox=True),
            dict(
                box_type_mapping=dict(gt_bboxes='rbox'),
                type='ConvertBoxType'),
            dict(
                meta_keys=(
                    'img_id',
                    'img_path',
                    'ori_shape',
                    'img_shape',
                    'scale_factor',
                ),
                type='mmdet.PackDetInputs'),
        ],
        test_mode=True,
        type='DOTADataset'),
    drop_last=False,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(shuffle=False, type='DefaultSampler'))
val_evaluator = dict(metric='mAP', type='DOTAMetric')
val_pipeline = [
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(keep_ratio=True, scale=(
        1024,
        1024,
    ), type='mmdet.Resize'),
    dict(box_type='qbox', type='mmdet.LoadAnnotations', with_bbox=True),
    dict(box_type_mapping=dict(gt_bboxes='rbox'), type='ConvertBoxType'),
    dict(
        meta_keys=(
            'img_id',
            'img_path',
            'ori_shape',
            'img_shape',
            'scale_factor',
        ),
        type='mmdet.PackDetInputs'),
]
vis_backends = [
    dict(type='LocalVisBackend'),
]
visualizer = dict(
    name='visualizer',
    type='RotLocalVisualizer',
    vis_backends=[
        dict(type='LocalVisBackend'),
    ])
work_dir = './work_dirs/r1/DCL__dior__seed2'

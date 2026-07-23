"""Frozen B4 external RotatedFCOS-PSCD configuration on DOTA-v1.0 train->val."""

angle_version = "le90"
data_root = "/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/"
dataset_type = "DOTADataset"
default_scope = "mmrotate"
backend_args = None

model = dict(
    type="mmdet.FCOS",
    data_preprocessor=dict(
        type="mmdet.DetDataPreprocessor",
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        bgr_to_rgb=True,
        pad_size_divisor=32,
        boxtype2tensor=False),
    backbone=dict(
        type="mmdet.ResNet",
        depth=50,
        num_stages=4,
        out_indices=(0, 1, 2, 3),
        frozen_stages=1,
        norm_cfg=dict(type="BN", requires_grad=True),
        norm_eval=True,
        style="pytorch",
        init_cfg=dict(type="Pretrained", checkpoint="torchvision://resnet50")),
    neck=dict(
        type="mmdet.FPN",
        in_channels=[256, 512, 1024, 2048],
        out_channels=256,
        start_level=1,
        add_extra_convs="on_output",
        num_outs=5,
        relu_before_extra_convs=True),
    bbox_head=dict(
        type="RotatedFCOSHead",
        num_classes=15,
        in_channels=256,
        stacked_convs=4,
        feat_channels=256,
        strides=[8, 16, 32, 64, 128],
        center_sampling=True,
        center_sample_radius=1.5,
        norm_on_bbox=True,
        centerness_on_reg=True,
        use_hbbox_loss=True,
        scale_angle=False,
        bbox_coder=dict(type="DistanceAnglePointCoder", angle_version=angle_version),
        angle_coder=dict(
            type="PSCCoder",
            angle_version=angle_version,
            dual_freq=True,
            num_step=3,
            thr_mod=0.47),
        loss_cls=dict(
            type="mmdet.FocalLoss",
            use_sigmoid=True,
            gamma=2.0,
            alpha=0.25,
            loss_weight=1.0),
        loss_bbox=dict(type="mmdet.IoULoss", loss_weight=1.0),
        loss_angle=dict(type="mmdet.L1Loss", loss_weight=0.1),
        loss_centerness=dict(
            type="mmdet.CrossEntropyLoss", use_sigmoid=True, loss_weight=1.0)),
    train_cfg=None,
    test_cfg=dict(
        nms_pre=2000,
        min_bbox_size=0,
        score_thr=0.05,
        nms=dict(type="nms_rotated", iou_threshold=0.1),
        max_per_img=2000))

train_pipeline = [
    dict(type="mmdet.LoadImageFromFile", backend_args=backend_args),
    dict(type="mmdet.LoadAnnotations", with_bbox=True, box_type="qbox"),
    dict(type="ConvertBoxType", box_type_mapping=dict(gt_bboxes="rbox")),
    dict(type="mmdet.Resize", scale=(1024, 1024), keep_ratio=True),
    dict(
        type="mmdet.RandomFlip",
        prob=0.75,
        direction=["horizontal", "vertical", "diagonal"]),
    dict(type="mmdet.PackDetInputs")
]
val_pipeline = [
    dict(type="mmdet.LoadImageFromFile", backend_args=backend_args),
    dict(type="mmdet.Resize", scale=(1024, 1024), keep_ratio=True),
    dict(type="mmdet.LoadAnnotations", with_bbox=True, box_type="qbox"),
    dict(type="ConvertBoxType", box_type_mapping=dict(gt_bboxes="rbox")),
    dict(
        type="mmdet.PackDetInputs",
        meta_keys=("img_id", "img_path", "ori_shape", "img_shape", "scale_factor"))
]

train_dataloader = dict(
    batch_size=2,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type="DefaultSampler", shuffle=True),
    batch_sampler=None,
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file="train/annfiles/",
        data_prefix=dict(img_path="train/images/"),
        filter_cfg=dict(filter_empty_gt=True),
        pipeline=train_pipeline))
val_dataloader = dict(
    batch_size=1,
    num_workers=4,
    persistent_workers=True,
    drop_last=False,
    sampler=dict(type="DefaultSampler", shuffle=False),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file="val/annfiles/",
        data_prefix=dict(img_path="val/images/"),
        test_mode=True,
        pipeline=val_pipeline))
test_dataloader = val_dataloader
val_evaluator = dict(type="DOTAMetric", metric="mAP")
test_evaluator = val_evaluator

train_cfg = dict(type="EpochBasedTrainLoop", max_epochs=12, val_interval=1)
val_cfg = dict(type="ValLoop")
test_cfg = dict(type="TestLoop")
param_scheduler = [
    dict(type="LinearLR", start_factor=1.0 / 3, by_epoch=False, begin=0, end=500),
    dict(
        type="MultiStepLR",
        begin=0,
        end=12,
        by_epoch=True,
        milestones=[8, 11],
        gamma=0.1)
]
optim_wrapper = dict(
    type="OptimWrapper",
    optimizer=dict(type="SGD", lr=0.0025, momentum=0.9, weight_decay=0.0001),
    clip_grad=dict(max_norm=35, norm_type=2))

default_hooks = dict(
    timer=dict(type="IterTimerHook"),
    logger=dict(type="LoggerHook", interval=50),
    param_scheduler=dict(type="ParamSchedulerHook"),
    checkpoint=dict(type="CheckpointHook", interval=1, save_best="auto", max_keep_ckpts=2),
    sampler_seed=dict(type="DistSamplerSeedHook"),
    visualization=dict(type="mmdet.DetVisualizationHook"))
env_cfg = dict(
    cudnn_benchmark=False,
    mp_cfg=dict(mp_start_method="fork", opencv_num_threads=0),
    dist_cfg=dict(backend="nccl"))
vis_backends = [dict(type="LocalVisBackend")]
visualizer = dict(
    type="RotLocalVisualizer",
    vis_backends=vis_backends,
    name="visualizer")
log_processor = dict(type="LogProcessor", window_size=50, by_epoch=True)
log_level = "INFO"
load_from = None
resume = False
launcher = "pytorch"
randomness = dict(seed=0, deterministic=False)
work_dir = "top_journal_v3_reaudit_055/paper_B_psc_mechanism/artifacts/b4_training/seed0"


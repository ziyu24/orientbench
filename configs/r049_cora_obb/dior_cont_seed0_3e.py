_base_ = '../../top_journal_v3_reaudit_055/saur_stagea_r043_20260818/configs/dior_cont_3e.py'

randomness = dict(seed=20260819, deterministic=False)
train_dataloader = dict(dataset=dict(pipeline=[
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(box_type='qbox', type='mmdet.LoadAnnotations', with_bbox=True),
    dict(box_type_mapping=dict(gt_bboxes='rbox'), type='ConvertBoxType'),
    dict(type='mmdet.FilterAnnotations', min_gt_bbox_wh=(1, 1), keep_empty=True),
    dict(keep_ratio=True, scale=(1024, 1024), type='mmdet.Resize'),
    dict(direction=['horizontal', 'vertical', 'diagonal'], prob=.75, type='mmdet.RandomFlip'),
    dict(type='mmdet.PackDetInputs'),
]))
default_hooks = dict(checkpoint=dict(type='CheckpointHook', interval=1, max_keep_ckpts=1, save_best='auto'))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2/dior_cont_seed0'

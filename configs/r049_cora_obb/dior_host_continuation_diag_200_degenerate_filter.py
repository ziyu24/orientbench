_base_ = './dior_host_continuation_diag_200.py'

# Two source train annotations (04137:14 and 07007:37) are zero-area quadrilaterals.
# This project-local pipeline only excludes rbox width/height <= 1 before target
# encoding. It does not change files, images, train membership, evaluation, or
# any CORA component.
train_dataloader = dict(dataset=dict(pipeline=[
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(box_type='qbox', type='mmdet.LoadAnnotations', with_bbox=True),
    dict(box_type_mapping=dict(gt_bboxes='rbox'), type='ConvertBoxType'),
    dict(type='mmdet.FilterAnnotations', min_gt_bbox_wh=(1, 1), keep_empty=True),
    dict(keep_ratio=True, scale=(1024, 1024), type='mmdet.Resize'),
    dict(direction=['horizontal', 'vertical', 'diagonal'], prob=.75, type='mmdet.RandomFlip'),
    dict(type='mmdet.PackDetInputs'),
]))

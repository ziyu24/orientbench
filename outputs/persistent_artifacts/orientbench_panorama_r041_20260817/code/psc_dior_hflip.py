_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py'

test_dataloader = dict(
    dataset=dict(
        data_root='/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/',
        pipeline=[
            dict(type='mmdet.LoadImageFromFile'),
            dict(type='mmdet.Resize', scale=(1024, 1024), keep_ratio=True),
            dict(type='mmdet.LoadAnnotations', with_bbox=True, box_type='qbox'),
            dict(type='ConvertBoxType', box_type_mapping=dict(gt_bboxes='rbox')),
            dict(type='mmdet.RandomFlip', prob=1.0, direction='horizontal'),
            dict(type='mmdet.PackDetInputs', meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'scale_factor', 'flip', 'flip_direction')),
        ],
    )
)

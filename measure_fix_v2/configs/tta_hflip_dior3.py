_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/cell03_orcnn_dior_sgd_lr020.py']
_SCR = '/dev/shm/cqc/orientbench/tta/DIOR-R_3'
test_pipeline = [
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(keep_ratio=True, scale=(1024, 1024), type='mmdet.Resize'),
    dict(prob=1.0, direction='horizontal', type='mmdet.RandomFlip'),
    dict(meta_keys=('img_id','img_path','ori_shape','img_shape','scale_factor','flip','flip_direction'),
         type='mmdet.PackDetInputs'),
]
test_dataloader = dict(dataset=dict(pipeline=test_pipeline))
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path=_SCR + '/hflip.pkl')

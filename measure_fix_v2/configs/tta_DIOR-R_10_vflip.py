_base_ = ['/home/rspip/cqc/pro/study/orientbench/measure_fix_v2/configs/lsknet_dior10_patched.py']
_FARM = '/dev/shm/cqc/orientbench/measure_fix_v2_tta/DIOR-R/'
_pipe = [
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(keep_ratio=True, scale=(1024, 1024), type='mmdet.Resize'),
    dict(prob=1.0, direction='vertical', type='mmdet.RandomFlip'),
    dict(meta_keys=('img_id','img_path','ori_shape','img_shape','scale_factor','flip','flip_direction'), type='mmdet.PackDetInputs'),
]
test_dataloader = dict(dataset=dict(data_root=_FARM, ann_file='annfiles/', data_prefix=dict(img_path='images/'), pipeline=_pipe))
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/dev/shm/cqc/orientbench/measure_fix_v2_tta/preds/DIOR-R_10/vflip.pkl')
test_cfg = dict(type='mmdet.TestLoop')
default_scope = 'mmrotate'

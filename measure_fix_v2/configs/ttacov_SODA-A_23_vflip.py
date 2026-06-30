_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py']
_pipe = [
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(keep_ratio=True, scale=(1024, 1024), type='mmdet.Resize'),
    dict(prob=1.0, direction='vertical', type='mmdet.RandomFlip'),
    dict(meta_keys=('img_id','img_path','ori_shape','img_shape','scale_factor','flip','flip_direction'), type='mmdet.PackDetInputs'),
]
test_dataloader = dict(dataset=dict(pipeline=_pipe))
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/dev/shm/cqc/orientbench/measure_fix_v2_tta/preds/SODA-A_23/vflip.pkl')

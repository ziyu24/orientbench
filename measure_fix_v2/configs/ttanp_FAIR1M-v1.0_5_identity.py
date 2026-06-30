_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py']
_FARM='/dev/shm/cqc/orientbench/measure_fix_v2_tta/FAIR1M-v1.0/'
_pipe = [
    dict(backend_args=None, type='mmdet.LoadImageFromFile'),
    dict(keep_ratio=True, scale=(1024, 1024), type='mmdet.Resize'),

    dict(meta_keys=('img_id','img_path','ori_shape','img_shape','scale_factor','flip','flip_direction'), type='mmdet.PackDetInputs'),
]
test_dataloader = dict(dataset=dict(metainfo=dict(classes=('obj',)), data_root=_FARM, ann_file='annfiles/', data_prefix=dict(img_path='images/'), img_suffix='png', pipeline=_pipe))
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/dev/shm/cqc/orientbench/measure_fix_v2_tta/preds/FAIR1M-v1.0_5/identity.pkl')

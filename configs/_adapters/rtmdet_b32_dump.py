# Adapter (orientbench workspace): _base_ the frozen baseline config, override
# only test data paths + dump-predictions evaluator. Does not modify pth_data.
_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DOTA10_train_val_taos/config.py']
_sub = '/home/rspip/cqc/pro/study/orientbench/outputs/predictions/DOTA-v1.0/_dcal_subset/'
test_dataloader = dict(dataset=dict(data_root=_sub, ann_file='annfiles/', data_prefix=dict(img_path='images/')))
train_dataloader = dict(dataset=dict(data_root=_sub, ann_file='annfiles/', data_prefix=dict(img_path='images/')))
val_dataloader = dict(dataset=dict(data_root=_sub, ann_file='annfiles/', data_prefix=dict(img_path='images/')))
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/predictions/DOTA-v1.0/32/raw/result_dcal_b32.pkl')
val_evaluator = test_evaluator

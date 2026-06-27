_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DOTA15_train_val_taos/config.py']
_sub = '/home/rspip/cqc/pro/study/orientbench/outputs/predictions/DOTA-v1.5/_dcal_subset/'
test_dataloader = dict(dataset=dict(data_root=_sub, ann_file='annfiles/', data_prefix=dict(img_path='images/')))
val_dataloader = test_dataloader
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/predictions/DOTA-v1.5/33/raw/result_b33.pkl')
val_evaluator = test_evaluator

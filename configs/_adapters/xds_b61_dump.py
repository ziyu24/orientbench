_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py']
test_dataloader = dict(dataset=dict(data_root='/home/rspip/cqc/pro/study/orientbench/outputs/predictions/DIOR-R/_root/', ann_file='annfiles/', data_prefix=dict(img_path='images/')))
val_dataloader = test_dataloader
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/predictions/DIOR-R/61/raw/result_b61.pkl')
val_evaluator = test_evaluator

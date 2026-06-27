_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/config.py']
test_dataloader = dict(dataset=dict(data_root='/home/rspip/cqc/pro/study/orientbench/outputs/predictions/SODA-A/_root/', ann_file='annfiles/', data_prefix=dict(img_path='images/')))
val_dataloader = test_dataloader
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/predictions/SODA-A/4/raw/result_b4.pkl')
val_evaluator = test_evaluator

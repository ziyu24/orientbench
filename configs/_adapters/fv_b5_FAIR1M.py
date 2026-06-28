_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py']
test_dataloader = dict(dataset=dict(data_root='/dev/shm/cqc/orientbench/predictions/FAIR1M-v1.0/_root/', ann_file='annfiles/', data_prefix=dict(img_path='images/')))
val_dataloader = test_dataloader
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/dev/shm/cqc/orientbench/predictions/FAIR1M-v1.0/5/raw/result_b5.pkl')
val_evaluator = test_evaluator

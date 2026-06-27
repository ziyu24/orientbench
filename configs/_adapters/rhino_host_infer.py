_base_=['/home/rspip/cqc/pro/study/ai4rs_clone/projects/RHINO/configs/rhino_phc_haus_4scale_r50_2xb4_36e_dota.py']
_sub='/home/rspip/cqc/pro/study/orientbench/outputs/predictions/DOTA-v1.0/_dcal_subset/'
test_dataloader=dict(dataset=dict(data_root=_sub, ann_file='annfiles/', data_prefix=dict(img_path='images/')))
val_dataloader=test_dataloader
test_evaluator=dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/predictions/DOTA-v1.0/rhino_host/raw/result_rhino.pkl')
val_evaluator=test_evaluator

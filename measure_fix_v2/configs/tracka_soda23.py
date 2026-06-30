_base_ = ['/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py']
custom_imports = dict(imports=['track_a_pkg'], allow_failed_imports=False)
model = dict(bbox_head=dict(type='InstrumentedAngleBranchRetinaHead'))
test_evaluator = dict(_delete_=True, type='mmdet.DumpDetResults', out_file_path='/dev/shm/cqc/orientbench/measure_fix_v2/track_a/SODA-A_23.pkl')

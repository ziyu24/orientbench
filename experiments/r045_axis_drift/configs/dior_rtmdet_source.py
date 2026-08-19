_base_ = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/units/unit_061_rtmdet_s_dior/parity/rtmdet_s_dior_portable.py'

test_dataloader = dict(
    batch_size=1,
    num_workers=2,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        ann_file='annfiles',
        data_prefix=dict(img_path='images'),
        data_root='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_dior_subset'))
test_evaluator = dict(
    _delete_=True,
    type='mmdet.DumpDetResults',
    out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_predictions/dior_rtmdet.pkl')
load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/best_mAP_5489_epoch_32.pth'
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_work/dior_rtmdet'

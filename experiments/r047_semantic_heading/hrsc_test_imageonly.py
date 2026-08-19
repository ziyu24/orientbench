_base_ = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_predictions/work_r50_audit/hrsc_r50_audit.py'
custom_imports = dict(imports=['experiments.r047_semantic_heading.image_only_dataset'], allow_failed_imports=False)
test_dataloader = dict(
    batch_size=1,
    num_workers=2,
    persistent_workers=True,
    dataset=dict(
        type='R047ImageOnlyHRSC',
        ann_file='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818/partitions/T_cal_ids.txt',
        data_root='/home/rspip/cqc/data/dataset/HRSC2016/images',
        pipeline=[
            dict(type='mmdet.LoadImageFromFile'),
            dict(type='mmdet.Resize', scale=(800,512), keep_ratio=True),
            dict(type='mmdet.PackDetInputs', meta_keys=('img_id','img_path','ori_shape','img_shape','scale_factor','flip','flip_direction'))],
        test_mode=True),
    sampler=dict(shuffle=False, type='DefaultSampler'), drop_last=False)
test_evaluator = dict(type='mmdet.DumpDetResults', out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818/tcal_r50_predictions.pkl')
test_cfg = dict(type='TestLoop')
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818/tcal_r50_work'

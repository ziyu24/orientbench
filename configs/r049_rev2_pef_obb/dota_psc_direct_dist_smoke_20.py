_base_ = './dota_psc_direct_dist_full.py'
train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=20, val_interval=20)
default_hooks = dict(checkpoint=dict(type='CheckpointHook', interval=20, max_keep_ckpts=1))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g1/dota_psc_direct_dist_smoke_20'

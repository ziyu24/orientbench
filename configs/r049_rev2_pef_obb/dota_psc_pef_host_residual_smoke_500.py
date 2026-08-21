_base_ = './dota_psc_pef_rotated_grid_full.py'
train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=500, val_interval=500)
default_hooks = dict(checkpoint=dict(type='CheckpointHook', interval=500, max_keep_ckpts=1))
work_dir = ('/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/'
            'orientbench_r049_rev2_pef_obb_20260819/g1/'
            'dota_psc_pef_host_residual_smoke_500')

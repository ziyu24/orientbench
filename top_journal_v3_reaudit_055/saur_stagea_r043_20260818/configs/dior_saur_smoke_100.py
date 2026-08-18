_base_ = './dior_saur_3e.py'

# Four-GPU 100-iteration technical smoke; no scientific checkpoint is retained.
train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=100, val_interval=100)
default_hooks = dict(checkpoint=dict(type='CheckpointHook', interval=100, max_keep_ckpts=1))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818/dior_saur_smoke_100'

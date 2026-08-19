_base_ = '../../top_journal_v3_reaudit_055/saur_stagea_r043_20260818/configs/dior_cont_3e.py'

# Engineering diagnostic only: exact registered PSC host, same four-card batch,
# optimizer, LR, augmentation and schedule; validation is omitted because this
# isolates the training-side non-finite bbox value seen by G1.
train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=200, val_interval=100000)
default_hooks = dict(checkpoint=dict(type='CheckpointHook', interval=200, max_keep_ckpts=1))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g1/host_continuation_diag_200'

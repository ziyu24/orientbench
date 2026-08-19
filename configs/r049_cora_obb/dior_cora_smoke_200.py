_base_ = '../../top_journal_v3_reaudit_055/saur_stagea_r043_20260818/configs/dior_cont_3e.py'

custom_imports = dict(imports=['experiments.r049_cora_obb.cora_head'], allow_failed_imports=False)
model = dict(bbox_head=dict(type='CORAAngleBranchRetinaHead', vm_loss_weight=.10,
                            harm_loss_weight=.20, cf_loss_weight=.10, harm_bins=8))
train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=200, val_interval=200)
default_hooks = dict(checkpoint=dict(type='CheckpointHook', interval=200, max_keep_ckpts=1))
# G1 stability-only retry: retain the host optimizer, global batch, LR, BN and
# clipping, but execute its 200 diagnostic iterations in full precision.  The
# AMP continuation remains the formal G2 setting if this finite-gradient check
# passes; this setting is not a scientific hyperparameter choice.
optim_wrapper = dict(type='OptimWrapper', clip_grad=dict(max_norm=35, norm_type=2),
                     optimizer=dict(type='SGD', lr=.005, momentum=.9, weight_decay=.0001))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g1/dior_cora_smoke_200'

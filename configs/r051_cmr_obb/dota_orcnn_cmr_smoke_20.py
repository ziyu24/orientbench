_base_ = './dota_orcnn_cmr_frozenhost_3ep.py'

train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=20, val_interval=20)
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_cmr_smoke_20'

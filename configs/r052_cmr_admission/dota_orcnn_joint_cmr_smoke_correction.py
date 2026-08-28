_base_ = './dota_orcnn_joint_cmr_smoke.py'

# The correction smoke has its own immutable output root; prior r052 outputs
# remain historical evidence and are never overwritten.
train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=5, val_interval=1000000)
work_dir = ('/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/'
            'orientbench_r052_cmr_admission_20260828/g1/correction_cmr_joint_smoke_5')

_base_ = './dior_cont_3e.py'

custom_imports = dict(
    imports=['top_journal_v3_reaudit_055.saur_stagea_r043_20260818'],
    allow_failed_imports=False)
model = dict(bbox_head=dict(
    type='SAURAngleBranchRetinaHead',
    saur_loss_weight=.25,
    geometry_gate_slope=4.0,
    geometry_gate_center=.25))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818/dior_saur'

_base_ = './dota_psc_cont_full.py'
custom_imports = dict(imports=['experiments.r049_rev2_pef_obb.control_heads'], allow_failed_imports=False)
model = dict(bbox_head=dict(type='DirectDistributionAngleBranchRetinaHead'))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2/dota_psc_direct_dist'

_base_ = './dior_cont_seed0_3e.py'

custom_imports = dict(imports=['experiments.r049_cora_obb.cora_head'], allow_failed_imports=False)
model = dict(bbox_head=dict(type='CORAAngleBranchRetinaHead', vm_loss_weight=.10,
                            harm_loss_weight=.20, cf_loss_weight=.10, harm_bins=8))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2/dior_cora_seed0'

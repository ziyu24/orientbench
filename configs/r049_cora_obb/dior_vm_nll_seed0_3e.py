_base_ = './dior_cont_seed0_3e.py'

custom_imports = dict(imports=['experiments.r049_cora_obb.cora_head'], allow_failed_imports=False)
# The VM-NLL boundary arm has only the periodic proper loss: ordinal harm and
# counterfactual terms are exactly zero and cannot update the detector.
model = dict(bbox_head=dict(type='CORAAngleBranchRetinaHead', vm_loss_weight=.10,
                            harm_loss_weight=.0, cf_loss_weight=.0, harm_bins=8,
                            native_risk_mode='vm_concentration'))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2/dior_vm_nll_seed0'

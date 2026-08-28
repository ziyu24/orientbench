_base_ = './dota_orcnn_cmr_frozenhost_3ep.py'

# Frozen strong control: equal CMR parameterization and K-way residual angle
# distribution, but exactly one host-angle RoI observation per proposal.
model = dict(roi_head=dict(type='CMRStandardRoIHead', cmr_loss_weight=.15,
                           cmr_num_classes=15, observation_mode='direct_dist'))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_direct_dist_frozenhost_3ep'

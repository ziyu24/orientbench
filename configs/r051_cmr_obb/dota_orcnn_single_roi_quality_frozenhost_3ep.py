_base_ = './dota_orcnn_cmr_frozenhost_3ep.py'

# Frozen strong control: equal CMR parameterization but only one host-angle
# RoI and scalar orientation-quality supervision; it performs no angle change.
model = dict(roi_head=dict(type='CMRStandardRoIHead', cmr_loss_weight=.15,
                           cmr_num_classes=15, observation_mode='single_roi_quality'))
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_single_roi_quality_frozenhost_3ep'

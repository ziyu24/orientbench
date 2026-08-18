_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py'

# Fixed original SODA-A train -> val protocol; official test remains excluded.
val_evaluator = dict(type='DOTAMetric', metric='mAP', iou_thrs=[.5, .75])
test_evaluator = dict(type='DOTAMetric', metric='mAP', iou_thrs=[.5, .75])
train_cfg = dict(max_epochs=3, val_interval=1, type='EpochBasedTrainLoop')
load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/best_mAP_5991_epoch_12.pth'
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818/soda_cont'

_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/cell06_orcnn_hrsc_3x_sgd_lr020.py'
# Explicitly use consumed official val only; never inherit the test loader.
test_dataloader = val_dataloader
test_evaluator = val_evaluator
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/r50_val_parity_work'

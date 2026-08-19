"""Dedicated-environment R50 AP parity on consumed official validation data."""
import sys
import cv2
import numpy as np
# Registered checkpoints were serialized under NumPy 2; this tracked loader
# alias only restores pickle module names and does not alter package versions.
if not hasattr(np, '_core'):
    sys.modules.setdefault('numpy._core', np.core)
    sys.modules.setdefault('numpy._core.multiarray', np.core.multiarray)
    sys.modules.setdefault('numpy._core.numeric', np.core.numeric)
def main():
    from mmengine.config import Config
    from mmengine.runner import Runner
    from mmrotate.utils import register_all_modules
    register_all_modules()
    cfg=Config.fromfile('/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/cell06_orcnn_hrsc_3x_sgd_lr020.py')
    cfg.test_dataloader=cfg.val_dataloader
    cfg.test_evaluator=cfg.val_evaluator
    ds=cfg.test_dataloader.dataset
    ds.ann_file='/home/rspip/cqc/data/dataset/HRSC2016/splits/val.txt'
    ds.data_root='/home/rspip/cqc/data/dataset/HRSC2016/'
    ds.data_prefix=dict(sub_data_root='/home/rspip/cqc/data/dataset/HRSC2016/')
    ds.img_subdir='images'
    ds.ann_subdir='annfiles'
    cfg.load_from='/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth'
    cfg.work_dir='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/r50_val_parity_work'
    Runner.from_cfg(cfg).test()

if __name__ == '__main__':
    main()

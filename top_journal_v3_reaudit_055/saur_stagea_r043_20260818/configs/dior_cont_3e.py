_base_ = '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py'

# User-authorized r043 DIOR-R protocol: fixed trainval -> test endpoint.
train_dataloader = dict(dataset=dict(
    data_root='/home/rspip/cqc/data/dataset/DIOR/',
    ann_file='/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/trainval/',
    data_prefix=dict(img_path='/home/rspip/cqc/data/dataset/DIOR/images/trainval/')))
val_dataloader = dict(dataset=dict(
    data_root='/home/rspip/cqc/data/dataset/DIOR/',
    ann_file='/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test/',
    data_prefix=dict(img_path='/home/rspip/cqc/data/dataset/DIOR/images/test/')))
test_dataloader = val_dataloader
train_cfg = dict(max_epochs=3, val_interval=1, type='EpochBasedTrainLoop')
load_from = '/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth'
work_dir = '/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818/dior_cont'

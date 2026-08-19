"""Frozen DIOR G2 CONT inference export; checkpoint is supplied by test.py."""
_base_ = './dior_cont_seed0_3e.py'

test_evaluator = dict(
    type='mmdet.DumpDetResults',
    out_file_path='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2/raw_predictions/dior_cont_seed0.pkl')


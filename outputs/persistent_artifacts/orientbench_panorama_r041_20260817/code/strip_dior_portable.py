"""Output-local DIOR dataset binding for the frozen Strip-RCNN baseline."""
from pathlib import Path

_frozen = Path('/home/rspip/cqc/pro/study/pth_data/baseline_strip_rcnn_s_fpn_1x_le90/DIOR_trainval_test_naood_seed0_aligned/config.py')
exec(compile(_frozen.read_text(encoding='utf-8'), str(_frozen), 'exec'))
data['test'] = dict(
    type='DIORDataset',
    ann_file='/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test/',
    img_prefix='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/input_views/dior_jpg_aliases/',
    pipeline=test_pipeline,
    version='le90')
del Path, _frozen

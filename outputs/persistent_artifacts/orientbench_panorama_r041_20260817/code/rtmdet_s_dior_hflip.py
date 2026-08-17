from pathlib import Path

_base_ = '/home/rspip/cqc/pro/study/third_party/ai4rs/configs/rotated_rtmdet/rotated_rtmdet_s-3x-dota.py'
_frozen = Path('/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py')
_text = _frozen.read_text(encoding='utf-8').replace("_base_ = '../../../third_party/ai4rs/configs/rotated_rtmdet/rotated_rtmdet_s-3x-dota.py'", '')
exec(compile(_text, str(_frozen), 'exec'))
test_dataloader = dict(dataset=dict(
    data_root='',
    ann_file='/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test/',
    data_prefix=dict(img_path='/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_panorama_r041_20260817/input_views/dior_hflip_png/')))
del Path, _frozen, _text

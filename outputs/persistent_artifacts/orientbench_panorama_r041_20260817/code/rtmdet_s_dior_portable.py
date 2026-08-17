"""Output-local loader for the frozen RTMDet DIOR baseline config.

The transferred config's relative third_party base resolves from pth_data and
is therefore invalid on this server.  Preserve every frozen override verbatim
while binding only its base path to the verified local ai4rs checkout.
"""
from pathlib import Path

_base_ = '/home/rspip/cqc/pro/study/third_party/ai4rs/configs/rotated_rtmdet/rotated_rtmdet_s-3x-dota.py'
_frozen = Path('/home/rspip/cqc/pro/study/pth_data/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py')
_text = _frozen.read_text(encoding='utf-8')
_text = _text.replace("_base_ = '../../../third_party/ai4rs/configs/rotated_rtmdet/rotated_rtmdet_s-3x-dota.py'", '')
exec(compile(_text, str(_frozen), 'exec'))
del Path, _frozen, _text

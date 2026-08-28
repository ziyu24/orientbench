#!/usr/bin/env python3
"""Persist the r052 CMR-to-frozen-host parameter delta."""
from __future__ import annotations
import argparse
import json
from mmdet.apis import init_detector

BASE = '/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py'
CMR = '/home/rspip/cqc/pro/study/orientbench/configs/r052_cmr_admission/dota_orcnn_joint_cmr_smoke_correction.py'

ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
host = init_detector(BASE, None, device='cuda:0')
cmr = init_detector(CMR, None, device='cuda:0')
host_n = sum(p.numel() for p in host.parameters()); cmr_n = sum(p.numel() for p in cmr.parameters())
result = {'baseline_parameters': host_n, 'cmr_parameters': cmr_n,
          'delta_parameters': cmr_n-host_n, 'delta_percent': (cmr_n-host_n)/host_n*100,
          'passed_le_5pct': (cmr_n-host_n)/host_n <= .05}
open(a.out, 'w').write(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))

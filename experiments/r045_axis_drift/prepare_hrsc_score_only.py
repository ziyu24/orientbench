#!/usr/bin/env python3
"""Create r045 HRSC image-only manifests without opening annotations."""
import csv
from pathlib import Path

ROOT=Path('/home/rspip/cqc/pro/study/orientbench')
OUT=ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_hrsc_score_only'
IMAGES=Path('/home/rspip/cqc/data/dataset/HRSC2016/images')

for split in ('D_cal_hrsc_trainval.csv','D_audit_hrsc_trainval.csv'):
    with (ROOT/'outputs/bench_core/splits'/split).open(newline='') as f:
        ids=[r['image_id'] for r in csv.DictReader(f)]
    for image_id in ids:
        if not (IMAGES/f'{image_id}.bmp').is_file():
            raise FileNotFoundError(image_id)
    (OUT/'manifests').mkdir(parents=True,exist_ok=True)
    (OUT/'manifests'/split.replace('.csv','.txt')).write_text('\n'.join(ids)+'\n')
print('wrote score-only manifests; no annotation path was read')

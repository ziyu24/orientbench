#!/usr/bin/env python3
import csv
import os
from pathlib import Path

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
OUT = ROOT / 'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/source_dior_subset'
IMG_SOURCE = ROOT / 'top_journal_v3_reaudit_055/data_prep/DIOR/dotaformat_images/trainval'
ANN_SOURCE = ROOT / 'top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/trainval'

ids = []
for name in ('D_cal_dior_trainval.csv', 'D_audit_dior_trainval.csv'):
    with (ROOT / 'outputs/bench_core/splits' / name).open(newline='') as handle:
        ids.extend(row['image_id'] for row in csv.DictReader(handle))
if len(ids) != 200 or len(set(ids)) != 200:
    raise SystemExit('expected exactly 200 unique frozen DIOR image ids')

for child in ('images', 'annfiles'):
    (OUT / child).mkdir(parents=True, exist_ok=True)
for child in ('source_predictions', 'source_work', 'logs'):
    (OUT.parent / child).mkdir(parents=True, exist_ok=True)
for image_id in sorted(ids):
    pairs = [
        (IMG_SOURCE / f'{image_id}.jpg', OUT / 'images' / f'{image_id}.jpg'),
        (IMG_SOURCE / f'{image_id}.jpg', OUT / 'images' / f'{image_id}.png'),
        (ANN_SOURCE / f'{image_id}.txt', OUT / 'annfiles' / f'{image_id}.txt'),
    ]
    for source, target in pairs:
        if not source.exists():
            raise SystemExit(f'missing source asset: {source}')
        if target.is_symlink():
            if target.resolve() != source.resolve():
                raise SystemExit(f'conflicting symlink: {target}')
        elif target.exists():
            raise SystemExit(f'non-symlink output exists: {target}')
        else:
            os.symlink(source, target)
print(f'prepared {len(ids)} frozen DIOR images at {OUT}')

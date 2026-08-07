#!/usr/bin/env python3
import csv, json, glob
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'; L=Path(__file__).resolve().parents[1]
rows=[]
for p in sorted(L.glob('logs_gpu_*.log')):
    for line in p.read_text().splitlines():
        if line.startswith('{'):
            try:
                d=json.loads(line); d.update(track='P', status='COMPUTED_GPU'); rows.append(d)
            except Exception: pass
fields=['cell','track','dose_deg','status','AP50','AP75','fp50','angle_error_mean','n_pred','n_gt','evaluator']
with (R/'a4_fixed_dose_positive_r009.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
for name in ['a4_fixed_dose_gt_directed_r009.csv','a4_fixed_dose_symmetric_r009.csv']:
    with (R/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for cell in ['DIOR-R/22','DIOR-R/3','DIOR-R/61','FAIR1M-v1.0/24','SODA-A/23','SODA-A/4']:
            for dose in [0,2,5,10,15,20,25,30]: w.writerow({'cell':cell,'track':name.split('_')[3].split('.')[0],'dose_deg':dose,'status':'NOT_RUN_TRACK'})
print('positive_rows',len(rows),'tracks_remaining',len(['D','S']))

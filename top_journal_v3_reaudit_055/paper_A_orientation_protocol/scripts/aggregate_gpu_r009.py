#!/usr/bin/env python3
import csv, json, glob
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'; L=Path(__file__).resolve().parents[1]
rows=[]
for p in sorted(L.glob('logs_gpu_*.log')):
    for line in p.read_text().splitlines():
        if line.startswith('{'):
            try:
                d=json.loads(line); d.setdefault('track','P'); d.update(status='COMPUTED_GPU'); rows.append(d)
            except Exception: pass
fields=['cell','track','dose_deg','status','AP50','AP75','fp50','angle_error_mean','n_pred','n_gt','evaluator']
dedup={ (d['cell'],d['track'],int(d['dose_deg'])):d for d in rows }
rows=list(dedup.values())
for name,track in [('a4_fixed_dose_positive_r009.csv','P'),('a4_fixed_dose_gt_directed_r009.csv','D'),('a4_fixed_dose_symmetric_r009.csv','S')]:
    with (R/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for d in sorted(rows,key=lambda x:(x['cell'],x['track'],int(x['dose_deg']))):
            if d['track']==track: w.writerow({k:d.get(k,'') for k in fields})
print('computed_rows',len(rows))

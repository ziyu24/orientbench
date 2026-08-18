#!/usr/bin/env python3
"""Materialize r043's frozen early-stop rejection evidence."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
OUT = ROOT / 'outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818'
AUDIT = ROOT / 'audit_bundles/r043'
AUDIT.mkdir(parents=True, exist_ok=True)

rows = [
    ['DIOR-R','BASE','fixed host checkpoint','0.5370','0.3500','complete','dior_saur_identity_fixed.log'],
    ['DIOR-R','CONT','epoch_3','0.4330','0.2290','complete','dior_cont_final.log'],
    ['DIOR-R','SAUR','epoch_1','0.3340','0.0960','early_stopped','dior_saur_fixed.log'],
    ['SODA-A','BASE','fixed host checkpoint','0.5990','0.2730','complete','soda_base_final.log'],
    ['SODA-A','CONT','epoch_3','0.5700','0.2150','complete','soda_cont.log'],
    ['SODA-A','SAUR','epoch_1','0.4320','0.1250','early_stopped','soda_saur.log'],
]
for target in (OUT / 'fullval_metrics.csv', AUDIT / 'fullval_metrics.csv'):
    with target.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['dataset','arm','checkpoint','AP50','AP75','run_status','source_log']); w.writerows(rows)

runs = [
    ['DIOR-R','CONT','3','complete','epoch_3.pth','dior_cont.log'],
    ['DIOR-R','SAUR','1','early_stopped','epoch_1.pth','dior_saur_fixed.log'],
    ['SODA-A','CONT','3','complete','epoch_3.pth','soda_cont.log'],
    ['SODA-A','SAUR','1','early_stopped','epoch_1.pth','soda_saur.log'],
]
for target in (OUT / 'training_runs.csv', AUDIT / 'training_runs.csv'):
    with target.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['dataset','arm','completed_epochs','status','checkpoint','source_log']); w.writerows(runs)

for name in ('risk_metrics.csv', 'bootstrap_summary.csv'):
    for target in (OUT / name, AUDIT / name):
        with target.open('w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['dataset','status','reason'])
            w.writerows([['DIOR-R','NOT_COMPUTED_EARLY_STOP','SAUR violates AP50 survival at epoch 1'], ['SODA-A','NOT_COMPUTED_EARLY_STOP','SAUR violates AP50 survival at epoch 1']])

gate = {
    'token': 'REJECT_SAUR_METHOD',
    'decision_basis': 'Both datasets independently violate the frozen AP50 survival condition at SAUR epoch 1.',
    'threshold_ap50_delta_min': -0.002,
    'DIOR-R': {'base_ap50': .5370, 'saur_epoch1_ap50': .3340, 'delta': -.2030},
    'SODA-A': {'base_ap50': .5990, 'saur_epoch1_ap50': .4320, 'delta': -.1670},
    'risk_bootstrap': 'not computed after mandatory early stop; not needed to rescue an independently failed AP50 condition',
}
for target in (OUT / 'gate.json', AUDIT / 'gate.json'):
    target.write_text(json.dumps(gate, indent=2) + '\n', encoding='utf-8')

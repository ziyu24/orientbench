#!/usr/bin/env python3
"""Frozen point-estimate adjudication for r049 DIOR G2 seed0.

This script has no tuning inputs.  It reads the final evaluation line from
each completed FP32 arm and the precomputed AR>=2.1 matched-TP metrics, then
applies the dispatch inequalities verbatim.  A DIOR failure is terminal for
r049 (SODA and extra seeds must not start).
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
G2 = ROOT / 'outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2'
ARMS = {'CONT': 'dior_cont_seed0_fp32', 'VM_NLL': 'dior_vm_nll_seed0_fp32', 'CORA': 'dior_cora_seed0_fp32'}
AP_RE = re.compile(r'dota/mAP: ([0-9.]+)\s+dota/AP50: ([0-9.]+)\s+dota/AP75: ([0-9.]+)')


def final_ap(path: Path) -> dict:
    matches = AP_RE.findall(path.read_text(errors='replace'))
    if not matches:
        raise RuntimeError(f'no completed AP result in {path}')
    _, ap50, ap75 = matches[-1]
    return {'AP50': float(ap50), 'AP75': float(ap75), 'log': str(path.relative_to(ROOT))}


def main() -> None:
    metrics_path = G2 / 'metrics/risk_metrics.csv'
    if not metrics_path.is_file():
        raise RuntimeError(f'missing {metrics_path}')
    ap = {arm: final_ap(G2 / directory / 'train.log') for arm, directory in ARMS.items()}
    metrics = list(csv.DictReader(metrics_path.open()))
    by_arm = {r['arm']: r for r in metrics if r['scope'] == 'ar_ge_2_1'}
    if set(by_arm) != set(ARMS):
        raise RuntimeError(f'AR>=2.1 metrics incomplete: {sorted(by_arm)}')
    for row in by_arm.values():
        for key in ('AUGRC', 'Risk_at_70', 'mean_angle_error_deg'):
            row[key] = float(row[key])
    control = ('CONT', 'VM_NLL')
    strongest_ap = {key: max(ap[a][key] for a in control) for key in ('AP50', 'AP75')}
    best_augrc = min(by_arm[a]['AUGRC'] for a in control)
    best_risk70 = min(by_arm[a]['Risk_at_70'] for a in control)
    lowest_mean_error = min(by_arm[a]['mean_angle_error_deg'] for a in control)
    cora = by_arm['CORA']
    checks = {
        'AP50_delta_ge_minus_0_005': ap['CORA']['AP50'] - strongest_ap['AP50'] >= -.005,
        'AP75_delta_ge_minus_0_005': ap['CORA']['AP75'] - strongest_ap['AP75'] >= -.005,
        'AUGRC_reduction_ge_0_01': best_augrc - cora['AUGRC'] >= .01,
        'Risk_at_70_reduction_ge_0_02': best_risk70 - cora['Risk_at_70'] >= .02,
        'mean_angle_error_increase_le_1_deg': cora['mean_angle_error_deg'] - lowest_mean_error <= 1.,
    }
    outcome = 'PASS_DIOR_G2' if all(checks.values()) else 'REJECT_CORA_METHOD'
    payload = {
        'dispatch_id': 'orientbench-b-r049-cora-obb-native-risk-stagea-20260819',
        'gate': 'G2_SEED0_TWO_DATASET_SURVIVAL', 'dataset': 'DIOR-R', 'scope': 'AR>=2.1 matched TP',
        'status': outcome, 'checks': checks, 'ap': ap, 'risk_metrics': by_arm,
        'contrasts': {
            'CORA_minus_strongest_AP50': ap['CORA']['AP50'] - strongest_ap['AP50'],
            'CORA_minus_strongest_AP75': ap['CORA']['AP75'] - strongest_ap['AP75'],
            'best_control_minus_CORA_AUGRC': best_augrc - cora['AUGRC'],
            'best_control_minus_CORA_Risk_at_70': best_risk70 - cora['Risk_at_70'],
            'CORA_minus_lowest_control_mean_angle_error_deg': cora['mean_angle_error_deg'] - lowest_mean_error,
        },
        'next_step': ('run SODA-A seed0 only if PASS_DIOR_G2; otherwise stop r049 as REJECT_CORA_METHOD'),
        'no_target_gt_calibration_or_threshold_selection': True,
    }
    target = G2 / 'metrics/gate_dior_seed0.json'
    target.write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps({'status': outcome, 'gate_path': str(target)}, indent=2))


if __name__ == '__main__':
    main()

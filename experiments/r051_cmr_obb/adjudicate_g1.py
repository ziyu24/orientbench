#!/usr/bin/env python3
"""Apply the immutable r051 G1 cheap-signal conjunction."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ARMS = ('CMR', 'DIRECT_DIST', 'SINGLE_ROI_QUALITY')
DIRS = {'CMR': 'dota_orcnn_cmr_frozenhost_3ep',
        'DIRECT_DIST': 'dota_orcnn_direct_dist_frozenhost_3ep',
        'SINGLE_ROI_QUALITY': 'dota_orcnn_single_roi_quality_frozenhost_3ep'}
AP_RE = re.compile(r'dota/mAP: ([0-9.]+)\s+dota/AP50: ([0-9.]+)\s+dota/AP75: ([0-9.]+)')


def final_ap(path: Path) -> dict:
    matches = AP_RE.findall(path.read_text(errors='replace'))
    if not matches:
        raise RuntimeError(f'missing AP50/AP75 final validation line: {path}')
    m = matches[-1]
    return {'mAP_mean_AP50_AP75': float(m[0]), 'AP50': float(m[1]), 'AP75': float(m[2]), 'log': str(path)}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument('--base', type=Path, required=True)
    args = parser.parse_args(); base = args.base
    ap = {arm: final_ap(base / DIRS[arm] / 'train.log') for arm in ARMS}
    rows = list(csv.DictReader((base / 'metrics' / 'risk_metrics.csv').open()))
    metric = {r['arm']: r for r in rows if r['scope'] == 'ar_ge_2_1'}
    if set(metric) != set(ARMS): raise RuntimeError('incomplete AR>=2.1 risk metrics')
    for row in metric.values():
        for key in ('AUGRC', 'Risk_at_70', 'mean_angle_error_deg'):
            row[key] = float(row[key])
    strongest = max(('DIRECT_DIST', 'SINGLE_ROI_QUALITY'),
                    key=lambda arm: (ap[arm]['AP50'], ap[arm]['AP75'], arm))
    cmr, control = metric['CMR'], metric[strongest]
    manifest = json.loads((base / 'metrics' / 'manifest.json').read_text())
    bootstrap = manifest['bootstrap_by_control'][strongest]
    aug_rel = (control['AUGRC'] - cmr['AUGRC']) / control['AUGRC'] if control['AUGRC'] else float('-inf')
    r70_rel = (control['Risk_at_70'] - cmr['Risk_at_70']) / control['Risk_at_70'] if control['Risk_at_70'] else float('-inf')
    err_rel = ((control['mean_angle_error_deg'] - cmr['mean_angle_error_deg']) / control['mean_angle_error_deg']
               if control['mean_angle_error_deg'] else float('-inf'))
    checks = {
        'AP50_delta_ge_minus_0_003': ap['CMR']['AP50'] - ap[strongest]['AP50'] >= -.003,
        'AP75_gain_ge_0_005': ap['CMR']['AP75'] - ap[strongest]['AP75'] >= .005,
        'AR_ge_2_1_angle_error_relative_reduction_ge_5pct': err_rel >= .05,
        'native_risk_AUGRC_relative_reduction_ge_10pct': aug_rel >= .10,
        'native_risk_Risk_at_70_relative_reduction_ge_10pct': r70_rel >= .10,
        'mother_image_bootstrap_AUGRC_ci_low_gt_0': bootstrap['AUGRC_improvement_ci95'][0] > 0,
        'mother_image_bootstrap_Risk_at_70_ci_low_gt_0': bootstrap['Risk_at_70_improvement_ci95'][0] > 0,
    }
    status = 'PASS_G1_PROCEED_G2' if all(checks.values()) else 'REJECT_CMR_CHEAP_SIGNAL'
    result = {'dispatch_id': 'orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822',
              'gate': 'G1_EXACT_PROPOSAL_CYCLIC_EVIDENCE_AND_CHEAP_SIGNAL', 'status': status,
              'scope': 'DOTA-v1.0 train->val; matched TP GT AR>=2.1', 'strongest_control': strongest,
              'ap': ap, 'risk_metrics': metric,
              'relative_improvements': {'AUGRC': aug_rel, 'Risk_at_70': r70_rel, 'mean_angle_error': err_rel},
              'bootstrap': bootstrap, 'checks': checks,
              'next_step': 'G2 only if PASS_G1_PROCEED_G2; otherwise stop all full-detector and expansion work.',
              'prohibited_endpoints_touched': False}
    out = base / 'metrics' / 'g1_gate.json'; out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': status, 'gate': str(out)}, indent=2))


if __name__ == '__main__':
    main()

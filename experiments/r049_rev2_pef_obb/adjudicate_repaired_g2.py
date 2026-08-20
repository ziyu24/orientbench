#!/usr/bin/env python3
"""Apply the r049-rev2 frozen DOTA/PSC G2 conjunction without tuning."""
from __future__ import annotations
import argparse, csv, json, re
from pathlib import Path

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
DIRS = {'CONT': 'dota_psc_cont', 'DIRECT_DIST': 'dota_psc_direct_dist', 'SCALAR_QUALITY': 'dota_psc_scalar_quality', 'PEF': 'dota_psc_pef'}
AP_RE = re.compile(r'dota/mAP: ([0-9.]+)\s+dota/AP50: ([0-9.]+)\s+dota/AP75: ([0-9.]+)')

def final_ap(path: Path) -> dict:
    m = AP_RE.findall(path.read_text(errors='replace'))
    if not m: raise RuntimeError(f'missing final AP in {path}')
    x = m[-1]; return {'mAP': float(x[0]), 'AP50': float(x[1]), 'AP75': float(x[2]), 'log': str(path.relative_to(ROOT))}

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument('--base', type=Path, required=True); a = p.parse_args()
    ap = {arm: final_ap(a.base / 'evaluation' / directory / 'test.log') for arm, directory in DIRS.items()}
    rows = list(csv.DictReader((a.base / 'metrics/risk_metrics.csv').open()))
    metric = {r['arm']: r for r in rows if r['scope'] == 'ar_ge_2_1'}
    if set(metric) != set(DIRS): raise RuntimeError('incomplete AR>=2.1 metrics')
    for r in metric.values():
        for k in ('AUGRC', 'Risk_at_70', 'mean_angle_error_deg'): r[k] = float(r[k])
    controls = ('CONT', 'DIRECT_DIST', 'SCALAR_QUALITY')
    strongest = max(controls, key=lambda arm: (ap[arm]['mAP'], ap[arm]['AP50'], ap[arm]['AP75'], arm))
    pef, ctl = metric['PEF'], metric[strongest]
    manifest = json.loads((a.base / 'metrics/manifest.json').read_text())
    boot = manifest['bootstrap_by_control'][strongest]
    aug_rel = (ctl['AUGRC'] - pef['AUGRC']) / ctl['AUGRC'] if ctl['AUGRC'] else float('-inf')
    r70_rel = (ctl['Risk_at_70'] - pef['Risk_at_70']) / ctl['Risk_at_70'] if ctl['Risk_at_70'] else float('-inf')
    err_rel = (ctl['mean_angle_error_deg'] - pef['mean_angle_error_deg']) / ctl['mean_angle_error_deg'] if ctl['mean_angle_error_deg'] else float('-inf')
    checks = {
        'mAP_delta_ge_minus_0_003': pef and ap['PEF']['mAP'] - ap[strongest]['mAP'] >= -.003,
        'AP50_delta_ge_minus_0_003': ap['PEF']['AP50'] - ap[strongest]['AP50'] >= -.003,
        'AP75_gain_ge_0_010': ap['PEF']['AP75'] - ap[strongest]['AP75'] >= .010,
        'AR_ge_2_1_mean_angle_error_relative_reduction_ge_10pct': err_rel >= .10,
        'native_risk_AUGRC_relative_reduction_ge_15pct': aug_rel >= .15,
        'native_risk_Risk_at_70_relative_reduction_ge_15pct': r70_rel >= .15,
        'mother_image_bootstrap_AUGRC_ci_low_gt_0': boot['AUGRC_improvement_ci95'][0] > 0,
        'mother_image_bootstrap_Risk_at_70_ci_low_gt_0': boot['Risk_at_70_improvement_ci95'][0] > 0,
    }
    status = 'PASS_G2_PROCEED_G3' if all(checks.values()) else 'REJECT_PEF_METHOD'
    result = {'dispatch_id': 'orientbench-b-r049-rev2-pef-multidata-multihost-20260819', 'gate': 'G2_DOTA_PSC_FULL_TRAIN_PRIMARY', 'status': status, 'scope': 'DOTA-v1.0 train->val, AR>=2.1 matched TP for angle/risk', 'strongest_control': strongest, 'ap': ap, 'risk_metrics': metric, 'relative_improvements': {'AUGRC': aug_rel, 'Risk_at_70': r70_rel, 'mean_angle_error': err_rel}, 'bootstrap': boot, 'checks': checks, 'next_step': 'Run G3 only if PASS_G2_PROCEED_G3; otherwise stop all expansion.', 'prohibited_endpoints_touched': False}
    (a.base / 'metrics/gate_dota_psc_repaired.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': status, 'gate': str(a.base / 'metrics/gate_dota_psc_repaired.json')}, indent=2))

if __name__ == '__main__': main()

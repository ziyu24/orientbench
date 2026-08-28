#!/usr/bin/env python3
"""Numerically adjudicate the persisted dynamic r052 G1 rank outputs."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def fraction(rows, key, threshold=1e-6):
    return sum(float(x[key]) > threshold for x in rows) / len(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--dynamic-dir', type=Path, required=True)
    p.add_argument('--mutation', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    rows = []
    for f in sorted(a.dynamic_dir.glob('rank[0-9].json')):
        rows.extend(json.loads(f.read_text()))
    if len(rows) != 1024 or len({x['proposal_uid'] for x in rows}) != 1024:
        raise RuntimeError('dynamic G1 did not execute exactly the frozen 1024 UID universe')
    mutation = json.loads(a.mutation.read_text())
    med = lambda key: float(statistics.median(float(x[key]) for x in rows))
    same_loss = max(abs(x['normal_loss'] - x['detached_loss']) for x in rows) <= 1e-6
    checks = {
        'direct_gradient_95pct': fraction(rows, 'direct_grad') >= .95,
        'direct_permutation_median_l1_gt_005': med('direct_l1') > .05,
        'candidate_variance_95pct': fraction(rows, 'candidate_var') >= .95,
        'cyclic_aligned_median_l1_le_005': med('cyclic_l1') <= .05,
        'geometry_relative_q_median_l1_le_005': med('geometry_q_l1') <= .05,
        'geometry_theta_median_delta_le_005': med('geometry_theta') <= .05,
        'class_gradient_95pct': fraction(rows, 'cls_grad') >= .95,
        'box_gradient_95pct': fraction(rows, 'box_grad') >= .95,
        'theta_gradient_95pct': fraction(rows, 'theta_grad') >= .95,
        'detach_forward_equal': same_loss,
        'normal_evidence_gradient': min(float(x['normal_evidence_grad']) for x in rows) > 1e-6,
        'detach_evidence_gradient': max(float(x['detached_evidence_grad']) for x in rows) <= 1e-12,
        'shuffle_loss_95pct': fraction(rows, 'shuffle_loss') >= .95,
        'shuffle_class_95pct': fraction(rows, 'shuffle_class') >= .95,
        'shuffle_box_95pct': fraction(rows, 'shuffle_box') >= .95,
        'finite_all': all(x['finite'] for x in rows),
        'candidate_scorer_gradient': min(float(x['normal_evidence_grad']) for x in rows) > 1e-6,
        'four_box_component_gradients': all(min(float(v) for v in x['box_component_grads']) > 1e-6 for x in rows),
        'all_uid_mutations_rejected': bool(mutation.get('passed')) and all(v.get('rejected') for v in mutation.get('mutations', {}).values()),
    }
    metrics = {k: med(k) for k in ('direct_l1', 'candidate_var', 'cyclic_l1', 'geometry_q_l1', 'geometry_theta', 'shuffle_loss', 'shuffle_class', 'shuffle_box')}
    metrics.update({f'{k}_fraction': fraction(rows, k) for k in ('direct_grad', 'cls_grad', 'box_grad', 'theta_grad')})
    result = dict(schema_version=1, frozen_count=len(rows), checks=checks,
                  metrics=metrics, passed=all(checks.values()))
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

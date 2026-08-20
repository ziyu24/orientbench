#!/usr/bin/env python3
"""Frozen DOTA/PSC G2 metrics for the repaired per-candidate PEF run.

This consumes final-epoch raw exports only.  Matching is class-aware, greedy
by detector score and one-to-one at rotated IoU >= .5.  The PEF ranker is
strictly ``-pef_native_risk``; controls retain only their detector score.  No
validation-derived calibration, threshold or score fusion is performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pickle
from pathlib import Path

import numpy as np
import torch
from mmcv.ops import box_iou_rotated

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
BASE = ROOT / 'outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_repaired_percandidate'
AR_CUTOFF = 2.1
ARMS = ('CONT', 'DIRECT_DIST', 'SCALAR_QUALITY', 'PEF')
DIRS = {'CONT': 'dota_psc_cont', 'DIRECT_DIST': 'dota_psc_direct_dist',
        'SCALAR_QUALITY': 'dota_psc_scalar_quality', 'PEF': 'dota_psc_pef'}


def tensor(value) -> torch.Tensor:
    return (value.tensor if hasattr(value, 'tensor') else value).detach().cpu().float()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def axial_error_deg(pred: np.ndarray, gt: np.ndarray) -> float:
    def heading(box: np.ndarray) -> float:
        angle = math.degrees(float(box[4]))
        if float(box[3]) > float(box[2]):
            angle += 90.
        return angle % 180.
    d = abs((heading(pred) - heading(gt)) % 180.)
    return min(d, 180. - d)


def mother_id(image_id: str) -> str:
    """DOTA split patch IDs retain their mother image before the first '__'."""
    return image_id.split('__', 1)[0]


def match_record(rec: dict, arm: str) -> list[dict]:
    pi, gi = rec['pred_instances'], rec['gt_instances']
    pb, ps, pl = tensor(pi['bboxes']).numpy(), tensor(pi['scores']).numpy(), tensor(pi['labels']).long().numpy()
    gb, gl = tensor(gi['bboxes']).numpy(), tensor(gi['labels']).long().numpy()
    native = None
    if arm == 'PEF':
        if 'pef_native_risk' not in pi or 'pef_q' not in pi:
            raise RuntimeError(f'PEF/{rec["img_id"]}: q/native risk missing')
        native = tensor(pi['pef_native_risk']).numpy()
        q = tensor(pi['pef_q']).numpy()
        if native.shape != ps.shape or q.shape != (len(ps), 12) or not np.isfinite(native).all():
            raise RuntimeError(f'PEF/{rec["img_id"]}: invalid q/native risk schema')
    if not len(pb) or not len(gb):
        return []
    overlaps = box_iou_rotated(torch.from_numpy(pb), torch.from_numpy(gb)).numpy()
    used: set[int] = set(); rows: list[dict] = []
    for pred_id in sorted(range(len(pb)), key=lambda i: (-float(ps[i]), i)):
        candidates = [gt_id for gt_id in range(len(gb)) if gt_id not in used
                      and int(pl[pred_id]) == int(gl[gt_id]) and float(overlaps[pred_id, gt_id]) >= .5]
        if not candidates:
            continue
        gt_id = min(candidates, key=lambda i: (-float(overlaps[pred_id, i]), i)); used.add(gt_id)
        pred, gt = pb[pred_id], gb[gt_id]
        ar = max(float(gt[2]), float(gt[3])) / max(min(float(gt[2]), float(gt[3])), 1e-6)
        err = axial_error_deg(pred, gt)
        risk = None if native is None else float(native[pred_id])
        row = dict(arm=arm, image_id=str(rec['img_id']), mother_image_id=mother_id(str(rec['img_id'])),
                   pred_id=int(pred_id), gt_id=int(gt_id), class_id=int(pl[pred_id]), match_iou=float(overlaps[pred_id, gt_id]),
                   gt_aspect_ratio=ar, gt_size=float(gt[2] * gt[3]), angle_error_deg=err,
                   orientation_harm=min(err / 90., 1.), detector_score=float(ps[pred_id]), native_risk=risk,
                   selection_score=-risk if risk is not None else float(ps[pred_id]))
        if arm == 'PEF':
            row['q'] = [float(x) for x in q[pred_id]]
            row['original_angle'] = float(tensor(pi['pef_original_angle'])[pred_id])
            row['refined_angle'] = float(tensor(pi['pef_refined_angle'])[pred_id])
        rows.append(row)
    return rows


def risk_metrics(rows: list[dict]) -> tuple[float, float, float]:
    score = np.asarray([r['selection_score'] for r in rows], float)
    harm = np.asarray([r['orientation_harm'] for r in rows], float)
    order = np.argsort(-score, kind='stable'); score, harm = score[order], harm[order]
    starts = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    count = np.diff(np.r_[starts, len(score)]).astype(float); summed = np.add.reduceat(harm, starts)
    cc, cr = np.cumsum(count), np.cumsum(summed); total = float(len(score))
    augrc = float(np.sum((np.r_[0., cr[:-1] / total] + cr / total) * (count / total) / 2.))
    i = int(np.searchsorted(cc, .70 * total))
    return augrc, float(cr[i] / cc[i]), float(np.mean(np.asarray([r['angle_error_deg'] for r in rows], float)))


def bootstrap_improvement(control: list[dict], pef: list[dict], reps: int, seed: int) -> dict:
    by_c, by_p = {}, {}
    for r in control: by_c.setdefault(r['mother_image_id'], []).append(r)
    for r in pef: by_p.setdefault(r['mother_image_id'], []).append(r)
    mothers = sorted(set(by_c) & set(by_p))
    if len(mothers) < 2: raise RuntimeError('insufficient common mother images for bootstrap')
    rng = np.random.default_rng(seed); aug, r70 = [], []
    for _ in range(reps):
        chosen = rng.choice(mothers, size=len(mothers), replace=True)
        c = [row for m in chosen for row in by_c[m]]; p = [row for m in chosen for row in by_p[m]]
        if not c or not p: continue
        ca, cr, _ = risk_metrics(c); pa, pr, _ = risk_metrics(p)
        aug.append(ca - pa); r70.append(cr - pr)
    if not aug: raise RuntimeError('bootstrap produced no usable resamples')
    return {'replicates': len(aug), 'mother_images_common': len(mothers),
            'AUGRC_improvement_ci95': [float(np.quantile(aug, .025)), float(np.quantile(aug, .975))],
            'Risk_at_70_improvement_ci95': [float(np.quantile(r70, .025)), float(np.quantile(r70, .975))]}


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, default=BASE / 'metrics'); ap.add_argument('--bootstrap-reps', type=int, default=1000); args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True); all_rows, manifest = [], {}
    for arm in ARMS:
        path = BASE / 'evaluation' / DIRS[arm] / 'predictions.pkl'
        if not path.is_file(): raise RuntimeError(f'missing export: {path}')
        records = pickle.load(path.open('rb'))
        rows = [row for rec in records for row in match_record(rec, arm)]
        if not rows: raise RuntimeError(f'{arm}: zero matched true positives')
        all_rows.extend(rows); manifest[arm] = {'path': str(path.relative_to(ROOT)), 'sha256': sha256(path), 'images': len(records), 'matched_rows': len(rows)}
    rows_path = args.out / 'matched_tp_rows.jsonl'
    with rows_path.open('w') as f:
        for row in all_rows: f.write(json.dumps(row, separators=(',', ':')) + '\n')
    metric_rows = []
    for arm in ARMS:
        arm_rows = [r for r in all_rows if r['arm'] == arm]
        for scope, rows in [('all_ar', arm_rows), ('ar_ge_2_1', [r for r in arm_rows if r['gt_aspect_ratio'] >= AR_CUTOFF])]:
            if not rows: raise RuntimeError(f'{arm}/{scope}: zero matched rows')
            augrc, r70, mae = risk_metrics(rows)
            metric_rows.append({'arm': arm, 'scope': scope, 'rows': len(rows), 'mother_images': len({r['mother_image_id'] for r in rows}), 'AUGRC': augrc, 'Risk_at_70': r70, 'mean_angle_error_deg': mae, 'ranker': 'negative_pef_native_risk' if arm == 'PEF' else 'detection_score'})
    metric_path = args.out / 'risk_metrics.csv'
    with metric_path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(metric_rows[0])); w.writeheader(); w.writerows(metric_rows)
    ar = {arm: [x for x in all_rows if x['arm'] == arm and x['gt_aspect_ratio'] >= AR_CUTOFF] for arm in ARMS}
    bootstraps = {arm: bootstrap_improvement(ar[arm], ar['PEF'], args.bootstrap_reps, 20260819)
                  for arm in ('CONT', 'DIRECT_DIST', 'SCALAR_QUALITY')}
    payload = {'schema_version': 1, 'dataset': 'DOTA-v1.0', 'split': 'val', 'scope': 'matched TP, GT AR>=2.1', 'matching': 'class-aware score-ordered rotated IoU >= 0.5 one-to-one', 'orientation_harm': 'min(axial long-side angle error degrees / 90, 1)', 'rankers': {'PEF': '-native risk only', 'controls': 'detector score only'}, 'raw_exports': manifest, 'matched_rows_sha256': sha256(rows_path), 'metrics_sha256': sha256(metric_path), 'bootstrap_by_control': bootstraps, 'no_target_gt_calibration_or_threshold_selection': True, 'can_recompute': True}
    (args.out / 'manifest.json').write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps({'status': 'complete', 'matched_rows': len(all_rows), 'metrics': str(metric_path)}, indent=2))


if __name__ == '__main__': main()

#!/usr/bin/env python3
"""Frozen r051 G1 matched-TP risk and angle metrics.

Consumes only persisted final-epoch exports.  It uses class-aware greedy
rotated-IoU matching and evaluates all three arms with their own no-GT native
risk; no validation calibration, score fusion or threshold selection occurs.
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
AR_CUTOFF = 2.1
ARMS = ('CMR', 'DIRECT_DIST', 'SINGLE_ROI_QUALITY')
DIRS = {'CMR': 'dota_orcnn_cmr_frozenhost_3ep',
        'DIRECT_DIST': 'dota_orcnn_direct_dist_frozenhost_3ep',
        'SINGLE_ROI_QUALITY': 'dota_orcnn_single_roi_quality_frozenhost_3ep'}


def value(obj, key):
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def tensor(x):
    return (x.tensor if hasattr(x, 'tensor') else x).detach().cpu().float()


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
    delta = abs((heading(pred) - heading(gt)) % 180.)
    return min(delta, 180. - delta)


def mother_id(image_id: str) -> str:
    return image_id.split('__', 1)[0]


def match_record(record, arm: str) -> list[dict]:
    pred, gt = value(record, 'pred_instances'), value(record, 'gt_instances')
    boxes, scores = tensor(value(pred, 'bboxes')).numpy(), tensor(value(pred, 'scores')).numpy()
    labels = tensor(value(pred, 'labels')).long().numpy()
    gt_boxes, gt_labels = tensor(value(gt, 'bboxes')).numpy(), tensor(value(gt, 'labels')).long().numpy()
    risk = tensor(value(pred, 'cmr_native_risk')).numpy()
    if risk.shape != scores.shape or not np.isfinite(risk).all():
        raise RuntimeError(f'{arm}/{value(record, "img_id")}: invalid native risk')
    if arm == 'CMR':
        q = tensor(value(pred, 'cmr_q')).numpy()
        if q.shape != (len(scores), 12) or not np.allclose(q.sum(-1), 1., atol=1e-5):
            raise RuntimeError(f'{arm}/{value(record, "img_id")}: invalid posterior')
    if not len(boxes) or not len(gt_boxes):
        return []
    ious = box_iou_rotated(torch.from_numpy(boxes), torch.from_numpy(gt_boxes)).numpy()
    used, rows = set(), []
    for pred_id in sorted(range(len(boxes)), key=lambda i: (-float(scores[i]), i)):
        candidates = [gt_id for gt_id in range(len(gt_boxes)) if gt_id not in used
                      and labels[pred_id] == gt_labels[gt_id] and ious[pred_id, gt_id] >= .5]
        if not candidates:
            continue
        gt_id = min(candidates, key=lambda i: (-float(ious[pred_id, i]), i)); used.add(gt_id)
        g = gt_boxes[gt_id]
        aspect = max(float(g[2]), float(g[3])) / max(min(float(g[2]), float(g[3])), 1e-6)
        error = axial_error_deg(boxes[pred_id], g)
        image_id = str(value(record, 'img_id'))
        rows.append(dict(arm=arm, image_id=image_id, mother_image_id=mother_id(image_id),
                         pred_id=pred_id, gt_id=gt_id, class_id=int(labels[pred_id]),
                         match_iou=float(ious[pred_id, gt_id]), gt_aspect_ratio=aspect,
                         angle_error_deg=error, orientation_harm=min(error / 90., 1.),
                         detector_score=float(scores[pred_id]), native_risk=float(risk[pred_id]),
                         selection_score=-float(risk[pred_id])))
    return rows


def risk_metrics(rows: list[dict]) -> tuple[float, float, float]:
    score = np.asarray([row['selection_score'] for row in rows])
    harm = np.asarray([row['orientation_harm'] for row in rows])
    order = np.argsort(-score, kind='stable'); score, harm = score[order], harm[order]
    starts = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    count = np.diff(np.r_[starts, len(score)]).astype(float); summed = np.add.reduceat(harm, starts)
    covered, cumulative = np.cumsum(count), np.cumsum(summed); total = float(len(score))
    augrc = float(np.sum((np.r_[0., cumulative[:-1] / total] + cumulative / total) * count / total / 2.))
    index = int(np.searchsorted(covered, .70 * total))
    return augrc, float(cumulative[index] / covered[index]), float(harm.mean() * 90.)


def bootstrap(control: list[dict], cmr: list[dict], reps: int, seed: int) -> dict:
    by_control, by_cmr = {}, {}
    for row in control: by_control.setdefault(row['mother_image_id'], []).append(row)
    for row in cmr: by_cmr.setdefault(row['mother_image_id'], []).append(row)
    mothers = sorted(set(by_control) & set(by_cmr))
    if len(mothers) < 2:
        raise RuntimeError('insufficient common mother images for bootstrap')
    rng = np.random.default_rng(seed); aug, r70 = [], []
    for _ in range(reps):
        sampled = rng.choice(mothers, size=len(mothers), replace=True)
        c = [row for m in sampled for row in by_control[m]]
        t = [row for m in sampled for row in by_cmr[m]]
        ca, cr, _ = risk_metrics(c); ta, tr, _ = risk_metrics(t)
        aug.append(ca - ta); r70.append(cr - tr)
    return {'replicates': reps, 'mother_images_common': len(mothers),
            'AUGRC_improvement_ci95': [float(np.quantile(aug, .025)), float(np.quantile(aug, .975))],
            'Risk_at_70_improvement_ci95': [float(np.quantile(r70, .025)), float(np.quantile(r70, .975))]}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path); parser.add_argument('--bootstrap-reps', type=int, default=1000)
    args = parser.parse_args(); out = args.out or args.base / 'metrics'; out.mkdir(parents=True, exist_ok=True)
    all_rows, raw = [], {}
    for arm in ARMS:
        path = args.base / DIRS[arm] / 'evaluation' / 'predictions.pkl'
        if not path.is_file(): raise RuntimeError(f'missing export: {path}')
        records = pickle.load(path.open('rb'))
        rows = [row for record in records for row in match_record(record, arm)]
        if not rows: raise RuntimeError(f'{arm}: zero matched true positives')
        all_rows.extend(rows); raw[arm] = {'path': str(path.relative_to(ROOT)), 'sha256': sha256(path), 'images': len(records), 'matched_rows': len(rows)}
    row_path = out / 'matched_tp_rows.jsonl'
    with row_path.open('w') as f:
        for row in all_rows: f.write(json.dumps(row, separators=(',', ':')) + '\n')
    metrics = []
    for arm in ARMS:
        arm_rows = [r for r in all_rows if r['arm'] == arm]
        for scope, rows in (('all_ar', arm_rows), ('ar_ge_2_1', [r for r in arm_rows if r['gt_aspect_ratio'] >= AR_CUTOFF])):
            if not rows: raise RuntimeError(f'{arm}/{scope}: zero matched rows')
            augrc, r70, mae = risk_metrics(rows)
            metrics.append(dict(arm=arm, scope=scope, rows=len(rows), mother_images=len({r['mother_image_id'] for r in rows}),
                                AUGRC=augrc, Risk_at_70=r70, mean_angle_error_deg=mae, ranker='negative_native_risk_only'))
    metric_path = out / 'risk_metrics.csv'
    with metric_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics[0])); writer.writeheader(); writer.writerows(metrics)
    ar = {arm: [r for r in all_rows if r['arm'] == arm and r['gt_aspect_ratio'] >= AR_CUTOFF] for arm in ARMS}
    manifest = dict(schema_version=1, dataset='DOTA-v1.0', split='val', scope='matched TP, GT AR>=2.1',
                    matching='class-aware score-ordered rotated IoU >= 0.5 one-to-one',
                    ranker='negative no-GT native risk only for every arm', raw_exports=raw,
                    matched_rows_sha256=sha256(row_path), metrics_sha256=sha256(metric_path),
                    bootstrap_by_control={arm: bootstrap(ar[arm], ar['CMR'], args.bootstrap_reps, 20260822)
                                          for arm in ('DIRECT_DIST', 'SINGLE_ROI_QUALITY')},
                    no_target_gt_calibration_or_threshold_selection=True, can_recompute=True)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': 'complete', 'matched_rows': len(all_rows), 'out': str(out)}, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Build the frozen DIOR seed-0 G2 matched-TP evidence from DumpDetResults.

All three inference exports retain the evaluated sample's GT instances.  This
script therefore performs one identical, score-ordered, class-aware rotated-IoU
matching pass per arm, then computes risk-coverage metrics without fitting any
target-domain parameter.  CONT is ranked only by detection score; VM-NLL and
CORA are ranked only by their exported native risk (lower risk is retained
first).  It is intentionally unusable until all three raw exports exist.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pickle
from pathlib import Path
from functools import lru_cache

import numpy as np
import torch
from mmcv.ops import box_iou_rotated
from mmrotate.structures.bbox import QuadriBoxes

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
OUT = ROOT / 'outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2'
AR_CUTOFF = 2.1
ARMS = {
    'CONT': OUT / 'raw_predictions/dior_cont_seed0.pkl',
    'VM_NLL': OUT / 'raw_predictions/dior_vm_nll_seed0.pkl',
    'CORA': OUT / 'raw_predictions/dior_cora_seed0.pkl',
}
DIOR_TEST_ANN = ROOT / 'top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test'
DIOR_CLASSES = (
    'airplane', 'airport', 'baseballfield', 'basketballcourt', 'bridge',
    'chimney', 'dam', 'Expressway-Service-area', 'Expressway-toll-station',
    'golffield', 'groundtrackfield', 'harbor', 'overpass', 'ship', 'stadium',
    'storagetank', 'tenniscourt', 'trainstation', 'vehicle', 'windmill')
DIOR_LABELS = {name: idx for idx, name in enumerate(DIOR_CLASSES)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def tensor(value) -> torch.Tensor:
    return (value.tensor if hasattr(value, 'tensor') else value).detach().cpu().float()


def le90_error_deg(pred: np.ndarray, gt: np.ndarray) -> float:
    # Long-side canonical heading makes w/h representation switches harmless.
    def heading(box: np.ndarray) -> float:
        angle = math.degrees(float(box[4]))
        if float(box[3]) > float(box[2]):
            angle += 90.
        return angle % 180.
    delta = abs((heading(pred) - heading(gt)) % 180.)
    return min(delta, 180. - delta)


@lru_cache(maxsize=None)
def gt_for_image(img_id: str) -> tuple[np.ndarray, np.ndarray]:
    """Read the frozen r043 DOTA-format test annotation for one DIOR image.

    ``DumpDetResults`` deliberately serializes predictions plus sample metadata,
    not GT.  This reconstructs exactly the test GT from the already-registered
    r043 annotation endpoint; it never consults model output or calibrates a
    metric parameter.
    """
    path = DIOR_TEST_ANN / f'{img_id}.txt'
    if not path.is_file():
        raise RuntimeError(f'missing frozen DIOR test annotation: {path}')
    qboxes, labels = [], []
    for line in path.read_text().splitlines():
        fields = line.split()
        if not fields:
            continue
        if len(fields) < 10 or fields[8] not in DIOR_LABELS:
            raise RuntimeError(f'bad DIOR annotation line in {path}: {line!r}')
        qboxes.append([float(v) for v in fields[:8]])
        labels.append(DIOR_LABELS[fields[8]])
    if not qboxes:
        return np.empty((0, 5), dtype=np.float32), np.empty((0,), dtype=np.int64)
    rboxes = QuadriBoxes(torch.tensor(qboxes, dtype=torch.float32)).convert_to('rbox').tensor
    return rboxes.cpu().numpy(), np.asarray(labels, dtype=np.int64)


def match_record(rec: dict, arm: str) -> list[dict]:
    pi = rec['pred_instances']
    pb = tensor(pi['bboxes']).numpy()
    ps = tensor(pi['scores']).numpy()
    pl = tensor(pi['labels']).long().numpy()
    gb, gl = gt_for_image(str(rec['img_id']))
    native = None
    if arm != 'CONT':
        if 'cora_native_risk' not in pi:
            raise RuntimeError(f'{arm}/{rec["img_id"]}: native risk missing')
        native = tensor(pi['cora_native_risk']).numpy()
        if native.shape != ps.shape or not np.isfinite(native).all():
            raise RuntimeError(f'{arm}/{rec["img_id"]}: invalid native risk')
    if not len(pb) or not len(gb):
        return []
    overlaps = box_iou_rotated(torch.from_numpy(pb), torch.from_numpy(gb)).numpy()
    used: set[int] = set()
    rows: list[dict] = []
    for pred_idx in sorted(range(len(pb)), key=lambda i: (-float(ps[i]), i)):
        candidates = [gt_idx for gt_idx in range(len(gb))
                      if gt_idx not in used and int(pl[pred_idx]) == int(gl[gt_idx])
                      and float(overlaps[pred_idx, gt_idx]) >= .5]
        if not candidates:
            continue
        gt_idx = min(candidates, key=lambda i: (-float(overlaps[pred_idx, i]), i))
        used.add(gt_idx)
        pred, gt = pb[pred_idx], gb[gt_idx]
        ar = max(float(gt[2]), float(gt[3])) / max(min(float(gt[2]), float(gt[3])), 1e-6)
        angle_error = le90_error_deg(pred, gt)
        native_risk = None if native is None else float(native[pred_idx])
        # Metric API uses larger values as earlier retention.  No fusion:
        # learned arms negate their native risk, CONT stays detection score.
        selection = float(ps[pred_idx]) if arm == 'CONT' else -native_risk
        rows.append(dict(
            arm=arm, dataset='DIOR-R', image_id=str(rec['img_id']), pred_id=int(pred_idx),
            gt_id=int(gt_idx), class_id=int(pl[pred_idx]), match_iou=float(overlaps[pred_idx, gt_idx]),
            gt_aspect_ratio=ar, gt_size=float(gt[2] * gt[3]),
            angle_error_deg=angle_error, orientation_harm=min(angle_error / 90., 1.),
            detector_score=float(ps[pred_idx]), native_risk=native_risk,
            selection_score=selection))
    return rows


def augrc_and_risk70(selection: np.ndarray, harm: np.ndarray) -> tuple[float, float]:
    """Whole-tie-group AUGRC and Risk@70; lower values are better."""
    order = np.argsort(-selection, kind='stable')
    score, risk = selection[order], harm[order]
    starts = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    count = np.diff(np.r_[starts, len(score)]).astype(float)
    summed = np.add.reduceat(risk, starts)
    cumulative_count = np.cumsum(count)
    cumulative_risk = np.cumsum(summed)
    total = float(len(score))
    augrc = float(np.sum((np.r_[0., cumulative_risk[:-1] / total] + cumulative_risk / total)
                         * (count / total) / 2.))
    idx = int(np.searchsorted(cumulative_count, .70 * total))
    return augrc, float(cumulative_risk[idx] / cumulative_count[idx])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=OUT / 'metrics')
    args = parser.parse_args()
    if any(not p.is_file() for p in ARMS.values()):
        missing = [str(p) for p in ARMS.values() if not p.is_file()]
        raise RuntimeError(f'raw exports incomplete: {missing}')
    args.out.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    raw_manifest = {}
    for arm, path in ARMS.items():
        records = pickle.load(path.open('rb'))
        if len(records) != 11738:
            raise RuntimeError(f'{arm}: expected 11738 DIOR test images, got {len(records)}')
        rows = [row for rec in records for row in match_record(rec, arm)]
        if not rows:
            raise RuntimeError(f'{arm}: zero matched TP rows')
        all_rows.extend(rows)
        raw_manifest[arm] = dict(path=str(path.relative_to(ROOT)), sha256=sha256(path),
                                 bytes=path.stat().st_size, images=len(records), matched_rows=len(rows))
    rows_path = args.out / 'matched_tp_rows.jsonl'
    with rows_path.open('w', encoding='utf-8') as f:
        for row in all_rows:
            f.write(json.dumps(row, separators=(',', ':')) + '\n')
    metrics = []
    for arm in ARMS:
        arm_rows = [r for r in all_rows if r['arm'] == arm]
        for scope, selected in [('all_ar', arm_rows), ('ar_ge_2_1', [r for r in arm_rows if r['gt_aspect_ratio'] >= AR_CUTOFF])]:
            if not selected:
                raise RuntimeError(f'{arm}/{scope}: zero matched TP rows')
            selection = np.asarray([r['selection_score'] for r in selected], dtype=float)
            harm = np.asarray([r['orientation_harm'] for r in selected], dtype=float)
            augrc, risk70 = augrc_and_risk70(selection, harm)
            metrics.append(dict(dataset='DIOR-R', arm=arm, scope=scope, rows=len(selected),
                                images=len({r['image_id'] for r in selected}), AUGRC=augrc,
                                Risk_at_70=risk70,
                                mean_angle_error_deg=float(np.mean([r['angle_error_deg'] for r in selected])),
                                median_angle_error_deg=float(np.median([r['angle_error_deg'] for r in selected])),
                                selection_definition='detection_score' if arm == 'CONT' else 'negative_native_risk'))
    metric_path = args.out / 'risk_metrics.csv'
    with metric_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics[0]))
        writer.writeheader(); writer.writerows(metrics)
    manifest = dict(schema_version=1, dataset='DIOR-R', split='r043-development-test',
                    matching='class-aware score-ordered rotated IoU >= 0.5, one GT per arm',
                    orientation_harm='min(le90 long-side angle error degrees / 90, 1)',
                    native_risk='VM_NLL/CORA only; no detection-score fusion',
                    risk_metrics='whole-tie-group AUGRC and Risk@70; lower is better',
                    raw_exports=raw_manifest, matched_rows_path=str(rows_path.relative_to(ROOT)),
                    matched_rows_sha256=sha256(rows_path), metrics_path=str(metric_path.relative_to(ROOT)),
                    metrics_sha256=sha256(metric_path), can_recompute=True,
                    generation_command='conda run -n pcp-obb python experiments/r049_cora_obb/build_dior_g2_metrics.py')
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(status='complete', metrics=str(metric_path), matched_rows=len(all_rows)), indent=2))


if __name__ == '__main__':
    main()

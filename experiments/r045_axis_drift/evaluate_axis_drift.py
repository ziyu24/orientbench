#!/usr/bin/env python3
"""Frozen r045 matching, policy selection, and axis-drift calculations.

This implementation deliberately keeps score-only thresholding separate from
GT-dependent evaluation.  ``source`` may open DIOR annotations; the later
``target`` mode is only invoked after the two required seals are pushed.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import pickle
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.stats import binom

CLASSES = ['airplane','airport','baseballfield','basketballcourt','bridge','chimney','dam',
           'Expressway-Service-area','Expressway-toll-station','golffield','groundtrackfield',
           'harbor','overpass','ship','stadium','storagetank','tenniscourt','trainstation',
           'vehicle','windmill']
Q_GRID = (0.25, 0.50, 1.00)
C_GRID = (0.90, 0.85, 0.80, 0.75, 0.70)
# The AI4RS RTMDet DIOR config orders the two Expressway classes before dam;
# its integer prediction labels must be translated to the canonical GT order.
RTMDET_DIOR_LABEL_REMAP = {6: 7, 7: 8, 8: 6}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canon(box):
    x, y, w, h, theta = map(float, box[:5])
    theta = ((theta + math.pi / 2) % math.pi) - math.pi / 2
    if h > w:
        w, h = h, w
        theta = ((theta + math.pi) % math.pi) - math.pi / 2
    return np.array((x, y, w, h, theta), dtype=float)


def polygon(box):
    x, y, w, h, theta = canon(box)
    points = np.array([[w/2,h/2],[-w/2,h/2],[-w/2,-h/2],[w/2,-h/2]], np.float32)
    c, s = math.cos(theta), math.sin(theta)
    return points @ np.array([[c,s],[-s,c]], np.float32) + np.array([x,y], np.float32)


def riou(a, b):
    pa, pb = polygon(a), polygon(b)
    aa, ab = abs(cv2.contourArea(pa)), abs(cv2.contourArea(pb))
    inter, _ = cv2.intersectConvexConvex(pa, pb)
    return float(inter / max(aa + ab - inter, 1e-12))


def axis_error_deg(a, b):
    diff = abs(float(canon(a)[4]) - float(canon(b)[4])) % math.pi
    return math.degrees(min(diff, math.pi - diff))


def parse_gt(ann_dir: Path, image_id: str):
    rows = []
    for line in (ann_dir / f'{image_id}.txt').read_text().splitlines():
        fields = line.split()
        if len(fields) < 10 or fields[8] not in CLASSES:
            continue
        pts = np.asarray(fields[:8], dtype=np.float32).reshape(4, 2)
        (x, y), (w, h), ang = cv2.minAreaRect(pts)
        rows.append((canon((x, y, w, h, math.radians(ang))), CLASSES.index(fields[8])))
    return rows


def tensor_array(x):
    return np.asarray(x.detach().cpu() if hasattr(x, 'detach') else x)


def load_predictions(path: Path, ann_dir: Path):
    raw = pickle.load(path.open('rb'))
    result = []
    if raw and isinstance(raw[0], dict) and 'pred_instances' in raw[0]:
        remap = RTMDET_DIOR_LABEL_REMAP if 'rtmdet' in path.name else {}
        for item in raw:
            pi = item['pred_instances']
            result.append((str(item['img_id']), [
                (canon(box), float(score), remap.get(int(label), int(label)))
                for box, score, label in zip(tensor_array(pi['bboxes']), tensor_array(pi['scores']), tensor_array(pi['labels']))
            ]))
        return result
    # Legacy mmrotate result lists do not retain img_id.  Its dataset consumes
    # annfiles through glob in this exact order; retain the same association.
    ids = [Path(x).stem for x in glob.glob(str(ann_dir / '*.txt'))]
    if len(raw) != len(ids):
        raise RuntimeError(f'legacy prediction/image mismatch: {len(raw)} != {len(ids)}')
    for image_id, per_class in zip(ids, raw):
        preds = []
        for label, boxes in enumerate(per_class):
            for box in np.asarray(boxes):
                preds.append((canon(box[:5]), float(box[5]), int(label)))
        result.append((image_id, preds))
    return result


def flat_predictions(predictions, ids):
    rows = []
    for image_id, preds in predictions:
        if image_id not in ids:
            continue
        for pred_id, (box, score, label) in enumerate(preds):
            rows.append(dict(image_id=image_id, pred_id=pred_id, detection_score=score,
                             class_id=label, cx=box[0], cy=box[1], w=box[2], h=box[3], angle_rad=box[4]))
    return pd.DataFrame(rows, columns=['image_id','pred_id','detection_score','class_id','cx','cy','w','h','angle_rad'])


def match_predictions(predictions, ann_dir: Path, ids):
    rows = []
    for image_id, preds in predictions:
        if image_id not in ids:
            continue
        gt = parse_gt(ann_dir, image_id)
        used = set()
        for pred_id, (box, score, label) in enumerate(sorted(preds, key=lambda x: -x[1])):
            candidates = [(riou(box, gbox), gi) for gi, (gbox, glabel) in enumerate(gt)
                          if gi not in used and glabel == label]
            best_iou, gt_id = max(candidates, default=(0.0, -1))
            if best_iou < .5:
                continue
            used.add(gt_id)
            gt_box, _ = gt[gt_id]
            e = axis_error_deg(box, gt_box)
            gt_ar = gt_box[2] / max(gt_box[3], 1e-12)
            rows.append(dict(image_id=image_id, pred_id=pred_id, gt_id=gt_id, class_id=label,
                             detection_score=score, iou=best_iou, angle_error_deg=e,
                             gt_w=gt_box[2], gt_h=gt_box[3], gt_ar=gt_ar,
                             pred_w=box[2], pred_h=box[3], pred_ar=box[2]/max(box[3], 1e-12)))
    out = pd.DataFrame(rows)
    if not out.empty:
        out['d_tip'] = np.minimum(1., (out.gt_ar / 2.) * np.sin(np.deg2rad(out.angle_error_deg)))
        for q in Q_GRID:
            out[f'z_{q:.2f}'] = (out.d_tip > q).astype(int)
    return out


def hb_ucb(image_risks: pd.Series, alpha: float) -> float:
    """One-sided Hoeffding--Bentkus UCB for [0,1] image-level risks.

    The binomial extremal inversion is the Bentkus part; Hoeffding is retained
    as a second valid upper bound and their minimum is still conservative.
    """
    values = np.asarray(image_risks, dtype=float)
    n = len(values)
    if n == 0:
        return 1.
    mean = float(values.mean())
    hoeffding = min(1., mean + math.sqrt(math.log(1./alpha) / (2*n)))
    k = int(math.ceil(n * mean - 1e-12))
    lo, hi = mean, 1.
    for _ in range(80):
        mid = (lo + hi) / 2
        if math.e * binom.cdf(k, n, mid) <= alpha:
            hi = mid
        else:
            lo = mid
    return min(hoeffding, hi)


def image_risk(matched, ids, threshold, q):
    retained = matched[matched.detection_score >= threshold]
    eligible = retained[retained.gt_ar >= 2.1]
    means = eligible.groupby('image_id')[f'z_{q:.2f}'].mean().reindex(sorted(ids), fill_value=0.)
    cont = eligible.groupby('image_id').d_tip.mean().reindex(sorted(ids), fill_value=0.)
    return retained, eligible, means, cont


def quantile_threshold(pred_rows, coverage):
    scores = pred_rows.detection_score.to_numpy(dtype=float)
    if not len(scores):
        raise RuntimeError('no predictions for score quantile')
    return float(np.quantile(scores, 1. - coverage, method='higher'))


def ap50(predictions, ann_dir: Path, ids, threshold):
    """Class-aware AP50 on the frozen images, using each class score ranking."""
    gts = {iid: parse_gt(ann_dir, iid) for iid in ids}
    aps = []
    for label in range(len(CLASSES)):
        n_gt = sum(sum(int(l == label) for _, l in gts[iid]) for iid in ids)
        if not n_gt:
            continue
        dets = []
        for iid, preds in predictions:
            if iid in ids:
                dets.extend((score, iid, box) for box, score, lab in preds if lab == label and score >= threshold)
        dets.sort(reverse=True, key=lambda x: x[0])
        used = {iid: set() for iid in ids}; tp=[]; fp=[]
        for _, iid, box in dets:
            opts=[(riou(box,g),j) for j,(g,l) in enumerate(gts[iid]) if l == label and j not in used[iid]]
            best,j=max(opts, default=(0.,-1))
            if best >= .5:
                used[iid].add(j); tp.append(1); fp.append(0)
            else: tp.append(0); fp.append(1)
        if not tp:
            aps.append(0.); continue
        tp, fp = np.cumsum(tp), np.cumsum(fp)
        recall, precision = tp/n_gt, tp/np.maximum(tp+fp, 1)
        mrec=np.r_[0.,recall,1.]; mpre=np.r_[0.,precision,0.]
        mpre=np.maximum.accumulate(mpre[::-1])[::-1]
        aps.append(float(np.sum((mrec[1:]-mrec[:-1])*mpre[1:])))
    return float(np.mean(aps)) if aps else 0.


def source(args):
    root = Path(args.root); out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    ann_dir=Path(args.ann_dir); pred_ann_dir=Path(args.pred_ann_dir or args.ann_dir)
    # Keep leading zeroes in DIOR image identifiers; pandas' numeric inference
    # would silently turn ``00172`` into ``172`` and invalidate all joins.
    cal_ids=set(pd.read_csv(args.cal_split, dtype={'image_id': str}).image_id.astype(str)); audit_ids=set(pd.read_csv(args.audit_split, dtype={'image_id': str}).image_id.astype(str))
    inventory=json.loads(Path(args.inventory).read_text())
    summary=[]; candidates={}
    for item in inventory['source_prediction_files']:
        family=item['family']; pred_path=Path(item['path']); predictions=load_predictions(pred_path, pred_ann_dir)
        flat=flat_predictions(predictions, cal_ids | audit_ids)
        matched=match_predictions(predictions, ann_dir, cal_ids | audit_ids)
        flat.to_csv(out/f'{family}_all_predictions.csv', index=False)
        matched.to_csv(out/f'{family}_matched.csv', index=False)
        candidates[family]=(predictions, flat, matched)
        cal_flat=flat[flat.image_id.isin(cal_ids)]
        cal_match=matched[matched.image_id.isin(cal_ids)]
        for coverage in C_GRID:
            threshold=quantile_threshold(cal_flat, coverage)
            _, eligible, risks, cont=image_risk(cal_match, cal_ids, threshold, .5)
            ucb=hb_ucb(risks, .05/len(inventory['source_prediction_files']))
            summary.append(dict(family=family, coverage=coverage, score_threshold=threshold,
                                d_cal_mean_d_tip=float(eligible.d_tip.mean()) if len(eligible) else 0.0, d_cal_severe_risk=float(risks.mean()),
                                d_cal_hb_ucb=ucb, d_cal_eligible_coverage=float(len(eligible)/max(1, (cal_match.gt_ar>=2.1).sum())),
                                passes=bool(ucb <= .10)))
    grid=pd.DataFrame(summary); grid.to_csv(out/'source_dcal_policy_grid.csv',index=False)
    feasible=grid[grid.passes].sort_values(['family','coverage'], ascending=[True,False]).groupby('family',as_index=False).first()
    audit=[]
    for rec in feasible.to_dict('records'):
        family=rec['family']; predictions,_,matched=candidates[family]
        audit_ids_rows=matched[matched.image_id.isin(audit_ids)]
        _, eligible, risks, cont=image_risk(audit_ids_rows, audit_ids, rec['score_threshold'], .5)
        audit.append(dict(**rec, d_audit_mean_d_tip=float(eligible.d_tip.mean()) if len(eligible) else 0.0, d_audit_severe_risk=float(risks.mean()),
                          d_audit_hb_ucb=hb_ucb(risks,.05/len(inventory['source_prediction_files'])),
                          d_audit_eligible_coverage=float(len(eligible)/max(1,(audit_ids_rows.gt_ar>=2.1).sum())),
                          d_audit_ap50=ap50(predictions,ann_dir,audit_ids,rec['score_threshold'])))
    pd.DataFrame(audit).to_csv(out/'source_daudit_selected_policy.csv',index=False)
    print(json.dumps({'families':len(candidates),'feasible':len(feasible),'output':str(out)},indent=2))


def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='mode',required=True)
    s=sub.add_parser('source'); s.add_argument('--root',required=True); s.add_argument('--out',required=True); s.add_argument('--ann-dir',required=True); s.add_argument('--pred-ann-dir'); s.add_argument('--cal-split',required=True); s.add_argument('--audit-split',required=True); s.add_argument('--inventory',required=True)
    a=p.parse_args()
    if a.mode=='source': source(a)

if __name__=='__main__': main()

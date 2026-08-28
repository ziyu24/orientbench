#!/usr/bin/env python3
"""Freeze the exact r052 G1 positive decoded-proposal universe from DOTA train."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

import torch
from mmcv.ops import box_iou_rotated

N_TARGET = 1024
PER_IMAGE_MAX = 4


def as_tensor(x) -> torch.Tensor:
    if hasattr(x, 'tensor'):
        x = x.tensor
    return torch.as_tensor(x, dtype=torch.float32)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--predictions', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    samples = pickle.load(args.predictions.open('rb'))
    by_id = {str(s['img_id']): s for s in samples}
    chosen = []
    for image_id in sorted(by_id, key=lambda x: (hashlib.sha256(x.encode()).hexdigest(), x)):
        sample = by_id[image_id]
        pred, gt = sample['pred_instances'], sample['gt_instances']
        boxes, labels = as_tensor(pred['bboxes']), torch.as_tensor(pred['labels'], dtype=torch.long)
        scores = as_tensor(pred['scores'])
        gt_boxes, gt_labels = as_tensor(gt['bboxes']), torch.as_tensor(gt['labels'], dtype=torch.long)
        local = []
        for cls in torch.unique(labels).tolist():
            pidx = torch.where(labels == cls)[0]
            gidx = torch.where(gt_labels == cls)[0]
            if not len(pidx) or not len(gidx):
                continue
            iou = box_iou_rotated(boxes[pidx].contiguous(), gt_boxes[gidx].contiguous(), aligned=False, clockwise=True)
            best_iou, best_gt = iou.max(dim=1)
            for j, index in enumerate(pidx.tolist()):
                if float(best_iou[j]) >= .5:
                    local.append((float(scores[index]), index, int(gidx[best_gt[j]]), float(best_iou[j])))
        # UID is assigned before selection/NMS-style ordering and is independent
        # of image traversal.  Score is never used to change the frozen count.
        for _, index, gt_index, iou in sorted(local, key=lambda x: x[1])[:PER_IMAGE_MAX]:
            box = boxes[index].tolist()
            chosen.append({
                'image_id': image_id,
                'proposal_uid': f'{image_id}:{index}',
                'proposal_index': index,
                'class_id': int(labels[index]),
                'score': float(scores[index]),
                'box': [float(v) for v in box],
                'matched_gt_index': gt_index,
                'matched_gt_box': [float(v) for v in gt_boxes[gt_index].tolist()],
                'rotated_iou': iou,
            })
            if len(chosen) == N_TARGET:
                break
        if len(chosen) == N_TARGET:
            break
    if len(chosen) != N_TARGET:
        raise RuntimeError(f'NOT_ADJUDICATED_ASSET_ENV: found {len(chosen)} positives, need exactly {N_TARGET}')
    payload = {
        'schema_version': 1,
        'dataset': 'DOTA-v1.0 train only',
        'selection': 'SHA256(image_id), image_id tie-break; proposal index ascending; max four/image; class match and rotated IoU >= 0.5',
        'count': N_TARGET,
        'proposals': chosen,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + '\n')
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()
    args.out.with_suffix('.sha256').write_text(digest + '  ' + args.out.name + '\n')
    print(json.dumps({'count': len(chosen), 'sha256': digest}, indent=2))


if __name__ == '__main__':
    main()

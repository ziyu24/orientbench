#!/usr/bin/env python3
"""Freeze the r052 G1 universe from actual pre-final-NMS detector rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

import torch
from mmcv.ops import box_iou_rotated

N_TARGET, PER_IMAGE_MAX = 1024, 4


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--shard-dir', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    samples = []
    files = sorted(args.shard_dir.glob('rank[0-9].pkl'))
    for f in files:
        samples.extend(pickle.load(f.open('rb')))
    by_id = {s['image_id']: s for s in samples}
    chosen = []
    for image_id in sorted(by_id, key=lambda x: (hashlib.sha256(x.encode()).hexdigest(), x)):
        sample, pre = by_id[image_id], by_id[image_id]['pre_nms']
        final = by_id[image_id]['final_nms']
        boxes = torch.as_tensor(pre['boxes'], dtype=torch.float32)
        labels = torch.as_tensor(pre['labels'], dtype=torch.long)
        gt_boxes = torch.as_tensor(sample['gt_boxes'], dtype=torch.float32)
        gt_labels = torch.as_tensor(sample['gt_labels'], dtype=torch.long)
        eligible = []
        for cls in torch.unique(labels).tolist():
            pidx, gidx = torch.where(labels == cls)[0], torch.where(gt_labels == cls)[0]
            if not len(pidx) or not len(gidx):
                continue
            overlaps = box_iou_rotated(boxes[pidx].contiguous(), gt_boxes[gidx].contiguous(),
                                       aligned=False, clockwise=True)
            best_iou, best_gt = overlaps.max(dim=1)
            for j, idx in enumerate(pidx.tolist()):
                if float(best_iou[j]) >= .5:
                    eligible.append((int(pre['proposal_index'][idx]), idx,
                                     int(gidx[best_gt[j]]), float(best_iou[j])))
        for _, idx, gt_idx, iou in sorted(eligible)[:PER_IMAGE_MAX]:
            candidate_uids = list(pre['candidate_uids'][idx])
            if len(candidate_uids) != 12 or len(set(candidate_uids)) != 12:
                raise RuntimeError('invalid candidate UID lineage before frozen manifest')
            chosen.append(dict(image_id=image_id, image_path=sample['image_path'],
                               proposal_uid=pre['proposal_uid'][idx], class_uid=pre['class_uid'][idx],
                               candidate_uids=candidate_uids,
                               proposal_index=int(pre['proposal_index'][idx]),
                               class_id=int(labels[idx]), score=float(pre['scores'][idx]),
                               decoded_pre_nms_box=[float(v) for v in boxes[idx].tolist()],
                               matched_gt_index=gt_idx,
                               matched_gt_box=[float(v) for v in gt_boxes[gt_idx].tolist()],
                               rotated_iou=iou,
                               # Final NMS lineage is exported from the same
                               # detector invocation. A pre-NMS row need not
                               # survive NMS, so absence is represented as
                               # null rather than reconstructed geometrically.
                               final_nms_keep_indices=[int(final['nms_keep_index'][j])
                                   for j, uid in enumerate(final['proposal_uid'])
                                   if uid == pre['proposal_uid'][idx]]))
            if len(chosen) == N_TARGET:
                break
        if len(chosen) == N_TARGET:
            break
    if len(chosen) != N_TARGET:
        raise RuntimeError(f'NOT_ADJUDICATED_ASSET_ENV: found {len(chosen)} pre-NMS positives, need 1024')
    payload = dict(schema_version=2, dataset='DOTA-v1.0 train only', count=N_TARGET,
                   source='detector-native decoded proposals before final ROI NMS',
                   selection='SHA256(image_id), image_id tie-break; proposal index ascending; max four/image; class match and rotated IoU >= 0.5',
                   source_shards=[str(x) for x in files], proposals=chosen)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + '\n')
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()
    args.out.with_suffix('.sha256').write_text(digest + '  ' + args.out.name + '\n')
    print(json.dumps({'count': len(chosen), 'sha256': digest}))


if __name__ == '__main__':
    main()

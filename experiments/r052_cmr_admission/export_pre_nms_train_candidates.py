#!/usr/bin/env python3
"""Low-footprint distributed export of true pre-NMS eligible r052 rows.

The detector is invoked for every image.  Unlike the superseded raw-shard
attempt, this only persists the at-most-four deterministic, IoU-qualified
pre-NMS candidates per image; it never reconstructs a proposal after NMS.
"""
from __future__ import annotations

import hashlib
import os
import pickle
from pathlib import Path

import torch
import torch.distributed as dist
from mmcv.ops import box_iou_rotated
from mmdet.apis import inference_detector, init_detector

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
BASE = ROOT / 'outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1'
SOURCE = BASE / 'train_proposal_export/predictions.pkl'
CFG = ROOT / 'configs/r052_cmr_admission/dota_orcnn_joint_cmr_smoke_correction.py'
CKPT = BASE / 'correction_cmr_joint_smoke_5/epoch_1.pth'
PER_IMAGE_MAX = 4


def candidates(sample: dict, pred) -> list[dict]:
    pre = pred.r052_pre_nms.records
    boxes = torch.as_tensor(pre['boxes'], dtype=torch.float32)
    labels = torch.as_tensor(pre['labels'], dtype=torch.long)
    gt_boxes = sample['gt_instances']['bboxes'].detach().cpu().float()
    gt_labels = sample['gt_instances']['labels'].detach().cpu().long()
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
    nms_by_proposal = {}
    for j, uid in enumerate(pred.proposal_uid):
        nms_by_proposal.setdefault(uid, []).append(int(pred.nms_keep_index[j]))
    out = []
    for _, idx, gt_idx, iou in sorted(eligible)[:PER_IMAGE_MAX]:
        uid = pre['proposal_uid'][idx]
        candidate_uids = list(pre['candidate_uids'][idx])
        if len(candidate_uids) != 12 or len(set(candidate_uids)) != 12:
            raise RuntimeError('invalid detector-native candidate UID lineage')
        out.append(dict(image_id=str(sample['img_id']), image_path=str(sample['img_path']),
                        proposal_uid=uid, class_uid=pre['class_uid'][idx],
                        candidate_uids=candidate_uids,
                        proposal_index=int(pre['proposal_index'][idx]),
                        class_id=int(labels[idx]), score=float(pre['scores'][idx]),
                        decoded_pre_nms_box=[float(v) for v in boxes[idx].tolist()],
                        rpn_decoded_box=[float(v) for v in pre['rpn_decoded_boxes'][idx].tolist()],
                        rpn_proposal_score=float(pre['rpn_proposal_scores'][idx]),
                        matched_gt_index=gt_idx,
                        matched_gt_box=[float(v) for v in gt_boxes[gt_idx].tolist()],
                        rotated_iou=iou,
                        final_nms_keep_indices=nms_by_proposal.get(uid, [])))
    return out


def main() -> None:
    dist.init_process_group('nccl')
    rank, world = dist.get_rank(), dist.get_world_size()
    torch.cuda.set_device(rank)
    source = pickle.load(SOURCE.open('rb'))
    source.sort(key=lambda x: (hashlib.sha256(str(x['img_id']).encode()).hexdigest(), str(x['img_id'])))
    source = source[:int(os.environ.get('R052_MAX_IMAGES', '6000'))]
    model = init_detector(str(CFG), str(CKPT), device=f'cuda:{rank}')
    out_root = BASE / os.environ['R052_EXPORT_DIR']
    out_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for source_index in range(rank, len(source), world):
        sample = source[source_index]
        pred = inference_detector(model, str(sample['img_path'])).pred_instances
        rows.extend(candidates(sample, pred))
        if (source_index // world + 1) % 64 == 0:
            with (out_root / f'rank{rank}.partial.pkl').open('wb') as f:
                pickle.dump(rows, f, protocol=pickle.HIGHEST_PROTOCOL)
    with (out_root / f'rank{rank}.pkl').open('wb') as f:
        pickle.dump(rows, f, protocol=pickle.HIGHEST_PROTOCOL)
    dist.barrier()
    dist.destroy_process_group()


if __name__ == '__main__':
    main()

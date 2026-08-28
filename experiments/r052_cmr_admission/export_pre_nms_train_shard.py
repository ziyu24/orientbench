#!/usr/bin/env python3
"""Distributed train-only exporter of detector-native, pre-final-NMS rows."""
from __future__ import annotations

import hashlib
import os
import pickle
from pathlib import Path

import torch
import torch.distributed as dist
from mmdet.apis import inference_detector, init_detector

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
BASE = ROOT / 'outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1'
SOURCE = BASE / 'train_proposal_export/predictions.pkl'
CFG = ROOT / 'configs/r052_cmr_admission/dota_orcnn_joint_cmr_smoke_correction.py'
CKPT = BASE / 'correction_cmr_joint_smoke_5/epoch_1.pth'


def main() -> None:
    dist.init_process_group('nccl')
    rank, world = dist.get_rank(), dist.get_world_size()
    torch.cuda.set_device(rank)
    max_images = int(os.environ.get('R052_MAX_IMAGES', '512'))
    source = pickle.load(SOURCE.open('rb'))
    source.sort(key=lambda x: (hashlib.sha256(str(x['img_id']).encode()).hexdigest(), str(x['img_id'])))
    source = source[:max_images]
    model = init_detector(str(CFG), str(CKPT), device=f'cuda:{rank}')
    out_root = BASE / 'correction_pre_nms_export'
    out_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for source_index in range(rank, len(source), world):
        sample = source[source_index]
        pred = inference_detector(model, str(sample['img_path'])).pred_instances
        pre = pred.r052_pre_nms.records
        gt = sample['gt_instances']
        rows.append(dict(image_id=str(sample['img_id']), image_path=str(sample['img_path']),
                         source_index=source_index, pre_nms=pre,
                         gt_boxes=gt['bboxes'].detach().cpu(),
                         gt_labels=gt['labels'].detach().cpu()))
        if len(rows) % 16 == 0:
            with (out_root / f'rank{rank}.partial.pkl').open('wb') as f:
                pickle.dump(rows, f, protocol=pickle.HIGHEST_PROTOCOL)
    with (out_root / f'rank{rank}.pkl').open('wb') as f:
        pickle.dump(rows, f, protocol=pickle.HIGHEST_PROTOCOL)
    dist.barrier()
    dist.destroy_process_group()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Four-GPU detector-native r052 inference/provenance smoke."""
from __future__ import annotations

import json
import os
from pathlib import Path

import torch
import torch.distributed as dist
from mmdet.apis import inference_detector, init_detector


ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
CKPT = ROOT / ('outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/'
               'g1/correction_cmr_joint_smoke_5/epoch_1.pth')
CFG = ROOT / 'configs/r052_cmr_admission/dota_orcnn_joint_cmr_smoke_correction.py'
IMAGES = [
    ROOT.parent.parent.parent / 'data/dataset/dota/dota1.0/split_ss_dota10/train/images/P2805__1024__824___824.png',
    ROOT.parent.parent.parent / 'data/dataset/dota/dota1.0/split_ss_dota10/train/images/P2805__1024__824___2181.png',
    ROOT.parent.parent.parent / 'data/dataset/dota/dota1.0/split_ss_dota10/train/images/P2805__1024__824___1648.png',
    ROOT.parent.parent.parent / 'data/dataset/dota/dota1.0/split_ss_dota10/train/images/P2805__1024__824___0.png',
]


def main() -> None:
    dist.init_process_group('nccl')
    rank = dist.get_rank()
    torch.cuda.set_device(rank)
    model = init_detector(str(CFG), str(CKPT), device=f'cuda:{rank}')
    result = inference_detector(model, str(IMAGES[rank])).pred_instances
    pre = result.r052_pre_nms.records
    ok = (len(pre['proposal_uid']) > 0 and len(result.proposal_uid) == len(result) and
          len(result.class_uid) == len(result) and len(result.candidate_uids) == len(result) and
          all(len(x) == 12 for x in result.candidate_uids))
    out = ROOT / ('outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/'
                  f'g1/correction_four_gpu_inference_smoke/rank{rank}.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(rank=rank, image=str(IMAGES[rank]), detections=len(result),
                                   pre_nms_proposals=len(pre['proposal_uid']), passed=bool(ok)), indent=2) + '\n')
    dist.barrier()
    dist.destroy_process_group()
    if not ok:
        raise SystemExit('r052 native inference/provenance smoke failed')


if __name__ == '__main__':
    main()

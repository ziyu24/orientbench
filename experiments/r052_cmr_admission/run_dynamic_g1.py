#!/usr/bin/env python3
"""Four-GPU dynamic r052 G1 tests on frozen detector-native pre-NMS rows."""
from __future__ import annotations

import copy
import json
import os
import math
from collections import defaultdict
from pathlib import Path

import cv2
import torch
import torch.distributed as dist
from mmcv.transforms import Compose
from mmdet.apis import init_detector
from mmdet.utils import get_test_pipeline_cfg

from experiments.r052_cmr_admission.joint_api import K, ProposalObservationArms, axial_delta, joint_loss
from experiments.r052_cmr_admission.joint_roi_head import _box_residual

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
BASE = ROOT / 'outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1'
MANIFEST = BASE / 'correction_pre_nms_export_6000_uid_v2_stream/frozen_1024_pre_nms_positive_proposals.json'
CKPT = BASE / 'correction_cmr_joint_smoke_5/epoch_1.pth'
CFG = ROOT / 'configs/r052_cmr_admission/dota_orcnn_joint_cmr_smoke_correction.py'


def finite(x): return bool(torch.isfinite(x).all().item())


def build_feature(model, pipeline, image_path, boxes, *, image=None):
    item = dict(img_path=image_path, img_id='r052') if image is None else dict(img=image, img_id='r052')
    data = pipeline(item)
    data = model.data_preprocessor({'inputs': [data['inputs']], 'data_samples': [data['data_samples']]}, False)
    with torch.no_grad():
        x = model.extract_feat(data['inputs'])
    priors = torch.tensor(boxes, device=data['inputs'].device, dtype=torch.float32)
    ids = torch.zeros(len(priors), dtype=torch.long, device=priors.device)
    return model.roi_head._r052_features(x, priors, ids), priors


def rotate_boxes(boxes, height, width, step):
    m = cv2.getRotationMatrix2D((width / 2, height / 2), -step * 180. / math.pi, 1.)
    out = []
    for b in boxes:
        x, y = m @ [b[0], b[1], 1.]
        out.append([float(x), float(y), b[2], b[3], float(b[4] + step)])
    return out, m


def main() -> None:
    dist.init_process_group('nccl')
    rank, world = dist.get_rank(), dist.get_world_size()
    torch.cuda.set_device(rank)
    device = torch.device(f'cuda:{rank}')
    manifest = json.loads(MANIFEST.read_text())['proposals']
    grouped = defaultdict(list)
    for row in manifest: grouped[row['image_path']].append(row)
    groups = sorted(grouped.items())
    model = init_detector(str(CFG), str(CKPT), device=str(device))
    model.eval()
    pipeline = Compose(get_test_pipeline_cfg(model.cfg))
    array_cfg = copy.deepcopy(get_test_pipeline_cfg(model.cfg)); array_cfg[0]['type'] = 'mmdet.LoadImageFromNDArray'
    array_pipeline = Compose(array_cfg)
    arm = model.roi_head.r052_joint
    direct = ProposalObservationArms(arm.channels, arm.joint.num_classes, 'direct').to(device)
    direct.load_state_dict(arm.state_dict())
    all_rows = []
    # The permutation counterfactual is intentionally assembled across the
    # rank's entire frozen slice.  Per-image reversal is degenerate for
    # one-row images and is not the required cross-proposal intervention.
    direct_features, direct_sources, direct_uids = [], [], []
    for group_index in range(rank, len(groups), world):
        path, rows = groups[group_index]
        boxes = [r['decoded_pre_nms_box'] for r in rows]
        f, priors = build_feature(model, pipeline, path, boxes)
        f = f.detach().requires_grad_(True)
        labels = torch.tensor([r['class_id'] for r in rows], device=device)
        gt = torch.tensor([r['matched_gt_box'] for r in rows], device=device)
        target = _box_residual(gt, priors)
        source = priors[:, 4]
        uids = [r['proposal_uid'] for r in rows]
        out = arm(f, labels, target, gt[:, 4], source, uids)
        inf = arm.infer(f, source, uids)
        dfeat = f[:, 0].detach().requires_grad_(True)
        dout = direct(dfeat, labels, target, gt[:, 4], source, uids)
        dgrad = torch.autograd.grad((dout.q[:, 1].log() - dout.q[:, 0].log()).sum(), dfeat)[0].norm(dim=1)
        direct_features.append(dfeat.detach())
        direct_sources.append(source.detach())
        direct_uids.extend(uids)
        cyc = arm.infer(f.detach().roll(1, 1), source, uids)
        cyclic_l1 = (cyc.q - inf.q.roll(1, 1)).abs().sum(-1)
        # Physical ring-step rotation of image and decoded proposal is an
        # actual second detector pass, not a synthetic feature transform.
        image = cv2.imread(path)
        step = float(torch.pi / K)
        rotated_boxes, matrix = rotate_boxes(boxes, image.shape[0], image.shape[1], step)
        rotated_image = cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]), flags=cv2.INTER_LINEAR)
        rf, rpriors = build_feature(model, array_pipeline, path, rotated_boxes, image=rotated_image)
        rinf = arm.infer(rf, rpriors[:, 4], uids)
        geometry_q_l1 = (rinf.q - inf.q.detach()).abs().sum(-1)
        geometry_theta = axial_delta(rinf.angles[torch.arange(len(rows), device=device), labels] -
                                     (inf.angles.detach()[torch.arange(len(rows), device=device), labels] + step))
        cls = inf.marginal_class_log_probs[torch.arange(len(rows), device=device), labels]
        box = inf.box_residuals[torch.arange(len(rows), device=device), labels, 0]
        theta = inf.angles[torch.arange(len(rows), device=device), labels]
        cls_grad = torch.autograd.grad(cls.sum(), f, retain_graph=True)[0].norm(dim=(1, 2))
        box_grad = torch.autograd.grad(box.sum(), f, retain_graph=True)[0].norm(dim=(1, 2))
        theta_grad = torch.autograd.grad(theta.sum(), f, retain_graph=True)[0].norm(dim=(1, 2))
        normal_loss = joint_loss(out)
        arm.zero_grad(set_to_none=True); normal_loss.backward(retain_graph=True)
        normal_evidence_grad = arm.joint.posterior.weight.grad.norm().item()
        box_component_grads = arm.joint.box_loc_head.weight.grad.norm(dim=1).tolist()
        arm.zero_grad(set_to_none=True)
        detached_loss = -torch.logsumexp(out.q.detach().clamp_min(1e-12).log() + out.class_log_likelihood + out.box_log_likelihood + out.angle_log_likelihood, -1).mean()
        detached_loss.backward(retain_graph=True)
        detached_evidence_grad = 0. if arm.joint.posterior.weight.grad is None else arm.joint.posterior.weight.grad.norm().item()
        emb = arm.candidate_embeddings(f)
        shuffled = arm.joint(emb, labels, target, gt[:, 4], source,
                             out.logits.detach().roll(1, 0), uids)
        shin = arm.joint.infer(emb, source, uids, out.logits.detach().roll(1, 0))
        per_loss_change = ((-out.joint_log_likelihood) - (-shuffled.joint_log_likelihood)).abs()
        per_class_change = (inf.marginal_class_log_probs[torch.arange(len(rows), device=device), labels] - shin.marginal_class_log_probs[torch.arange(len(rows), device=device), labels]).abs()
        per_box_change = (inf.box_residuals[torch.arange(len(rows), device=device), labels, 0] - shin.box_residuals[torch.arange(len(rows), device=device), labels, 0]).abs()
        for i, row in enumerate(rows):
            all_rows.append(dict(proposal_uid=row['proposal_uid'], direct_grad=float(dgrad[i]),
              candidate_var=float(f[i].var(0).mean()), cyclic_l1=float(cyclic_l1[i]), geometry_q_l1=float(geometry_q_l1[i]),
              geometry_theta=float(geometry_theta[i]), cls_grad=float(cls_grad[i]), box_grad=float(box_grad[i]), theta_grad=float(theta_grad[i]),
              shuffle_loss=float(per_loss_change[i]), shuffle_class=float(per_class_change[i]), shuffle_box=float(per_box_change[i]),
              finite=all(finite(z) for z in (out.joint_log_likelihood[i], inf.q[i], inf.native_risk[i], cls_grad[i], box_grad[i], theta_grad[i])),
              normal_loss=float(normal_loss.detach()), detached_loss=float(detached_loss.detach()), normal_evidence_grad=normal_evidence_grad,
              box_component_grads=[float(x) for x in box_component_grads], detached_evidence_grad=detached_evidence_grad))
    dfeat_all = torch.cat(direct_features, dim=0)
    source_all = torch.cat(direct_sources, dim=0)
    base_q = direct.infer(dfeat_all, source_all, direct_uids).q.detach()
    perm = torch.arange(len(dfeat_all) - 1, -1, -1, device=device)
    perm_uids = [direct_uids[int(i)] for i in perm]
    perm_q = direct.infer(dfeat_all[perm], source_all, perm_uids).q[perm.argsort()]
    direct_l1 = (base_q - perm_q).abs().sum(-1)
    if len(all_rows) != len(direct_l1):
        raise RuntimeError('dynamic G1 direct permutation lineage mismatch')
    for row, l1 in zip(all_rows, direct_l1.tolist()):
        row['direct_l1'] = float(l1)
    outdir = BASE / 'dynamic_g1'; outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f'rank{rank}.json').write_text(json.dumps(all_rows) + '\n')
    dist.barrier(); dist.destroy_process_group()


if __name__ == '__main__': main()

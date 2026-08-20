"""Equal-budget non-PEF controls retained outside the PEF evidence path."""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn
from mmrotate.registry import MODELS
from mmrotate.models.dense_heads.angle_branch_retina_head import AngleBranchRetinaHead


@MODELS.register_module()
class DirectDistributionAngleBranchRetinaHead(AngleBranchRetinaHead):
    """AQE/O2-like direct periodic distribution control; no resampling grid."""
    def _init_layers(self):
        super()._init_layers()
        self.direct_distribution = nn.Conv2d(self.feat_channels, self.num_anchors * 12, 3, padding=1)

    def forward_single(self, x):
        cls, bbox, angle = super().forward_single(x)
        return cls, bbox, angle, self.direct_distribution(x)

    def loss_by_feat(self, cls, bbox, angle, direct, batch_gt_instances, batch_img_metas,
                     batch_gt_instances_ignore=None):
        base = super().loss_by_feat(cls, bbox, angle, batch_gt_instances, batch_img_metas,
                                    batch_gt_instances_ignore)
        sizes = [x.shape[-2:] for x in cls]
        anchors, flags = self.get_anchors(sizes, batch_img_metas, device=cls[0].device)
        targets = self.get_targets(anchors, flags, batch_gt_instances, batch_img_metas,
                                   batch_gt_instances_ignore=batch_gt_instances_ignore)
        angle_targets, weights = targets[-2:]
        bins = torch.arange(12, device=cls[0].device, dtype=cls[0].dtype) * (torch.pi / 12)
        losses = []
        for out, target, weight in zip(direct, angle_targets, weights):
            b, _, h, w = out.shape; a = target.shape[1] // (h * w)
            gt = self.angle_coder.decode(target.reshape(-1, self.encode_size)).reshape(b, h, w, a)
            idx = (.5 * torch.atan2(torch.sin(2 * (gt[..., None] - bins)), torch.cos(2 * (gt[..., None] - bins))).abs()).argmin(-1)
            logits = out.reshape(b, a, 12, h, w).permute(0, 3, 4, 1, 2).reshape(-1, 12)
            ce = F.cross_entropy(logits, idx.reshape(-1), reduction='none').reshape_as(weight[..., 0])
            losses.append((ce * weight[..., 0]).sum() / weight[..., 0].sum().clamp_min(1))
        base['loss_direct_dist'] = [x * .15 for x in losses]
        return base

    def predict_by_feat(self, cls, bbox, angle, direct, **kwargs):
        return super().predict_by_feat(cls, bbox, angle, **kwargs)


@MODELS.register_module()
class ScalarQualityAngleBranchRetinaHead(AngleBranchRetinaHead):
    """PQA-like scalar-quality control; explicitly not a PEF energy field."""
    def _init_layers(self):
        super()._init_layers()
        self.scalar_quality = nn.Conv2d(self.feat_channels, self.num_anchors, 3, padding=1)

    def forward_single(self, x):
        cls, bbox, angle = super().forward_single(x)
        return cls, bbox, angle, self.scalar_quality(x)

    def loss_by_feat(self, cls, bbox, angle, scalar, batch_gt_instances, batch_img_metas,
                     batch_gt_instances_ignore=None):
        base = super().loss_by_feat(cls, bbox, angle, batch_gt_instances, batch_img_metas,
                                    batch_gt_instances_ignore)
        sizes = [x.shape[-2:] for x in cls]
        anchors, flags = self.get_anchors(sizes, batch_img_metas, device=cls[0].device)
        targets = self.get_targets(anchors, flags, batch_gt_instances, batch_img_metas,
                                   batch_gt_instances_ignore=batch_gt_instances_ignore)
        angle_targets, weights = targets[-2:]
        losses = []
        for pred, target, weight, out in zip(angle, angle_targets, weights, scalar):
            b, _, h, w = out.shape; a = out.shape[1]
            native = self.angle_coder.decode(pred.permute(0, 2, 3, 1).reshape(-1, self.encode_size)).reshape(b, h, w, a)
            gt = self.angle_coder.decode(target.reshape(-1, self.encode_size)).reshape(b, h, w, a)
            harm = (.5 * torch.atan2(torch.sin(2 * (gt - native)), torch.cos(2 * (gt - native))).abs() / (torch.pi / 2)).detach()
            bce = F.binary_cross_entropy_with_logits(out.permute(0, 2, 3, 1), harm, reduction='none')
            losses.append((bce * weight[..., 0].reshape_as(bce)).sum() / weight[..., 0].sum().clamp_min(1))
        base['loss_scalar_quality'] = [x * .15 for x in losses]
        return base

    def predict_by_feat(self, cls, bbox, angle, scalar, **kwargs):
        return super().predict_by_feat(cls, bbox, angle, **kwargs)

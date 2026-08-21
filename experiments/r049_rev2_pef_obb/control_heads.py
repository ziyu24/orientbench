"""Equal-budget non-PEF controls retained outside the PEF evidence path."""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn
from mmrotate.registry import MODELS
from mmrotate.models.dense_heads.angle_branch_retina_head import AngleBranchRetinaHead


@MODELS.register_module()
class DirectDistributionAngleBranchRetinaHead(AngleBranchRetinaHead):
    """AQE/O2-like residual periodic distribution control; no resampling grid.

    The host angle remains the zero-residual reference.  This is necessary
    because an untrained absolute circular distribution has an undefined mean
    and would replace every host angle with an arbitrary numerical direction.
    ``direct_distribution`` is still an operative distribution at inference;
    it predicts the axial correction rather than being an auxiliary-only loss.
    """
    def _init_layers(self):
        super()._init_layers()
        self.direct_distribution = nn.Conv2d(self.feat_channels, self.num_anchors * 12, 3, padding=1)
        # A uniform residual q means an exactly zero correction at admission,
        # preserving host parity before the equal-budget branch learns.
        nn.init.zeros_(self.direct_distribution.weight)
        nn.init.zeros_(self.direct_distribution.bias)

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
        for pred, out, target, weight in zip(angle, direct, angle_targets, weights):
            b, _, h, w = out.shape; a = target.shape[1] // (h * w)
            gt = self.angle_coder.decode(target.reshape(-1, self.encode_size)).reshape(b, h, w, a)
            native = self.angle_coder.decode(
                pred.permute(0, 2, 3, 1).reshape(-1, self.encode_size)
            ).reshape(b, h, w, a).detach()
            residual = .5 * torch.atan2(
                torch.sin(2 * (gt - native)), torch.cos(2 * (gt - native)))
            idx = (.5 * torch.atan2(
                torch.sin(2 * (residual[..., None] - bins)),
                torch.cos(2 * (residual[..., None] - bins))).abs()).argmin(-1)
            logits = out.reshape(b, a, 12, h, w).permute(0, 3, 4, 1, 2).reshape(-1, 12)
            ce = F.cross_entropy(logits, idx.reshape(-1), reduction='none').reshape_as(weight[..., 0])
            losses.append((ce * weight[..., 0]).sum() / weight[..., 0].sum().clamp_min(1))
        base['loss_direct_dist'] = [x * .15 for x in losses]
        return base

    def predict_by_feat(self, cls, bbox, angle, direct, **kwargs):
        # Equal-budget direct distribution is an operative angle inference
        # baseline, not merely an auxiliary training loss.
        refined_codes = []
        bins = torch.arange(12, device=cls[0].device, dtype=cls[0].dtype) * (torch.pi / 12)
        for native_code, logits in zip(angle, direct):
            b, _, h, w = logits.shape
            q = logits.reshape(b, self.num_anchors, 12, h, w).softmax(2)
            sin = (q * torch.sin(2 * bins).view(1, 1, -1, 1, 1)).sum(2)
            cos = (q * torch.cos(2 * bins).view(1, 1, -1, 1, 1)).sum(2)
            # The circular mean of an exactly uniform q is undefined.  Treat
            # it as the no-correction identity, not an arbitrary atan2 angle.
            concentration = torch.hypot(sin, cos)
            residual = .5 * torch.atan2(sin, cos)
            residual = torch.where(concentration > 1e-6, residual, torch.zeros_like(residual))
            native = self.angle_coder.decode(
                native_code.permute(0, 2, 3, 1).reshape(-1, self.encode_size)
            ).reshape(b, h, w, self.num_anchors)
            theta = native + residual.permute(0, 2, 3, 1)
            code = self.angle_coder.encode(theta.reshape(-1, 1))
            code = code.reshape(b, self.num_anchors, h, w, self.encode_size).permute(0, 1, 4, 2, 3)
            refined_codes.append(code.reshape(b, self.num_anchors * self.encode_size, h, w))
        return super().predict_by_feat(cls, bbox, refined_codes, **kwargs)


@MODELS.register_module()
class ScalarQualityAngleBranchRetinaHead(AngleBranchRetinaHead):
    """PQA-like scalar-quality control; explicitly not a PEF energy field."""
    def _init_layers(self):
        super()._init_layers()
        self.scalar_quality = nn.Conv2d(self.feat_channels, self.num_anchors, 3, padding=1)

    def init_weights(self):
        super().init_weights()
        # ``-scalar_quality`` is passed through the detector's sigmoid score
        # factor.  A zero/random scalar field halves or suppresses otherwise
        # valid host detections before this equal-budget control has trained.
        # Start as an identity quality factor (sigmoid(6) ~= .9975), while the
        # scalar BCE target remains the same learned angular-harm quantity.
        nn.init.zeros_(self.scalar_quality.weight)
        nn.init.constant_(self.scalar_quality.bias, -6.)

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
        # The scalar head predicts angular harm.  Its negative logit is a
        # detection quality factor at inference, giving a real PQA-like
        # ranking baseline while retaining the host angle decoder.
        return super().predict_by_feat(cls, bbox, angle, score_factors=[-x for x in scalar], **kwargs)

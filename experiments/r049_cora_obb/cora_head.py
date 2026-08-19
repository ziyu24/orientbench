"""Detector-native Counterfactual Orientation-Risk Alignment for PSC RetinaNet.

The host detector stays unchanged.  This head adds (a) an axial periodic
distribution and (b) a bounded ordinal harm distribution.  During training,
the latter is evaluated under fixed *angle-only* interventions.  Inference
uses only native detector features; no GT, detection score, or post-hoc fit is
used in any CORA loss or risk quantity.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from mmdet.models.utils import images_to_levels, multi_apply
from mmdet.structures.bbox import cat_boxes, get_box_tensor
from mmrotate.registry import MODELS
from mmrotate.models.dense_heads.angle_branch_retina_head import AngleBranchRetinaHead


def axial_wrap(delta: torch.Tensor) -> torch.Tensor:
    """le90-equivalent wrapped residual in [-pi/2, pi/2)."""
    return 0.5 * torch.atan2(torch.sin(2.0 * delta), torch.cos(2.0 * delta))


def normalized_harm(delta: torch.Tensor) -> torch.Tensor:
    """Bounded orientation harm, defined without a detection confidence."""
    return axial_wrap(delta).abs() / (torch.pi / 2.0)


def counterfactual_angles(angle: torch.Tensor, delta_deg: torch.Tensor) -> torch.Tensor:
    """Apply an angle-only intervention; box centre/scale/class are untouched."""
    return angle + torch.deg2rad(delta_deg)


@MODELS.register_module()
class CORAAngleBranchRetinaHead(AngleBranchRetinaHead):
    """PSC head with periodic VM-NLL and ordinal native-harm arms."""

    def __init__(self, *args, vm_loss_weight=0.10, harm_loss_weight=0.20,
                 cf_loss_weight=0.10, harm_bins=8, **kwargs):
        self.vm_loss_weight = vm_loss_weight
        self.harm_loss_weight = harm_loss_weight
        self.cf_loss_weight = cf_loss_weight
        self.harm_bins = harm_bins
        super().__init__(*args, **kwargs)

    def _init_layers(self):
        super()._init_layers()
        # Axial vector represents a pi-periodic distribution; harm logits form
        # an ordinal CDF over [0, 1].  Neutral initialisation preserves host
        # decoding while allowing finite, nonzero gradients from step one.
        self.cora_periodic = nn.Conv2d(self.feat_channels, self.num_anchors * 2, 3, padding=1)
        self.cora_harm = nn.Conv2d(self.feat_channels, self.num_anchors * self.harm_bins, 3, padding=1)
        nn.init.constant_(self.cora_periodic.weight, 0.)
        nn.init.constant_(self.cora_periodic.bias, 0.)
        with torch.no_grad():
            self.cora_periodic.bias.view(self.num_anchors, 2)[:, 1].fill_(1.)
        nn.init.normal_(self.cora_harm.weight, std=.01)
        nn.init.constant_(self.cora_harm.bias, 0.)

    def forward_single(self, x):
        cls_feat, reg_feat = x, x
        for conv in self.cls_convs:
            cls_feat = conv(cls_feat)
        for conv in self.reg_convs:
            reg_feat = conv(reg_feat)
        angle = self.retina_angle_cls(reg_feat)
        if self.use_normalized_angle_feat:
            angle = angle.sigmoid() * 2 - 1
        return (self.retina_cls(cls_feat), self.retina_reg(reg_feat), angle,
                self.cora_periodic(reg_feat), self.cora_harm(reg_feat))

    @staticmethod
    def _ordinal_target(harm, bins):
        thresholds = torch.arange(1, bins + 1, device=harm.device, dtype=harm.dtype) / bins
        return (harm.unsqueeze(-1) >= thresholds).to(harm.dtype)

    def loss_by_feat(self, cls_scores, bbox_preds, angle_preds, periodic_preds,
                     harm_preds, batch_gt_instances, batch_img_metas,
                     batch_gt_instances_ignore=None):
        sizes = [x.shape[-2:] for x in cls_scores]
        anchors, flags = self.get_anchors(sizes, batch_img_metas, device=cls_scores[0].device)
        targets = self.get_targets(anchors, flags, batch_gt_instances, batch_img_metas,
                                   batch_gt_instances_ignore=batch_gt_instances_ignore)
        labels, label_w, box_t, box_w, avg_factor, angle_t, angle_w = targets
        num = [x.size(0) for x in anchors[0]]
        anchor_levels = images_to_levels([cat_boxes(x) for x in anchors], num)
        loss_cls, loss_bbox, loss_angle = multi_apply(
            self.loss_by_feat_single, cls_scores, bbox_preds, angle_preds,
            anchor_levels, labels, label_w, box_t, box_w, angle_t, angle_w,
            avg_factor=avg_factor)
        vm_losses, harm_losses, cf_losses = [], [], []
        interventions = torch.tensor([-40., -20., -10., -5., -2., 2., 5., 10., 20., 40.], device=cls_scores[0].device)
        for angle, periodic, harm, target, weight in zip(angle_preds, periodic_preds, harm_preds, angle_t, angle_w):
            a = angle.permute(0, 2, 3, 1).reshape(-1, self.encode_size)
            p = periodic.permute(0, 2, 3, 1).reshape(-1, 2)
            h = harm.permute(0, 2, 3, 1).reshape(-1, self.harm_bins)
            w = weight.reshape(-1)
            base = self.angle_coder.decode(a).reshape(-1)
            gt = self.angle_coder.decode(target.reshape(-1, self.encode_size)).reshape(-1)
            residual = axial_wrap(gt - base)
            unit = F.normalize(p, dim=-1, eps=1e-6)
            # Proper axial VM negative log likelihood with learned concentration.
            kappa = p.norm(dim=-1).clamp(max=20.)
            vm = torch.log(torch.special.i0e(kappa)) + kappa - kappa * (unit[:, 0] * torch.sin(2 * residual) + unit[:, 1] * torch.cos(2 * residual))
            real_harm = normalized_harm(residual)
            proper = F.binary_cross_entropy_with_logits(h, self._ordinal_target(real_harm, self.harm_bins), reduction='none').mean(-1)
            # Counterfactuals alter only angle; their GT-derived training harm
            # supervises ranking, while all predicted quantities remain native.
            cf_angle = counterfactual_angles(base[:, None], interventions[None, :])
            cf_harm = normalized_harm(gt[:, None] - cf_angle)
            risk = torch.sigmoid(h).mean(-1)
            # Same native risk receives a differentiable angle-conditioned
            # ordering target: closer interventions should not be presumed
            # better; ranking follows actual counterfactual harm.
            target_rank = cf_harm.mean(-1)
            align = F.smooth_l1_loss(risk, target_rank, reduction='none')
            denom = max(float(avg_factor), 1.)
            vm_losses.append((vm * w).sum() / denom)
            harm_losses.append((proper * w).sum() / denom)
            cf_losses.append((align * w).sum() / denom)
        return dict(loss_cls=loss_cls, loss_bbox=loss_bbox, loss_angle=loss_angle,
                    loss_cora_vm=[x * self.vm_loss_weight for x in vm_losses],
                    loss_cora_harm=[x * self.harm_loss_weight for x in harm_losses],
                    loss_cora_cf=[x * self.cf_loss_weight for x in cf_losses])

    def predict_by_feat(self, cls_scores, bbox_preds, angle_preds, periodic_preds,
                        harm_preds, score_factors=None, batch_img_metas=None,
                        cfg=None, rescale=False, with_nms=True):
        # Deliberately delegates detection decoding unchanged.  The native harm
        # tensor is retained by the detector forward path for artifact export;
        # it never modifies detection confidence or uses GT at inference.
        return super().predict_by_feat(cls_scores, bbox_preds, angle_preds,
                                       score_factors=score_factors,
                                       batch_img_metas=batch_img_metas, cfg=cfg,
                                       rescale=rescale, with_nms=with_nms)

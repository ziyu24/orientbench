"""Detector-native Counterfactual Orientation-Risk Alignment for PSC RetinaNet.

The host detector stays unchanged.  This head adds (a) an axial periodic
distribution and (b) a bounded ordinal harm distribution.  During training,
the latter is evaluated under fixed *angle-only* interventions.  Inference
uses only native detector features; no GT, detection score, or post-hoc fit is
used in any CORA loss or risk quantity.
"""
from __future__ import annotations

import copy

import torch
import torch.nn as nn
import torch.nn.functional as F
from mmengine.structures import InstanceData
from mmdet.models.utils import (filter_scores_and_topk, images_to_levels,
                                multi_apply, select_single_mlvl)
from mmdet.structures.bbox import cat_boxes
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


def counterfactual_harm_logits(base_logits: torch.Tensor, angle_slope: torch.Tensor,
                               delta_deg: torch.Tensor) -> torch.Tensor:
    """Native angle-conditioned ordinal harm logits for fixed interventions.

    ``base_logits`` and ``angle_slope`` come from the same positive-anchor
    feature.  Only the supplied angular intervention varies; no box geometry,
    class score, GT quantity, or detector score is an input here.
    """
    return base_logits[:, None, :] + angle_slope[:, None, None] * (delta_deg[None, :, None] / 40.0)


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
        self.cora_cf_slope = nn.Conv2d(self.feat_channels, self.num_anchors, 3, padding=1)
        nn.init.constant_(self.cora_periodic.weight, 0.)
        nn.init.constant_(self.cora_periodic.bias, 0.)
        with torch.no_grad():
            self.cora_periodic.bias.view(self.num_anchors, 2)[:, 1].fill_(1.)
        nn.init.normal_(self.cora_harm.weight, std=.01)
        nn.init.constant_(self.cora_harm.bias, 0.)
        nn.init.normal_(self.cora_cf_slope.weight, std=.01)
        nn.init.constant_(self.cora_cf_slope.bias, 0.)

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
                self.cora_periodic(reg_feat), self.cora_harm(reg_feat),
                self.cora_cf_slope(reg_feat))

    @staticmethod
    def _ordinal_target(harm, bins):
        thresholds = torch.arange(1, bins + 1, device=harm.device, dtype=harm.dtype) / bins
        return (harm.unsqueeze(-1) >= thresholds).to(harm.dtype)

    def loss_by_feat(self, cls_scores, bbox_preds, angle_preds, periodic_preds,
                     harm_preds, cf_slope_preds, batch_gt_instances, batch_img_metas,
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
        for angle, periodic, harm, cf_slope, target, weight in zip(
                angle_preds, periodic_preds, harm_preds, cf_slope_preds, angle_t, angle_w):
            a = angle.permute(0, 2, 3, 1).reshape(-1, self.encode_size)
            p = periodic.permute(0, 2, 3, 1).reshape(-1, 2)
            h = harm.permute(0, 2, 3, 1).reshape(-1, self.harm_bins)
            s = cf_slope.permute(0, 2, 3, 1).reshape(-1)
            w = weight.reshape(-1)
            base = self.angle_coder.decode(a).reshape(-1)
            gt = self.angle_coder.decode(target.reshape(-1, self.encode_size)).reshape(-1)
            residual = axial_wrap(gt - base)
            # ``F.normalize`` can create an AMP-overflowing derivative close
            # to a zero axial vector.  The explicit epsilon is part of the
            # frozen numerical parameterisation, not a loss-weight change.
            squared_norm = p.square().sum(-1, keepdim=True)
            unit = p / torch.sqrt(squared_norm + 1e-4)
            # Proper axial VM negative log likelihood with learned concentration.
            kappa = torch.sqrt(squared_norm.squeeze(-1) + 1e-4).clamp(max=20.)
            vm = torch.log(torch.special.i0e(kappa)) + kappa - kappa * (unit[:, 0] * torch.sin(2 * residual) + unit[:, 1] * torch.cos(2 * residual))
            real_harm = normalized_harm(residual)
            proper = F.binary_cross_entropy_with_logits(h, self._ordinal_target(real_harm, self.harm_bins), reduction='none').mean(-1)
            # Counterfactuals alter only angle.  The same native feature has a
            # learned angle response, and GT appears solely in this train loss.
            cf_angle = counterfactual_angles(base[:, None], interventions[None, :])
            cf_harm = normalized_harm(gt[:, None] - cf_angle)
            cf_logits = counterfactual_harm_logits(h, s, interventions)
            cf_target = self._ordinal_target(cf_harm.reshape(-1), self.harm_bins).reshape_as(cf_logits)
            cf_proper = F.binary_cross_entropy_with_logits(cf_logits, cf_target, reduction='none').mean((-1, -2))
            cf_risk = torch.sigmoid(cf_logits).mean(-1)
            # Ordering follows the actual GT harm, not intervention magnitude.
            pred_diff = cf_risk[:, :, None] - cf_risk[:, None, :]
            true_diff = cf_harm[:, :, None] - cf_harm[:, None, :]
            pair_mask = true_diff.ne(0)
            pair_target = (true_diff > 0).to(pred_diff.dtype)
            pair = F.binary_cross_entropy_with_logits(pred_diff, pair_target, reduction='none')
            pair = (pair * pair_mask).sum((-1, -2)) / pair_mask.sum((-1, -2)).clamp_min(1)
            align = cf_proper + pair
            denom = max(float(avg_factor), 1.)
            vm_losses.append((vm * w).sum() / denom)
            harm_losses.append((proper * w).sum() / denom)
            cf_losses.append((align * w).sum() / denom)
        return dict(loss_cls=loss_cls, loss_bbox=loss_bbox, loss_angle=loss_angle,
                    loss_cora_vm=[x * self.vm_loss_weight for x in vm_losses],
                    loss_cora_harm=[x * self.harm_loss_weight for x in harm_losses],
                    loss_cora_cf=[x * self.cf_loss_weight for x in cf_losses])

    def predict_by_feat(self, cls_scores, bbox_preds, angle_preds, periodic_preds,
                        harm_preds, cf_slope_preds, score_factors=None, batch_img_metas=None,
                        cfg=None, rescale=False, with_nms=True):
        if score_factors is not None:
            raise NotImplementedError('PSC host does not use score factors')
        priors = self.prior_generator.grid_priors(
            [x.shape[-2:] for x in cls_scores], dtype=cls_scores[0].dtype,
            device=cls_scores[0].device)
        results = []
        for image_id, meta in enumerate(batch_img_metas):
            results.append(self._predict_cora_single(
                select_single_mlvl(cls_scores, image_id, detach=True),
                select_single_mlvl(bbox_preds, image_id, detach=True),
                select_single_mlvl(angle_preds, image_id, detach=True),
                select_single_mlvl(harm_preds, image_id, detach=True), priors,
                meta, cfg, rescale, with_nms))
        return results

    def _predict_cora_single(self, cls_list, bbox_list, angle_list, harm_list,
                             priors_list, img_meta, cfg, rescale, with_nms):
        """Decode host boxes unchanged and attach only native CDF risk."""
        cfg = copy.deepcopy(self.test_cfg if cfg is None else cfg)
        boxes_all, scores_all, labels_all, risks_all = [], [], [], []
        for cls, bbox, angle, harm, priors in zip(
                cls_list, bbox_list, angle_list, harm_list, priors_list):
            bbox = bbox.float().permute(1, 2, 0).reshape(-1, self.bbox_coder.encode_size)
            angle = angle.permute(1, 2, 0).reshape(-1, self.encode_size)
            harm = harm.permute(1, 2, 0).reshape(-1, self.harm_bins)
            scores = cls.float().permute(1, 2, 0).reshape(-1, self.cls_out_channels).sigmoid()
            scores, labels, keep, kept = filter_scores_and_topk(
                scores, cfg.get('score_thr', 0), cfg.get('nms_pre', -1),
                dict(bbox_pred=bbox, priors=priors, angle_pred=angle, harm=harm))
            bbox, priors, angle, harm = (kept['bbox_pred'], kept['priors'],
                                         kept['angle_pred'], kept['harm'])
            # This is the original PSC decode: CORA risk does not change it.
            bbox[..., -1] = self.angle_coder.decode(angle)
            boxes_all.append(self.bbox_coder.decode(priors, bbox, max_shape=img_meta['img_shape']))
            scores_all.append(scores)
            labels_all.append(labels)
            risks_all.append(torch.sigmoid(harm).mean(-1))
        result = InstanceData(bboxes=cat_boxes(boxes_all), scores=torch.cat(scores_all),
                              labels=torch.cat(labels_all), cora_native_risk=torch.cat(risks_all))
        return self._bbox_post_process(result, cfg, rescale, with_nms, img_meta)

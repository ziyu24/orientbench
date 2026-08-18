"""SAUR-OBB: an in-head axial residual distribution for PSC RetinaNet.

The branch is deliberately independent of the detector classification score.
It predicts an axial residual direction (sin(2d), cos(2d)) and a positive
concentration.  A continuous geometry gate suppresses spurious certainty for
near-square boxes.  Only image features and decoded detector boxes are used at
inference; ground truth is used solely by the training loss.
"""

import copy
from typing import List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from mmengine.structures import InstanceData
from mmdet.models.utils import filter_scores_and_topk, images_to_levels, multi_apply, select_single_mlvl
from mmdet.structures.bbox import cat_boxes, get_box_tensor

from mmrotate.registry import MODELS
from mmrotate.models.dense_heads.angle_branch_retina_head import AngleBranchRetinaHead


def axial_wrap(delta: torch.Tensor) -> torch.Tensor:
    """Map an angle difference to [-pi/2, pi/2), respecting OBB symmetry."""
    return .5 * torch.atan2(torch.sin(2.0 * delta), torch.cos(2.0 * delta))


def geometry_identifiability(width: torch.Tensor, height: torch.Tensor,
                             slope: float = 4.0, center: float = .25) -> torch.Tensor:
    """Continuous symmetry gate: zero-ish for squares, one-ish when elongated."""
    ratio = torch.log((width.abs() + 1e-6) / (height.abs() + 1e-6)).abs()
    return torch.sigmoid(slope * (ratio - center))


@MODELS.register_module()
class SAURAngleBranchRetinaHead(AngleBranchRetinaHead):
    """PSC angle head augmented with a residual mean and concentration head."""

    def __init__(self, *args, saur_loss_weight: float = .25,
                 geometry_gate_slope: float = 4.0,
                 geometry_gate_center: float = .25, **kwargs):
        self.saur_loss_weight = saur_loss_weight
        self.geometry_gate_slope = geometry_gate_slope
        self.geometry_gate_center = geometry_gate_center
        super().__init__(*args, **kwargs)

    def _init_layers(self):
        super()._init_layers()
        # Per-anchor axial residual vector (sin(2d), cos(2d)) and log-kappa.
        self.saur_residual = nn.Conv2d(self.feat_channels, self.num_anchors * 2, 3, padding=1)
        self.saur_concentration = nn.Conv2d(self.feat_channels, self.num_anchors, 3, padding=1)
        nn.init.normal_(self.saur_residual.weight, std=.01)
        nn.init.constant_(self.saur_residual.bias, 0.)
        nn.init.normal_(self.saur_concentration.weight, std=.01)
        nn.init.constant_(self.saur_concentration.bias, -2.)

    def forward_single(self, x):
        cls_feat = x
        reg_feat = x
        for conv in self.cls_convs:
            cls_feat = conv(cls_feat)
        for conv in self.reg_convs:
            reg_feat = conv(reg_feat)
        cls_score = self.retina_cls(cls_feat)
        bbox_pred = self.retina_reg(reg_feat)
        angle_pred = self.retina_angle_cls(reg_feat)
        if self.use_normalized_angle_feat:
            angle_pred = angle_pred.sigmoid() * 2 - 1
        return (cls_score, bbox_pred, angle_pred,
                self.saur_residual(reg_feat), self.saur_concentration(reg_feat))

    def _decode_box_tensor(self, anchors, bbox_pred):
        return get_box_tensor(self.bbox_coder.decode(anchors, bbox_pred))

    def _saur_nll(self, angle_pred, residual_pred, concentration_pred,
                  anchors, bbox_targets, angle_weights, avg_factor):
        base = self.angle_coder.decode(angle_pred)
        target = self.angle_coder.decode(bbox_targets[..., -self.encode_size:]) if bbox_targets.size(-1) == self.encode_size else None
        # ``bbox_targets`` passed below is the encoded scalar box target, whose
        # final angle is the same scalar encoded by the PSC coder.
        if target is None:
            raise RuntimeError('SAUR requires PSC-compatible angle targets')
        boxes = self._decode_box_tensor(anchors, bbox_targets)
        gate = geometry_identifiability(boxes[:, 2], boxes[:, 3], self.geometry_gate_slope, self.geometry_gate_center)
        vec = residual_pred.reshape(-1, self.num_anchors, 2) if False else residual_pred
        raw_delta = .5 * torch.atan2(vec[:, 0], vec[:, 1])
        delta = gate * raw_delta
        kappa = F.softplus(concentration_pred) * gate + 1e-4
        residual_target = axial_wrap(target.reshape(-1) - base.reshape(-1))
        # Stable axial von-Mises NLL: log I0(kappa) - kappa cos(2 error).
        nll = (torch.log(torch.special.i0e(kappa)) + kappa
               - kappa * torch.cos(2.0 * axial_wrap(residual_target - delta)))
        weights = angle_weights.reshape(-1)
        return (nll * weights).sum() / max(float(avg_factor), 1.0)

    def loss_by_feat(self, cls_scores, bbox_preds, angle_preds, residual_preds,
                     concentration_preds, batch_gt_instances, batch_img_metas,
                     batch_gt_instances_ignore=None):
        featmap_sizes = [x.size()[-2:] for x in cls_scores]
        device = cls_scores[0].device
        anchor_list, valid_flag_list = self.get_anchors(featmap_sizes, batch_img_metas, device=device)
        targets = self.get_targets(anchor_list, valid_flag_list, batch_gt_instances,
                                   batch_img_metas, batch_gt_instances_ignore=batch_gt_instances_ignore)
        (labels_list, label_weights_list, bbox_targets_list, bbox_weights_list,
         avg_factor, angle_target_list, angle_weight_list) = targets
        num_level_anchors = [x.size(0) for x in anchor_list[0]]
        all_anchor_list = images_to_levels([cat_boxes(x) for x in anchor_list], num_level_anchors)
        loss_cls, loss_bbox, loss_angle = multi_apply(
            self.loss_by_feat_single, cls_scores, bbox_preds, angle_preds,
            all_anchor_list, labels_list, label_weights_list, bbox_targets_list,
            bbox_weights_list, angle_target_list, angle_weight_list, avg_factor=avg_factor)
        saur_losses = []
        for pred, residual, concentration, anchors, box_target, angle_target, angle_weight in zip(
                angle_preds, residual_preds, concentration_preds, all_anchor_list,
                bbox_targets_list, angle_target_list, angle_weight_list):
            ap = pred.permute(0, 2, 3, 1).reshape(-1, self.encode_size)
            rp = residual.permute(0, 2, 3, 1).reshape(-1, 2)
            cp = concentration.permute(0, 2, 3, 1).reshape(-1)
            # Decode target geometry from ordinary encoded box targets.  The
            # PSC target itself is supplied separately as angle_target.
            anchor_flat = anchors.reshape(-1, anchors.size(-1))
            bt = box_target.reshape(-1, box_target.size(-1))
            target_boxes = self._decode_box_tensor(anchor_flat, bt)
            gate = geometry_identifiability(target_boxes[:, 2], target_boxes[:, 3], self.geometry_gate_slope, self.geometry_gate_center)
            base = self.angle_coder.decode(ap)
            target = self.angle_coder.decode(angle_target.reshape(-1, self.encode_size))
            raw_delta = .5 * torch.atan2(rp[:, 0], rp[:, 1])
            kappa = F.softplus(cp) * gate + 1e-4
            error = axial_wrap(target - (base + gate * raw_delta))
            nll = torch.log(torch.special.i0e(kappa)) + kappa - kappa * torch.cos(2.0 * error)
            saur_losses.append((nll * angle_weight.reshape(-1)).sum() / max(float(avg_factor), 1.0))
        return dict(loss_cls=loss_cls, loss_bbox=loss_bbox, loss_angle=loss_angle,
                    loss_saur=[x * self.saur_loss_weight for x in saur_losses])

    def predict_by_feat(self, cls_scores: List, bbox_preds: List, angle_preds: List,
                        residual_preds: List, concentration_preds: List,
                        score_factors: Optional[List] = None, batch_img_metas: Optional[List[dict]] = None,
                        cfg=None, rescale=False, with_nms=True):
        if score_factors is not None:
            raise NotImplementedError('SAUR PSC host does not use score factors')
        priors = self.prior_generator.grid_priors([x.shape[-2:] for x in cls_scores], dtype=cls_scores[0].dtype, device=cls_scores[0].device)
        results = []
        for image_id, meta in enumerate(batch_img_metas):
            results.append(self._predict_saur_single(
                select_single_mlvl(cls_scores, image_id, detach=True),
                select_single_mlvl(bbox_preds, image_id, detach=True),
                select_single_mlvl(angle_preds, image_id, detach=True),
                select_single_mlvl(residual_preds, image_id, detach=True),
                select_single_mlvl(concentration_preds, image_id, detach=True), priors, meta, cfg, rescale, with_nms))
        return results

    def _predict_saur_single(self, cls_list, bbox_list, angle_list, residual_list,
                             concentration_list, priors_list, img_meta, cfg, rescale, with_nms):
        cfg = copy.deepcopy(self.test_cfg if cfg is None else cfg)
        boxes_all, scores_all, labels_all, rel_all = [], [], [], []
        for cls, bbox, angle, residual, concentration, priors in zip(cls_list, bbox_list, angle_list, residual_list, concentration_list, priors_list):
            bbox = bbox.float().permute(1, 2, 0).reshape(-1, self.bbox_coder.encode_size)
            angle = angle.permute(1, 2, 0).reshape(-1, self.encode_size)
            residual = residual.permute(1, 2, 0).reshape(-1, 2)
            concentration = concentration.permute(1, 2, 0).reshape(-1)
            scores = cls.float().permute(1, 2, 0).reshape(-1, self.cls_out_channels).sigmoid()
            scores, labels, keep, kept = filter_scores_and_topk(scores, cfg.get('score_thr', 0), cfg.get('nms_pre', -1), dict(bbox_pred=bbox, priors=priors))
            bbox, priors = kept['bbox_pred'], kept['priors']
            decoded = self._decode_box_tensor(priors, bbox)
            gate = geometry_identifiability(decoded[:, 2], decoded[:, 3], self.geometry_gate_slope, self.geometry_gate_center)
            delta = gate * .5 * torch.atan2(residual[keep, 0], residual[keep, 1])
            theta = axial_wrap(self.angle_coder.decode(angle[keep]) + delta)
            bbox[..., -1] = theta
            boxes_all.append(self.bbox_coder.decode(priors, bbox, max_shape=img_meta['img_shape']))
            scores_all.append(scores); labels_all.append(labels)
            rel_all.append(F.softplus(concentration[keep]) * gate)
        result = InstanceData(bboxes=cat_boxes(boxes_all), scores=torch.cat(scores_all), labels=torch.cat(labels_all), saur_concentration=torch.cat(rel_all))
        return self._bbox_post_process(result, cfg, rescale, with_nms, img_meta)

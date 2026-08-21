"""PSC RetinaNet head with a true candidate-conditioned PEF auxiliary field."""
from __future__ import annotations

import math
import torch
import torch.nn.functional as F
from mmrotate.registry import MODELS
from mmrotate.models.dense_heads.angle_branch_retina_head import AngleBranchRetinaHead
from .pef_field import PeriodicEvidenceField, axial_wrap


@MODELS.register_module()
class PEFAngleBranchRetinaHead(AngleBranchRetinaHead):
    """Keep PSC detection paths while learning a sampled axial evidence field.

    The host PSC decode remains a separately exported control during the smoke;
    ``pef_energy``/``pef_refined_angle``/``pef_native_risk`` are the PEF
    outputs.  No GT or score is consumed during PEF inference.
    """
    def __init__(self, *args, pef_candidates=12, pef_loss_weight=.15, **kwargs):
        self.pef_candidates = pef_candidates
        self.pef_loss_weight = pef_loss_weight
        super().__init__(*args, **kwargs)

    def _init_layers(self):
        super()._init_layers()
        self.pef = PeriodicEvidenceField(self.feat_channels, self.pef_candidates,
                                         num_classes=self.num_classes)

    def init_weights(self):
        super().init_weights()
        self.pef.init_identity()

    def forward_single(self, x):
        cls, bbox, angle = super().forward_single(x)
        return cls, bbox, angle

    def forward(self, feats):
        """Build the field against the fixed per-level candidate box.

        The detector's anchor generator supplies the centre/size template for
        every FPN location.  A candidate angle may rotate its sampling axes,
        but it cannot change that box; the semantic class is still the host
        detector's class head and neither its score nor GT enters the scorer.
        """
        outputs = []
        for level, x in enumerate(feats):
            cls, bbox, angle = super().forward_single(x)
            stride_x, stride_y = self.prior_generator.strides[level]
            anchors = self.prior_generator.base_anchors[level].to(x)
            sizes = torch.stack(((anchors[:, 2] - anchors[:, 0]).abs() / stride_x,
                                 (anchors[:, 3] - anchors[:, 1]).abs() / stride_y), 1)
            b, _, h, w = cls.shape
            class_ids = cls.reshape(b, self.num_anchors, self.num_classes, h, w).argmax(2)
            native = self.angle_coder.decode(
                angle.permute(0, 2, 3, 1).reshape(-1, self.encode_size)
            ).reshape(b, h, w, self.num_anchors).permute(0, 3, 1, 2)
            energy, residual, risk = self.pef(x, sizes, class_ids, native)
            refined = axial_wrap(native + residual)
            outputs.append((cls, bbox, angle, energy, refined, risk))
        return tuple(map(list, zip(*outputs)))

    def loss_by_feat(self, cls_scores, bbox_preds, angle_preds, pef_energies,
                     pef_angles, pef_risks, batch_gt_instances, batch_img_metas,
                     batch_gt_instances_ignore=None):
        base = super().loss_by_feat(cls_scores, bbox_preds, angle_preds,
                                    batch_gt_instances, batch_img_metas,
                                    batch_gt_instances_ignore)
        sizes = [x.shape[-2:] for x in cls_scores]
        anchors, flags = self.get_anchors(sizes, batch_img_metas, device=cls_scores[0].device)
        targets = self.get_targets(anchors, flags, batch_gt_instances, batch_img_metas,
                                   batch_gt_instances_ignore=batch_gt_instances_ignore)
        angle_targets, angle_weights = targets[-2:]
        losses = []
        candidate = self.pef.candidate_angles.to(cls_scores[0])
        for energy, target, weight in zip(pef_energies, angle_targets, angle_weights):
            b, a, k, h, w = energy.shape
            target = target.reshape(b, h, w, a, self.encode_size).permute(0, 3, 1, 2, 4)
            weight = weight.reshape(b, h, w, a).permute(0, 3, 1, 2).float()
            gt = self.angle_coder.decode(target.reshape(-1, self.encode_size)).reshape(b, a, h, w)
            native = self.angle_coder.decode(
                angle_preds[len(losses)].permute(0, 2, 3, 1).reshape(-1, self.encode_size)
            ).reshape(b, h, w, a).permute(0, 3, 1, 2).detach()
            residual_gt = axial_wrap(gt - native)
            d = axial_wrap(residual_gt.unsqueeze(2) - candidate.view(1, 1, -1, 1, 1)).abs()
            index = d.argmin(2)
            ce = F.cross_entropy(energy.permute(0, 1, 3, 4, 2).reshape(-1, k), index.reshape(-1), reduction='none').reshape_as(weight)
            losses.append((ce * weight).sum() / weight.sum().clamp_min(1.))
        base['loss_pef'] = [x * self.pef_loss_weight for x in losses]
        return base

    def predict_by_feat(self, cls_scores, bbox_preds, angle_preds, pef_energies,
                        pef_angles, pef_risks, **kwargs):
        # Replace only the decoded orientation with the candidate-evidence
        # circular estimate.  Class score and box geometry are untouched and
        # risk is never score-fused.  One location-level evidence field is
        # shared over its anchor templates, matching the FPN sampling site.
        refined_codes = []
        for refined in pef_angles:
            b, a, h, w = refined.shape
            code = self.angle_coder.encode(refined.reshape(-1, 1))
            code = code.reshape(b, a, h, w, self.encode_size).permute(0, 1, 4, 2, 3)
            refined_codes.append(code.reshape(b, a * self.encode_size, h, w))
        results = super().predict_by_feat(cls_scores, bbox_preds, refined_codes, **kwargs)
        # Preserve no-GT per-candidate evidence for every final detection.
        # NMS keeps arbitrary InstanceData fields, so q/risk are available to
        # the persisted prediction exporter without score fusion.
        for image_id, result in enumerate(results):
            if len(result) == 0:
                result.pef_q = cls_scores[0].new_empty((0, self.pef_candidates))
                result.pef_native_risk = cls_scores[0].new_empty((0,))
                result.pef_original_angle = cls_scores[0].new_empty((0,))
                result.pef_refined_angle = cls_scores[0].new_empty((0,))
                continue
            boxes = result.bboxes.tensor if hasattr(result.bboxes, 'tensor') else result.bboxes
            side = (boxes[:, 2].abs() * boxes[:, 3].abs()).sqrt().clamp_min(1.)
            level_sizes = boxes.new_tensor([
                math.sqrt(float(((a[:, 2] - a[:, 0]).abs() * (a[:, 3] - a[:, 1]).abs()).mean()))
                for a in self.prior_generator.base_anchors])
            level_ids = (side[:, None].log() - level_sizes.log()[None]).abs().argmin(1)
            qs, risks, originals = [], [], []
            for det_id, level in enumerate(level_ids.tolist()):
                stride_x, stride_y = self.prior_generator.strides[level]
                h, w = pef_risks[level].shape[-2:]
                ix = int((boxes[det_id, 0] / stride_x - .5).round().clamp(0, w - 1).item())
                iy = int((boxes[det_id, 1] / stride_y - .5).round().clamp(0, h - 1).item())
                anchors = self.prior_generator.base_anchors[level].to(boxes)
                aw = (anchors[:, 2] - anchors[:, 0]).abs()
                ah = (anchors[:, 3] - anchors[:, 1]).abs()
                aspect = (boxes[det_id, 2].abs() / boxes[det_id, 3].abs().clamp_min(1e-6)).log()
                anchor_id = ((aw / ah).log() - aspect).abs().argmin()
                energy = pef_energies[level][image_id, anchor_id, :, iy, ix]
                qs.append(energy.softmax(0))
                risks.append(pef_risks[level][image_id, anchor_id, iy, ix])
                raw = angle_preds[level][image_id].reshape(self.num_anchors, self.encode_size, h, w)
                originals.append(self.angle_coder.decode(raw[anchor_id, :, iy, ix].reshape(1, -1)).reshape(()))
            result.pef_q = torch.stack(qs)
            result.pef_native_risk = torch.stack(risks)
            result.pef_original_angle = torch.stack(originals)
            result.pef_refined_angle = boxes[:, 4]
        return results

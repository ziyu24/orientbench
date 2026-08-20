"""PSC RetinaNet head with a true candidate-conditioned PEF auxiliary field."""
from __future__ import annotations

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
        self.pef = PeriodicEvidenceField(self.feat_channels, self.pef_candidates)

    def forward_single(self, x):
        cls, bbox, angle = super().forward_single(x)
        energy, refined, risk = self.pef(x)
        return cls, bbox, angle, energy, refined, risk

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
            anchor = self.prior_generator.base_anchors[level][0].to(x)
            stride_x, stride_y = self.prior_generator.strides[level]
            box_size = x.new_tensor(((anchor[2] - anchor[0]).abs() / stride_x,
                                     (anchor[3] - anchor[1]).abs() / stride_y))
            energy, refined, risk = self.pef(x, box_size)
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
            # MMRotate target lists are (batch, locations, encode_size),
            # whereas the candidate field is one shared visual sample per
            # spatial location.  Retain the supervised anchor with maximal
            # angle weight at each location; anchor identity never enters PEF.
            b, _, h, w = energy.shape
            anchors_per_loc = target.shape[1] // (h * w)
            target = target.reshape(b, h, w, anchors_per_loc, self.encode_size)
            weight = weight.reshape(b, h, w, anchors_per_loc)
            chosen = weight.argmax(-1, keepdim=True)
            target = target.gather(3, chosen[..., None].expand(-1, -1, -1, -1, self.encode_size)).squeeze(3)
            w = weight.gather(3, chosen).squeeze(3).float()
            gt = self.angle_coder.decode(target.reshape(-1, self.encode_size)).reshape_as(energy[:, 0])
            d = axial_wrap(gt.unsqueeze(1) - candidate.view(1, -1, 1, 1)).abs()
            index = d.argmin(1)
            ce = F.cross_entropy(energy, index, reduction='none')
            losses.append((ce * w).sum() / w.sum().clamp_min(1.))
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
            b, h, w = refined.shape
            code = self.angle_coder.encode(refined.reshape(-1, 1))
            code = code.reshape(b, h, w, self.encode_size).permute(0, 3, 1, 2)
            code = code.unsqueeze(1).expand(-1, self.num_anchors, -1, -1, -1)
            refined_codes.append(code.reshape(b, self.num_anchors * self.encode_size, h, w))
        return super().predict_by_feat(cls_scores, bbox_preds, refined_codes, **kwargs)

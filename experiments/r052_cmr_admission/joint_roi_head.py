"""Local r052 joint-loss RoI head; third-party source remains untouched."""
from __future__ import annotations

import torch
from mmdet.models.roi_heads.standard_roi_head import StandardRoIHead
from mmdet.structures.bbox import get_box_tensor
from mmrotate.registry import MODELS

from .joint_api import K, ProposalObservationArms, joint_loss


@MODELS.register_module()
class R052JointRoIHead(StandardRoIHead):
    """Consumes proposal-conditioned marginal likelihood in the detector loss."""
    def __init__(self, *args, r052_mode: str = 'cmr', r052_loss_weight: float = .15,
                 r052_num_classes: int = 15, **kwargs):
        super().__init__(*args, **kwargs)
        self.r052_mode = r052_mode
        self.r052_loss_weight = r052_loss_weight
        self.r052_joint = ProposalObservationArms(
            self.bbox_roi_extractor.out_channels, r052_num_classes, r052_mode)

    def _r052_features(self, x, priors, batch_ids):
        if self.r052_mode == 'cmr':
            offsets = torch.arange(K, device=priors.device, dtype=priors.dtype) * (torch.pi / K)
            candidates = priors[:, None, :].expand(-1, K, -1).clone()
            candidates[..., 4] = torch.remainder(candidates[..., 4] + offsets + torch.pi / 2, torch.pi) - torch.pi / 2
            rois = torch.cat((batch_ids[:, None, None].expand(-1, K, 1).to(priors.dtype), candidates), -1).reshape(-1, 6)
            feat = self.bbox_roi_extractor(x[:self.bbox_roi_extractor.num_inputs], rois)
            return feat.mean((-2, -1)).reshape(len(priors), K, -1)
        rois = torch.cat((batch_ids[:, None].to(priors.dtype), priors), dim=1)
        feat = self.bbox_roi_extractor(x[:self.bbox_roi_extractor.num_inputs], rois)
        return feat.mean((-2, -1))

    def bbox_loss(self, x, sampling_results):
        result = super().bbox_loss(x, sampling_results)
        positives = [r for r in sampling_results if len(r.pos_priors)]
        if not positives:
            result['loss_r052_joint'] = sum(p.sum() for p in self.r052_joint.parameters()) * 0.
            return result
        priors = torch.cat([get_box_tensor(r.pos_priors) for r in positives])
        gt = torch.cat([get_box_tensor(r.pos_gt_bboxes) for r in positives])
        labels = torch.cat([r.pos_gt_labels.long() for r in positives])
        batch_ids = torch.cat([
            torch.full((len(r.pos_priors),), i, device=priors.device, dtype=torch.long)
            for i, r in enumerate(positives)])
        box_target = torch.stack((gt[:, 0], gt[:, 1], gt[:, 2].clamp_min(1e-3).log(), gt[:, 3].clamp_min(1e-3).log()), -1)
        out = self.r052_joint(self._r052_features(x, priors, batch_ids), labels, box_target, gt[:, 4], priors[:, 4])
        result['loss_r052_joint'] = joint_loss(out) * self.r052_loss_weight
        result['r052_q_entropy'] = -(out.q * out.q.clamp_min(1e-12).log()).sum(-1).mean().detach()
        result['r052_native_risk'] = out.native_risk.mean().detach()
        return result

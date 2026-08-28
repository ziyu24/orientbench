"""CMR training adapter for real decoded Oriented R-CNN proposals."""
from __future__ import annotations

import torch
import torch.nn.functional as F
from mmdet.models.roi_heads.standard_roi_head import StandardRoIHead
from mmdet.models.layers import multiclass_nms
from mmdet.structures.bbox import bbox2roi, get_box_tensor, scale_boxes
from mmengine.structures import InstanceData
from mmrotate.registry import MODELS

from .cmr_core import CMRRoIEvidence, axial_wrap


@MODELS.register_module()
class CMRStandardRoIHead(StandardRoIHead):
    """Adds CMR likelihood training to the host RoI head without source edits.

    It receives ``SamplingResult.pos_priors`` produced by the host RPN, so the
    intervention is on decoded RPN proposals rather than FPN anchor templates.
    The inference/NMS provenance adapter is deliberately kept separate until
    its explicit index-preservation validator is wired in.
    """

    def __init__(self, *args, cmr_loss_weight: float = .15,
                 cmr_num_classes: int = 15, observation_mode: str = 'cmr', **kwargs):
        super().__init__(*args, **kwargs)
        if observation_mode not in ('cmr', 'direct_dist', 'single_roi_quality'):
            raise ValueError(f'unknown frozen r051 observation mode: {observation_mode}')
        self.cmr_loss_weight = cmr_loss_weight
        self.observation_mode = observation_mode
        self.cmr = CMRRoIEvidence(self.bbox_roi_extractor.out_channels,
                                  num_classes=cmr_num_classes)

    def bbox_loss(self, x, sampling_results):
        result = super().bbox_loss(x, sampling_results)
        positive = [res for res in sampling_results if len(res.pos_priors)]
        if not positive:
            # DDP requires a differentiable zero on ranks whose sampled image
            # has no positive RoIs; host features are intentionally frozen.
            result['loss_cmr'] = sum(parameter.sum() for parameter in self.cmr.parameters()) * 0.
            return result
        priors = [get_box_tensor(res.pos_priors) for res in positive]
        gt_boxes = [get_box_tensor(res.pos_gt_bboxes) for res in positive]
        labels = torch.cat([res.pos_gt_labels.long() for res in positive])
        rois = bbox2roi(priors)
        proposal_boxes = rois[:, 1:]
        target_angles = torch.cat([box[:, 4] for box in gt_boxes])
        evidence_args = (x[:self.bbox_roi_extractor.num_inputs], proposal_boxes,
                         rois[:, 0].long(), labels, self.bbox_roi_extractor)
        if self.observation_mode == 'cmr':
            cmr_out = self.cmr.forward_with_extractor(*evidence_args)
        elif self.observation_mode == 'direct_dist':
            cmr_out = self.cmr.forward_direct_with_extractor(*evidence_args)
        else:
            cmr_out = self.cmr.forward_single_with_extractor(*evidence_args)
            quality_target = (axial_wrap(target_angles - proposal_boxes[:, 4]).abs() / (torch.pi / 2)).clamp(0., 1.)
            result['loss_cmr'] = F.binary_cross_entropy_with_logits(cmr_out['quality_logit'], quality_target) * self.cmr_loss_weight
            result['cmr_train_quality'] = cmr_out['native_risk'].mean().detach()
            return result
        # Training-only likelihood target. No validation/test value selects K,
        # risk, temperature, loss weight, schedule or checkpoint.
        distance = axial_wrap(target_angles[:, None] - cmr_out['candidate_angles']).abs()
        target = distance.argmin(-1)
        result['loss_cmr'] = F.cross_entropy(cmr_out['logits'], target) * self.cmr_loss_weight
        result['cmr_train_q_entropy'] = -(cmr_out['q'] * cmr_out['q'].clamp_min(1e-12).log()).sum(-1).mean().detach()
        return result

    def predict_bbox(self, x, batch_img_metas, rpn_results_list, rcnn_test_cfg,
                     rescale: bool = False):
        """Decode CMR candidates before NMS and carry exact RPN source rows.

        ``multiclass_nms(return_inds=True)`` supplies the actual kept
        proposal/class rows.  The final fields below are selected by these
        indices; no final-box geometry lookup or nearest-neighbour recovery is
        used anywhere in the provenance path.
        """
        proposals = [res.bboxes for res in rpn_results_list]
        rois = bbox2roi(proposals)
        if not len(rois):
            return super().predict_bbox(x, batch_img_metas, rpn_results_list, rcnn_test_cfg, rescale)
        raw = self._bbox_forward(x, rois)
        counts = tuple(len(p) for p in proposals)
        rois_by_img = rois.split(counts, 0)
        scores_by_img = raw['cls_score'].split(counts, 0)
        preds_by_img = raw['bbox_pred'].split(counts, 0)
        out = []
        for image_id, (roi, cls_score, bbox_pred, rpn, meta) in enumerate(
                zip(rois_by_img, scores_by_img, preds_by_img, rpn_results_list, batch_img_metas)):
            result = InstanceData()
            if not len(roi):
                result.bboxes = get_box_tensor(rpn.bboxes).new_zeros((0, 5))
                result.scores = result.bboxes.new_zeros(0); result.labels = result.bboxes.new_zeros(0, dtype=torch.long)
                result.candidate_uid = result.labels; result.cmr_q = result.bboxes.new_zeros((0, self.cmr.k))
                result.cmr_native_risk = result.bboxes.new_zeros(0)
                out.append(result); continue
            scores = F.softmax(cls_score, dim=-1)
            decoded = self.bbox_head.bbox_coder.decode(roi[:, 1:], bbox_pred, max_shape=meta['img_shape'])
            boxes = get_box_tensor(decoded)
            if rescale:
                factors = [1 / s for s in meta['scale_factor']]
                if len(factors) == 2:
                    factors = [factors[0], factors[1], factors[0], factors[1]]
                factor = boxes.new_tensor(factors + [1.])
                boxes = boxes * factor
            classes = self.bbox_head.num_classes
            pair_source = torch.arange(len(boxes), device=boxes.device).repeat_interleave(classes)
            pair_label = torch.arange(classes, device=boxes.device).repeat(len(boxes))
            pair_scores = scores[:, :-1].reshape(-1)
            active = pair_scores > rcnn_test_cfg.score_thr
            # All active class/proposal pairs receive their own fixed-class,
            # decoded-box CMR field before NMS. The CMR encoder deliberately
            # contains no batch-dependent normalization, so chunks preserve the
            # same per-candidate shared-scorer computation while bounding VRAM.
            active_source, active_label = pair_source[active], pair_label[active]
            active_boxes = boxes[active_source]
            if not len(active_boxes):
                result.bboxes = boxes.new_zeros((0, 5)); result.scores = boxes.new_zeros(0)
                result.labels = boxes.new_zeros(0, dtype=torch.long)
                result.candidate_uid = result.labels; result.cmr_q = boxes.new_zeros((0, self.cmr.k))
                result.cmr_native_risk = boxes.new_zeros(0)
                out.append(result); continue
            pieces = []
            for begin in range(0, len(active_boxes), 128):
                end = min(begin + 128, len(active_boxes))
                evidence_args = (x[:self.bbox_roi_extractor.num_inputs], active_boxes[begin:end],
                                 active_boxes.new_full((end - begin,), image_id, dtype=torch.long),
                                 active_label[begin:end].long(), self.bbox_roi_extractor)
                if self.observation_mode == 'cmr':
                    pieces.append(self.cmr.forward_with_extractor(*evidence_args))
                elif self.observation_mode == 'direct_dist':
                    pieces.append(self.cmr.forward_direct_with_extractor(*evidence_args))
                else:
                    pieces.append(self.cmr.forward_single_with_extractor(*evidence_args))
            if self.observation_mode == 'single_roi_quality':
                cmr_out = {
                    'q': torch.ones((len(active_boxes), 1), device=active_boxes.device),
                    'refined_angle': torch.cat([piece['refined_angle'] for piece in pieces], 0),
                    'native_risk': torch.cat([piece['native_risk'] for piece in pieces], 0)}
            else:
                cmr_out = {key: torch.cat([piece[key] for piece in pieces], 0)
                           for key in ('q', 'refined_angle', 'native_risk')}
            refined_boxes = active_boxes.clone(); refined_boxes[:, 4] = cmr_out['refined_angle']
            multi_boxes = boxes[:, None, :].expand(-1, classes, -1).reshape(-1, 5).clone()
            multi_boxes[active] = refined_boxes
            dets, labels, kept = multiclass_nms(
                multi_boxes.view(len(boxes), classes * 5), scores,
                rcnn_test_cfg.score_thr, rcnn_test_cfg.nms, rcnn_test_cfg.max_per_img,
                return_inds=True, box_dim=5)
            active_global = active.nonzero(as_tuple=False).squeeze(1)
            positions = torch.searchsorted(active_global, kept)
            if len(positions) and not torch.equal(active_global[positions], kept):
                raise RuntimeError('CMR provenance mismatch: NMS kept a row without candidate evidence')
            source = kept // classes
            result.bboxes, result.scores, result.labels = dets[:, :-1], dets[:, -1], labels
            result.candidate_uid = rpn.candidate_uid[source]
            result.cmr_q = cmr_out['q'][positions]
            result.cmr_native_risk = cmr_out['native_risk'][positions]
            result.cmr_original_box = active_boxes[positions]
            result.cmr_refined_box = refined_boxes[positions]
            result.cmr_source_row = source
            # Persist the exact flat proposal/class row returned by NMS.  This
            # gives the independent validator an auditable algebraic link from
            # the final row back to the pre-NMS decoded proposal/class pair.
            result.cmr_nms_kept_index = kept
            result.cmr_nms_class = kept.remainder(classes)
            result.cmr_rpn_level_id = rpn.level_ids[source]
            result.cmr_rpn_cell_id = rpn.cell_ids[source]
            result.cmr_rpn_proposal_id = rpn.proposal_ids[source]
            out.append(result)
        return out

"""Local r052 detector-native CMR RoI head; third-party source is untouched."""
from __future__ import annotations

from dataclasses import dataclass

import torch
from mmcv.ops import nms_rotated
from mmengine.structures import InstanceData
from mmdet.models.roi_heads.standard_roi_head import StandardRoIHead
from mmdet.structures.bbox import bbox2roi, get_box_tensor
from mmrotate.registry import MODELS

from .joint_api import K, ProposalObservationArms, axial_wrap, joint_loss


@dataclass
class PreNMSPayload:
    """Pickle-safe sidecar with InstanceData-compatible length semantics."""
    records: dict
    instance_count: int

    def __len__(self):
        return self.instance_count


def _box_residual(target: torch.Tensor, prior: torch.Tensor) -> torch.Tensor:
    pw, ph = prior[:, 2].clamp_min(1e-3), prior[:, 3].clamp_min(1e-3)
    return torch.stack(((target[:, 0] - prior[:, 0]) / pw,
                        (target[:, 1] - prior[:, 1]) / ph,
                        (target[:, 2].clamp_min(1e-3) / pw).log(),
                        (target[:, 3].clamp_min(1e-3) / ph).log()), -1)


def _decode_residual(prior: torch.Tensor, residual: torch.Tensor,
                     theta: torch.Tensor) -> torch.Tensor:
    pw, ph = prior[:, None, 2].clamp_min(1e-3), prior[:, None, 3].clamp_min(1e-3)
    return torch.stack((prior[:, None, 0] + residual[..., 0] * pw,
                        prior[:, None, 1] + residual[..., 1] * ph,
                        pw * residual[..., 2].clamp(-5., 3.).exp(),
                        ph * residual[..., 3].clamp(-5., 3.).exp(),
                        axial_wrap(theta)), -1)


@MODELS.register_module()
class R052JointRoIHead(StandardRoIHead):
    """Shared joint likelihood used in loss and real decode/NMS inference."""
    def __init__(self, *args, r052_mode: str = 'cmr', r052_loss_weight: float = .15,
                 r052_num_classes: int = 15, **kwargs):
        super().__init__(*args, **kwargs)
        self.r052_mode = r052_mode
        self.r052_loss_weight = r052_loss_weight
        self.r052_joint = ProposalObservationArms(
            self.bbox_roi_extractor.out_channels, r052_num_classes, r052_mode)

    def _r052_features(self, x, priors: torch.Tensor, batch_ids: torch.Tensor):
        if self.r052_mode == 'cmr':
            offsets = torch.arange(K, device=priors.device, dtype=priors.dtype) * (torch.pi / K)
            candidates = priors[:, None, :].expand(-1, K, -1).clone()
            candidates[..., 4] = axial_wrap(candidates[..., 4] + offsets)
            rois = torch.cat((batch_ids[:, None, None].expand(-1, K, 1).to(priors.dtype),
                              candidates), -1).reshape(-1, 6)
            feat = self.bbox_roi_extractor(x[:self.bbox_roi_extractor.num_inputs], rois)
            return feat.mean((-2, -1)).reshape(len(priors), K, -1)
        rois = torch.cat((batch_ids[:, None].to(priors.dtype), priors), dim=1)
        feat = self.bbox_roi_extractor(x[:self.bbox_roi_extractor.num_inputs], rois)
        return feat.mean((-2, -1))

    def bbox_loss(self, x, sampling_results):
        result = super().bbox_loss(x, sampling_results)
        positives = [(batch_id, r) for batch_id, r in enumerate(sampling_results)
                     if len(r.pos_priors)]
        if not positives:
            result['loss_r052_joint'] = sum(p.sum() for p in self.r052_joint.parameters()) * 0.
            return result
        priors = torch.cat([get_box_tensor(r.pos_priors) for _, r in positives])
        gt = torch.cat([get_box_tensor(r.pos_gt_bboxes) for _, r in positives])
        labels = torch.cat([r.pos_gt_labels.long() for _, r in positives])
        batch_ids = torch.cat([torch.full((len(r.pos_priors),), batch_id,
                                           device=priors.device, dtype=torch.long)
                               for batch_id, r in positives])
        uids = [f'train:{batch_id}:{i}' for batch_id, r in positives
                for i in range(len(r.pos_priors))]
        out = self.r052_joint(self._r052_features(x, priors, batch_ids), labels,
                              _box_residual(gt, priors), gt[:, 4], priors[:, 4], uids)
        result['loss_r052_joint'] = joint_loss(out) * self.r052_loss_weight
        result['r052_q_entropy'] = -(out.q * out.q.clamp_min(1e-12).log()).sum(-1).mean().detach()
        result['r052_native_risk'] = out.native_risk.mean().detach()
        return result

    @staticmethod
    def _image_id(meta: dict, batch_id: int) -> str:
        # MMDetection's one-image inference commonly sets img_id=0.  That is
        # only batch-local and would collide across the frozen universe, so
        # prefer the immutable source path whenever it is available.
        return str(meta.get('img_path', meta.get('img_id', f'batch-{batch_id}')))

    @staticmethod
    def _pre_nms_record(boxes, scores, labels, proposal_uids, class_uids,
                        candidate_uids, risks, rpn_boxes, rpn_scores):
        return dict(
            proposal_uid=list(proposal_uids),
            class_uid=[class_uids[i][int(labels[i])] for i in range(len(labels))],
            candidate_uids=[list(candidate_uids[i][int(labels[i])]) for i in range(len(labels))],
            proposal_index=list(range(len(labels))),
            boxes=boxes.detach().cpu(), scores=scores.detach().cpu(),
            # These are the immutable decoded RPN proposal and its score,
            # captured before ROI class expansion; boxes above are the
            # class-conditioned decoded output awaiting final ROI NMS.
            rpn_decoded_boxes=rpn_boxes.detach().cpu(),
            rpn_proposal_scores=rpn_scores.detach().cpu(),
            labels=labels.detach().cpu(), native_risk=risks.detach().cpu())

    def predict_bbox(self, x, batch_img_metas, rpn_results_list, rcnn_test_cfg,
                     rescale: bool = False):
        """No-GT marginal class/full-box/theta/risk followed by rotated NMS."""
        proposals = [get_box_tensor(res.bboxes) for res in rpn_results_list]
        rois = bbox2roi(proposals)
        if rois.shape[0] == 0:
            return super().predict_bbox(x, batch_img_metas, rpn_results_list,
                                        rcnn_test_cfg, rescale)
        counts = tuple(len(p) for p in proposals)
        batch_ids, priors = rois[:, 0].long(), rois[:, 1:]
        rpn_scores = torch.cat([res.scores for res in rpn_results_list])
        proposal_uids = [f'{self._image_id(batch_img_metas[i], i)}:{j}'
                         for i, count in enumerate(counts) for j in range(count)]
        # CMR executes K real, distinct 7x7 rotated RoIAlign observations.
        inference = self.r052_joint.infer(
            self._r052_features(x, priors, batch_ids), priors[:, 4], proposal_uids)
        scores_all = inference.marginal_class_log_probs.exp()
        boxes_all = _decode_residual(priors, inference.box_residuals, inference.angles)
        score_thr = float(rcnn_test_cfg.score_thr)
        iou_thr = float(rcnn_test_cfg.nms.iou_threshold)
        max_per_img = int(rcnn_test_cfg.max_per_img)
        results, offset = [], 0
        for image_index, count in enumerate(counts):
            sl = slice(offset, offset + count)
            scores, boxes, risks = scores_all[sl], boxes_all[sl], inference.native_risk[sl]
            labels = scores.argmax(-1)
            arange = torch.arange(count, device=boxes.device)
            top_boxes, top_scores = boxes[arange, labels], scores[arange, labels]
            pre_nms = self._pre_nms_record(
                top_boxes, top_scores, labels, inference.proposal_uids[sl],
                inference.class_uids[sl], inference.candidate_uids[sl], risks[arange, labels],
                priors[sl], rpn_scores[sl])
            class_ids = torch.arange(scores.shape[1], device=scores.device)[None].expand(count, -1)
            flat_boxes, flat_scores = boxes.reshape(-1, 5), scores.reshape(-1)
            flat_labels = class_ids.reshape(-1)
            flat_prop = arange[:, None].expand_as(scores).reshape(-1)
            valid = flat_scores > score_thr
            result = InstanceData()
            if valid.any():
                dets, keep_local = nms_rotated(flat_boxes[valid], flat_scores[valid], iou_thr,
                                               labels=flat_labels[valid], clockwise=True)
                valid_indices = valid.nonzero(as_tuple=False).squeeze(1)[keep_local]
                keep = valid_indices[dets[:, -1].argsort(descending=True)[:max_per_img]]
                result.bboxes, result.scores, result.labels = flat_boxes[keep], flat_scores[keep], flat_labels[keep]
                result.native_risk, result.proposal_index, result.nms_keep_index = risks.reshape(-1)[keep], flat_prop[keep], keep
                result.proposal_uid = [inference.proposal_uids[offset + int(i)] for i in flat_prop[keep].tolist()]
                result.class_uid = [inference.class_uids[offset + int(i)][int(c)]
                                    for i, c in zip(flat_prop[keep].tolist(), flat_labels[keep].tolist())]
                result.candidate_uids = [list(inference.candidate_uids[offset + int(i)][int(c)])
                                         for i, c in zip(flat_prop[keep].tolist(), flat_labels[keep].tolist())]
            else:
                result.bboxes = flat_boxes.new_zeros((0, 5)); result.scores = flat_scores.new_zeros((0,))
                result.labels = flat_labels.new_zeros((0,), dtype=torch.long)
                result.native_risk = flat_scores.new_zeros((0,)); result.proposal_index = result.labels.clone()
                result.nms_keep_index = result.labels.clone(); result.proposal_uid, result.class_uid, result.candidate_uids = [], [], []
            result.r052_pre_nms = PreNMSPayload(pre_nms, len(result))
            results.append(result)
            offset += count
        return results

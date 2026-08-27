"""Project-local oriented RPN that preserves decoded-proposal provenance."""
from __future__ import annotations

import copy
from typing import List, Optional

import torch
from mmcv.ops import batched_nms
from mmengine.config import ConfigDict
from mmengine.structures import InstanceData
from mmdet.structures.bbox import BaseBoxes, cat_boxes, get_box_tensor, get_box_wh, scale_boxes
from mmrotate.models.dense_heads.oriented_rpn_head import OrientedRPNHead
from mmrotate.registry import MODELS
from mmrotate.structures.bbox import rbox2hbox


@MODELS.register_module()
class CMRProvenanceOrientedRPNHead(OrientedRPNHead):
    """Keep an immutable pre-NMS source row and level/cell identity.

    This is intentionally a project-local replacement for the host RPN rather
    than an edit to mmrotate.  All fields are carried by ``InstanceData``
    through the RPN NMS selection; nothing is inferred from final geometry.
    """

    def _predict_by_feat_single(self, cls_score_list: List[torch.Tensor],
                                bbox_pred_list: List[torch.Tensor],
                                score_factor_list: List[torch.Tensor],
                                mlvl_priors: List[torch.Tensor], img_meta: dict,
                                cfg: ConfigDict, rescale: bool = False,
                                with_nms: bool = True) -> InstanceData:
        cfg = copy.deepcopy(self.test_cfg if cfg is None else cfg)
        img_shape, nms_pre = img_meta['img_shape'], cfg.get('nms_pre', -1)
        bbox_preds, priors_out, scores_out, levels, cells = [], [], [], [], []
        for level, (cls_score, bbox_pred, priors) in enumerate(zip(cls_score_list, bbox_pred_list, mlvl_priors)):
            reg_dim = self.bbox_coder.encode_size
            bbox_pred = bbox_pred.permute(1, 2, 0).reshape(-1, reg_dim)
            cls_score = cls_score.permute(1, 2, 0).reshape(-1, self.cls_out_channels)
            scores = cls_score.sigmoid() if self.use_sigmoid_cls else cls_score.softmax(-1)[:, :-1]
            scores = torch.squeeze(scores)
            original_cell = torch.arange(scores.shape[0], device=scores.device, dtype=torch.long)
            if 0 < nms_pre < scores.shape[0]:
                ranked, chosen = scores.sort(descending=True)
                chosen, scores = chosen[:nms_pre], ranked[:nms_pre]
                bbox_pred, priors, original_cell = bbox_pred[chosen], priors[chosen], original_cell[chosen]
            bbox_preds.append(bbox_pred); priors_out.append(priors); scores_out.append(scores)
            levels.append(scores.new_full((scores.shape[0],), level, dtype=torch.long))
            cells.append(original_cell)
        decoded = self.bbox_coder.decode(cat_boxes(priors_out), torch.cat(bbox_preds), max_shape=img_shape)
        results = InstanceData()
        results.bboxes = decoded
        results.scores = torch.cat(scores_out)
        results.level_ids = torch.cat(levels)
        results.cell_ids = torch.cat(cells)
        results.proposal_ids = torch.arange(len(results.scores), device=results.scores.device, dtype=torch.long)
        results.candidate_uid = results.proposal_ids.clone()
        return self._bbox_post_process(results, cfg, rescale, img_meta=img_meta)

    def _bbox_post_process(self, results: InstanceData, cfg: ConfigDict,
                           rescale: bool = False, with_nms: bool = True,
                           img_meta: Optional[dict] = None) -> InstanceData:
        assert with_nms
        if rescale:
            scale = [1 / s for s in img_meta['scale_factor']]
            results.bboxes = scale_boxes(results.bboxes, scale)
        if cfg.get('min_bbox_size', -1) >= 0:
            w, h = get_box_wh(results.bboxes)
            results = results[(w > cfg.min_bbox_size) & (h > cfg.min_bbox_size)]
        if results.bboxes.numel() == 0:
            empty = InstanceData()
            empty.bboxes = results.bboxes.empty_boxes() if isinstance(results.bboxes, BaseBoxes) else results.scores.new_zeros((0, 5))
            empty.scores = results.scores.new_zeros(0)
            empty.labels = results.scores.new_zeros(0, dtype=torch.long)
            empty.candidate_uid = results.scores.new_zeros(0, dtype=torch.long)
            empty.level_ids = results.scores.new_zeros(0, dtype=torch.long)
            empty.cell_ids = results.scores.new_zeros(0, dtype=torch.long)
            empty.proposal_ids = results.scores.new_zeros(0, dtype=torch.long)
            return empty
        hboxes = rbox2hbox(get_box_tensor(results.bboxes))
        dets, keep = batched_nms(hboxes, results.scores, results.level_ids, cfg.nms)
        results = results[keep][:cfg.max_per_img]
        results.scores = dets[:cfg.max_per_img, -1]
        results.labels = results.scores.new_zeros(len(results), dtype=torch.long)
        return results

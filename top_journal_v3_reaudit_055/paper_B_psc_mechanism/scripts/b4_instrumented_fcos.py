"""Project-local RotatedFCOS instrumentation that preserves PSC vectors through NMS."""

import copy

import torch
from mmdet.models.utils import filter_scores_and_topk
from mmdet.structures.bbox import cat_boxes
from mmengine.structures import InstanceData
from mmrotate.models.dense_heads.rotated_fcos_head import RotatedFCOSHead
from mmrotate.registry import MODELS
from mmrotate.structures import RotatedBoxes


@MODELS.register_module(force=True)
class B4InstrumentedRotatedFCOSHead(RotatedFCOSHead):
    """Carry encoded angle and centerness fields through the standard NMS."""

    def _predict_by_feat_single(
            self, cls_score_list, bbox_pred_list, angle_pred_list,
            score_factor_list, mlvl_priors, img_meta, cfg,
            rescale=False, with_nms=True):
        with_score_factors = score_factor_list[0] is not None
        cfg = copy.deepcopy(self.test_cfg if cfg is None else cfg)
        img_shape = img_meta["img_shape"]
        nms_pre = cfg.get("nms_pre", -1)
        mlvl_bbox_preds, mlvl_valid_priors = [], []
        mlvl_scores, mlvl_labels, mlvl_angle_encoded = [], [], []
        mlvl_score_factors = [] if with_score_factors else None

        for cls_score, bbox_pred, angle_pred, score_factor, priors in zip(
                cls_score_list, bbox_pred_list, angle_pred_list,
                score_factor_list, mlvl_priors):
            bbox_pred = bbox_pred.permute(1, 2, 0).reshape(-1, 4)
            angle_pred = angle_pred.permute(1, 2, 0).reshape(
                -1, self.angle_coder.encode_size)
            if with_score_factors:
                score_factor = score_factor.permute(1, 2, 0).reshape(-1).sigmoid()
            cls_score = cls_score.permute(1, 2, 0).reshape(
                -1, self.cls_out_channels)
            scores = (
                cls_score.sigmoid() if self.use_sigmoid_cls
                else cls_score.softmax(-1)[:, :-1])
            scores, labels, keep_idxs, filtered = filter_scores_and_topk(
                scores, cfg.get("score_thr", 0), nms_pre,
                dict(bbox_pred=bbox_pred, angle_pred=angle_pred, priors=priors))
            bbox_pred = filtered["bbox_pred"]
            angle_pred = filtered["angle_pred"]
            priors = filtered["priors"]
            decoded_angle = self.angle_coder.decode(angle_pred, keepdim=True)
            bbox_pred = torch.cat([bbox_pred, decoded_angle], dim=-1)
            mlvl_bbox_preds.append(bbox_pred)
            mlvl_valid_priors.append(priors)
            mlvl_scores.append(scores)
            mlvl_labels.append(labels)
            mlvl_angle_encoded.append(angle_pred.clone())
            if with_score_factors:
                mlvl_score_factors.append(score_factor[keep_idxs])

        bbox_pred = torch.cat(mlvl_bbox_preds)
        priors = cat_boxes(mlvl_valid_priors)
        results = InstanceData()
        results.bboxes = RotatedBoxes(
            self.bbox_coder.decode(priors, bbox_pred, max_shape=img_shape))
        results.scores = torch.cat(mlvl_scores)
        results.labels = torch.cat(mlvl_labels)
        results.angle_encoded = torch.cat(mlvl_angle_encoded)
        if with_score_factors:
            results.score_factors = torch.cat(mlvl_score_factors)
        return self._bbox_post_process(
            results=results, cfg=cfg, rescale=rescale,
            with_nms=with_nms, img_meta=img_meta)


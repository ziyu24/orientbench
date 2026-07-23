"""Instrumented AngleBranchRetinaHead: carries the ENCODED angle vector through NMS so we can
read each kept detection's native uncertainty (PSC phase_mod / CSL entropy-margin / DCL bit
margin) aligned to the final boxes. Project-local (does NOT modify third_party mmrotate).

The upstream `_predict_by_feat_single` overwrites `angle_pred` with the decoded angle in place,
destroying the encoded vector. We copy the method verbatim and, per level, stash the encoded
angle (post keep_idxs, pre-decode) into `results.angle_encoded`; InstanceData indexing preserves
this custom field through `_bbox_post_process` NMS. TEST-TIME ONLY (predict path); loss/forward
unchanged, so it does not alter trained checkpoints — only how we read them.
"""
import copy
import torch
from mmdet.models.utils import filter_scores_and_topk
from mmdet.structures.bbox import cat_boxes
from mmengine.structures import InstanceData
from mmrotate.registry import MODELS
from mmrotate.models.dense_heads.angle_branch_retina_head import AngleBranchRetinaHead


@MODELS.register_module()
class InstrumentedAngleBranchRetinaHead(AngleBranchRetinaHead):

    def _predict_by_feat_single(self, cls_score_list, bbox_pred_list, angle_pred_list,
                                score_factor_list, mlvl_priors, img_meta, cfg,
                                rescale=False, with_nms=True):
        with_score_factors = score_factor_list[0] is not None
        cfg = self.test_cfg if cfg is None else cfg
        cfg = copy.deepcopy(cfg)
        img_shape = img_meta['img_shape']
        nms_pre = cfg.get('nms_pre', -1)

        mlvl_bbox_preds, mlvl_valid_priors, mlvl_scores, mlvl_labels = [], [], [], []
        mlvl_angle_encoded = []  # <-- instrumentation
        mlvl_phase1_feature_norm = []
        phase1_feature_norms = getattr(self, '_phase1_feature_norms', None)
        mlvl_score_factors = [] if with_score_factors else None
        for level, (cls_score, bbox_pred, angle_pred, score_factor, priors) in enumerate(zip(
                cls_score_list, bbox_pred_list, angle_pred_list,
                score_factor_list, mlvl_priors)):
            cls_score = cls_score.float(); bbox_pred = bbox_pred.float()
            dim = self.bbox_coder.encode_size
            bbox_pred = bbox_pred.permute(1, 2, 0).reshape(-1, dim)
            angle_pred = angle_pred.permute(1, 2, 0).reshape(-1, self.encode_size)
            if with_score_factors:
                score_factor = score_factor.permute(1, 2, 0).reshape(-1).sigmoid()
            cls_score = cls_score.permute(1, 2, 0).reshape(-1, self.cls_out_channels)
            scores = cls_score.sigmoid() if self.use_sigmoid_cls else cls_score.softmax(-1)[:, :-1]
            score_thr = cfg.get('score_thr', 0)
            results = filter_scores_and_topk(
                scores, score_thr, nms_pre, dict(bbox_pred=bbox_pred, priors=priors))
            scores, labels, keep_idxs, filtered_results = results
            bbox_pred = filtered_results['bbox_pred']; priors = filtered_results['priors']
            angle_pred = angle_pred[keep_idxs]
            mlvl_angle_encoded.append(angle_pred.clone())          # <-- keep ENCODED vector
            if phase1_feature_norms is not None:
                feature_norm = phase1_feature_norms[level]
                if feature_norm.ndim == 3:
                    feature_norm = feature_norm[0]
                feature_norm = feature_norm.reshape(-1).repeat_interleave(self.num_anchors)
                mlvl_phase1_feature_norm.append(feature_norm[keep_idxs].clone())
            if with_score_factors:
                score_factor = score_factor[keep_idxs]
            angle_dec = self.angle_coder.decode(angle_pred)
            if self.use_encoded_angle:
                bbox_pred[..., -1] = angle_dec
                bbox_pred = self.bbox_coder.decode(priors, bbox_pred, max_shape=img_shape)
            else:
                bbox_pred = self.bbox_coder.decode(priors, bbox_pred, max_shape=img_shape)
                bbox_pred[..., -1] = angle_dec
            mlvl_bbox_preds.append(bbox_pred); mlvl_valid_priors.append(priors)
            mlvl_scores.append(scores); mlvl_labels.append(labels)
            if with_score_factors:
                mlvl_score_factors.append(score_factor)

        results = InstanceData()
        results.bboxes = cat_boxes(mlvl_bbox_preds)
        results.scores = torch.cat(mlvl_scores)
        results.labels = torch.cat(mlvl_labels)
        results.angle_encoded = torch.cat(mlvl_angle_encoded)      # survives NMS via InstanceData
        if mlvl_phase1_feature_norm:
            results.phase1_reg_feature_norm = torch.cat(mlvl_phase1_feature_norm)
        if with_score_factors:
            results.score_factors = torch.cat(mlvl_score_factors)
        return self._bbox_post_process(
            results=results, cfg=cfg, rescale=rescale, with_nms=with_nms, img_meta=img_meta)

import copy, torch
from mmengine.structures import InstanceData
from mmdet.models.utils import filter_scores_and_topk
from mmdet.structures.bbox import cat_boxes
from mmrotate.registry import MODELS
from mmrotate.models.dense_heads.angle_branch_retina_head import AngleBranchRetinaHead

@MODELS.register_module()
class InstrumentedAngleBranchRetinaHead(AngleBranchRetinaHead):
    """Identical to AngleBranchRetinaHead but attaches PSC phase_mod
    (intrinsic angle confidence = phase_cos^2+phase_sin^2, first freq) to
    pred_instances so it survives NMS and can be dumped (Track A signal)."""
    def _predict_by_feat_single(self, cls_score_list, bbox_pred_list,
                                angle_pred_list, score_factor_list,
                                mlvl_priors, img_meta, cfg, rescale=False, with_nms=True):
        with_score_factors = score_factor_list[0] is not None
        cfg = self.test_cfg if cfg is None else cfg
        cfg = copy.deepcopy(cfg)
        img_shape = img_meta['img_shape']
        nms_pre = cfg.get('nms_pre', -1)
        mlvl_bbox_preds, mlvl_valid_priors, mlvl_scores, mlvl_labels, mlvl_pm = [], [], [], [], []
        mlvl_score_factors = [] if with_score_factors else None
        ac = self.angle_coder; ns = ac.num_step
        cs = ac.coef_sin; cc = ac.coef_cos
        for idx, (cls_score, bbox_pred, angle_pred, score_factor, priors) in \
                enumerate(zip(cls_score_list, bbox_pred_list, angle_pred_list, score_factor_list, mlvl_priors)):
            cls_score = cls_score.float(); bbox_pred = bbox_pred.float()
            dim = self.bbox_coder.encode_size
            bbox_pred = bbox_pred.permute(1, 2, 0).reshape(-1, dim)
            angle_pred = angle_pred.permute(1, 2, 0).reshape(-1, self.encode_size)
            if with_score_factors:
                score_factor = score_factor.permute(1, 2, 0).reshape(-1).sigmoid()
            cls_score = cls_score.permute(1, 2, 0).reshape(-1, self.cls_out_channels)
            scores = cls_score.sigmoid() if self.use_sigmoid_cls else cls_score.softmax(-1)[:, :-1]
            score_thr = cfg.get('score_thr', 0)
            results = filter_scores_and_topk(scores, score_thr, nms_pre, dict(bbox_pred=bbox_pred, priors=priors))
            scores, labels, keep_idxs, filtered_results = results
            bbox_pred = filtered_results['bbox_pred']; priors = filtered_results['priors']
            angle_pred = angle_pred[keep_idxs]
            if with_score_factors: score_factor = score_factor[keep_idxs]
            # phase_mod (intrinsic confidence, first freq) BEFORE decode
            _cs = cs.to(angle_pred); _cc = cc.to(angle_pred)
            ph_sin = (angle_pred[:, 0:ns] * _cs).sum(-1)
            ph_cos = (angle_pred[:, 0:ns] * _cc).sum(-1)
            phase_mod = ph_cos ** 2 + ph_sin ** 2
            angle_pred = ac.decode(angle_pred)
            if self.use_encoded_angle:
                bbox_pred[..., -1] = angle_pred
                bbox_pred = self.bbox_coder.decode(priors, bbox_pred, max_shape=img_shape)
            else:
                bbox_pred = self.bbox_coder.decode(priors, bbox_pred, max_shape=img_shape)
                bbox_pred[..., -1] = angle_pred
            mlvl_bbox_preds.append(bbox_pred); mlvl_valid_priors.append(priors)
            mlvl_scores.append(scores); mlvl_labels.append(labels); mlvl_pm.append(phase_mod)
            if with_score_factors: mlvl_score_factors.append(score_factor)
        results = InstanceData()
        results.bboxes = cat_boxes(mlvl_bbox_preds)
        results.scores = torch.cat(mlvl_scores)
        results.labels = torch.cat(mlvl_labels)
        results.phase_mod = torch.cat(mlvl_pm)
        if with_score_factors: results.score_factors = torch.cat(mlvl_score_factors)
        return self._bbox_post_process(results=results, cfg=cfg, rescale=rescale, with_nms=with_nms, img_meta=img_meta)

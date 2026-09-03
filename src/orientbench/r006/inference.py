"""Direct, traceable r006 inference after resize and before normalization.

The runner deliberately owns the integer canvas translation.  It does not use
an image-file transform after resizing, so no interpolation can enter a shift.
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import mmcv
import numpy as np
import torch
from mmengine.config import Config
from mmengine.runner.checkpoint import load_checkpoint
from mmengine.structures import InstanceData
from mmdet.structures import DetDataSample
from mmdet.utils import register_all_modules as register_mmdet
from mmrotate.registry import MODELS
from mmrotate.structures import RotatedBoxes, distance2obb
from mmrotate.utils import register_all_modules as register_mmrotate

from .preflight import MODELS as MODEL_SPECS


MARGIN = 64  # frozen from the declared maximum source stride, 32 input pixels


def _tensor(value: Any) -> torch.Tensor:
    return value.tensor if hasattr(value, "tensor") else value


def _unwrap(value: Any) -> Any:
    if isinstance(value, tuple) and len(value) == 1:
        return value[0]
    return value


@dataclass(frozen=True)
class Canvas:
    image: np.ndarray
    scale: tuple[float, float]
    offset: tuple[int, int]
    original_shape: tuple[int, int]


def _resize_and_canvas(image: np.ndarray, scale: tuple[int, int], axis: str, shift: int,
                       margin: int = MARGIN, pad: int = 0) -> Canvas:
    """Match the config's keep-ratio resize, then add a fixed raw-pixel canvas."""
    resized, factor = mmcv.imrescale(image, scale, return_scale=True, backend="cv2")
    sx = resized.shape[1] / image.shape[1]
    sy = resized.shape[0] / image.shape[0]
    height, width = resized.shape[:2]
    canvas = np.full((height + 2 * margin, width + 2 * margin, 3), pad, dtype=image.dtype)
    dx, dy = (shift, 0) if axis == "x" else (0, shift)
    canvas[margin + dy:margin + dy + height, margin + dx:margin + dx + width] = resized
    return Canvas(canvas, (sx, sy), (margin + dx, margin + dy), image.shape[:2])


class SourceTrace:
    """Associates final post-NMS predictions with their actual source level."""
    def __init__(self, model: torch.nn.Module, model_name: str):
        self.model, self.model_name = model, model_name
        self.rois = self.levels = self.bbox_output = self.rtm_output = None
        self.handles = []
        if model_name == "oriented_rcnn_r50":
            extractor = model.roi_head.bbox_roi_extractor
            self.handles.append(extractor.register_forward_pre_hook(self._roi_input))
            self.handles.append(model.roi_head.bbox_head.register_forward_hook(self._bbox_output))
        elif model_name == "rotated_rtmdet_m":
            self.handles.append(model.bbox_head.register_forward_hook(self._rtm_output))
        else:
            raise ValueError(model_name)

    def clear(self) -> None:
        self.rois = self.levels = self.bbox_output = self.rtm_output = None

    def close(self) -> None:
        for handle in self.handles:
            handle.remove()

    def _roi_input(self, module: torch.nn.Module, inputs: tuple[Any, ...]) -> None:
        rois = inputs[1].detach()
        self.rois = rois
        # Rotated RoIs include a leading batch index.  The extractor's mapper
        # indexes width/height at columns 3/4 of that six-column layout.
        self.levels = module.map_roi_levels(rois, len(module.featmap_strides)).detach()

    def _bbox_output(self, module: torch.nn.Module, inputs: tuple[Any, ...], output: Any) -> None:
        self.bbox_output = tuple(part.detach() for part in output)

    def _rtm_output(self, module: torch.nn.Module, inputs: tuple[Any, ...], output: Any) -> None:
        self.rtm_output = tuple(tuple(part.detach() for part in group) for group in output)

    @staticmethod
    def _match(final: torch.Tensor, final_scores: torch.Tensor, boxes: torch.Tensor,
               candidate_scores: torch.Tensor, levels: torch.Tensor) -> list[int]:
        """Exact decoded-box/score association, with a strict numeric tolerance."""
        answer: list[int] = []
        used: set[int] = set()
        for box, score in zip(final, final_scores):
            delta = (boxes[:, :4] - box[:4]).abs().sum(1)
            # score disambiguates duplicate decoded boxes before NMS.
            delta = delta + (candidate_scores - score).abs() * 1e3
            order = torch.argsort(delta)
            index = next((int(ix) for ix in order.tolist() if int(ix) not in used), None)
            if index is None or float(delta[index]) > 2e-3:
                raise RuntimeError(
                    "cannot exactly associate final prediction with source candidate; "
                    f"best_delta={float(delta[order[0]]):.8g}, final={box[:4].tolist()}, "
                    f"candidate={boxes[order[0], :4].tolist()}")
            used.add(index)
            answer.append(int(levels[index]))
        return answer

    def source_strides(self, prediction: InstanceData, img_meta: dict[str, Any]) -> list[int]:
        final = _tensor(prediction.bboxes).detach()
        scores = prediction.scores.detach()
        if self.model_name == "oriented_rcnn_r50":
            if self.rois is None or self.levels is None or self.bbox_output is None:
                raise RuntimeError("missing RoI provenance hook")
            cls_score, bbox_pred = self.bbox_output
            candidate_scores = torch.softmax(cls_score, dim=-1)[:, 0]
            decoded = self.model.roi_head.bbox_head.bbox_coder.decode(
                self.rois[:, 1:], bbox_pred, max_shape=img_meta["img_shape"])
            candidate_boxes = _tensor(decoded).detach()
            level_index = self._match(final, scores, candidate_boxes, candidate_scores, self.levels)
            strides = self.model.roi_head.bbox_roi_extractor.featmap_strides
            if any(level < 0 or level >= len(strides) for level in level_index):
                raise RuntimeError(
                    f"invalid hooked RoI levels {sorted(set(level_index))}; "
                    f"extractor strides={list(strides)}, raw range="
                    f"[{int(self.levels.min())}, {int(self.levels.max())}]")
            return [int(strides[level]) for level in level_index]
        if self.rtm_output is None:
            raise RuntimeError("missing RTMDet provenance hook")
        cls_scores, bbox_preds, angle_preds = self.rtm_output
        head = self.model.bbox_head
        feat_sizes = [score.shape[-2:] for score in cls_scores]
        priors = head.prior_generator.grid_priors(feat_sizes, dtype=cls_scores[0].dtype,
                                                  device=cls_scores[0].device)
        candidate_boxes, candidate_scores, candidate_levels = [], [], []
        for level, (cls_score, bbox, angle, prior) in enumerate(zip(cls_scores, bbox_preds, angle_preds, priors)):
            scores_l = cls_score[0].permute(1, 2, 0).reshape(-1, head.cls_out_channels).sigmoid()
            bbox_l = bbox[0].permute(1, 2, 0).reshape(-1, 4)
            angle_l = angle[0].permute(1, 2, 0).reshape(-1, head.angle_coder.encode_size)
            threshold = head.test_cfg.get("score_thr", 0.0)
            nms_pre = head.test_cfg.get("nms_pre", -1)
            from mmdet.models.utils import filter_scores_and_topk
            score_l, _, keep, filtered = filter_scores_and_topk(
                scores_l, threshold, nms_pre, dict(bbox_pred=bbox_l, angle_pred=angle_l, priors=prior))
            decoded_angle = head.angle_coder.decode(filtered["angle_pred"], keepdim=True)
            decoded = distance2obb(filtered["priors"], torch.cat([filtered["bbox_pred"], decoded_angle], -1),
                                  angle_version=head.angle_version)
            candidate_boxes.append(decoded.detach())
            candidate_scores.append(score_l.detach())
            candidate_levels.append(torch.full_like(score_l, level, dtype=torch.long))
        levels = self._match(final, scores, torch.cat(candidate_boxes), torch.cat(candidate_scores),
                             torch.cat(candidate_levels))
        strides = [int(pair[0]) for pair in head.prior_generator.strides]
        return [strides[level] for level in levels]


def _load_model(model_name: str, pth_root: Path, device: str) -> tuple[torch.nn.Module, Config]:
    register_mmdet(init_default_scope=False)
    register_mmrotate(init_default_scope=True)
    spec = MODEL_SPECS[model_name]
    cfg = Config.fromfile(pth_root / spec["config"])
    cfg.model.train_cfg = None
    model = MODELS.build(cfg.model)
    load_checkpoint(model, str(pth_root / spec["checkpoint"]), map_location="cpu")
    model.to(device).eval()
    return model, cfg


def _predict(model: torch.nn.Module, trace: SourceTrace, canvas: Canvas, image_id: str,
             device: str) -> dict[str, Any]:
    raw = torch.from_numpy(np.ascontiguousarray(canvas.image.transpose(2, 0, 1)))
    meta = {
        # The model may request rescaled prediction during test_step.  Canvas is
        # its own coordinate frame; source-coordinate conversion happens below.
        "img_id": image_id, "ori_shape": canvas.image.shape[:2], "img_shape": canvas.image.shape[:2],
        "pad_shape": canvas.image.shape[:2], "scale_factor": (1.0, 1.0),
    }
    sample = DetDataSample(metainfo=meta)
    batch = model.data_preprocessor({"inputs": [raw], "data_samples": [sample]}, False)
    trace.clear()
    with torch.no_grad():
        # test_step requests rescale=True and clips to the original image.  The
        # r006 canvas is deliberately the inference coordinate system, so its
        # reversible coordinate map is applied below instead.
        output = model.predict(batch["inputs"], batch["data_samples"], rescale=False)[0]
    pred = output.pred_instances
    boxes = _tensor(pred.bboxes).detach().cpu().numpy().astype(float)
    source = trace.source_strides(pred, output.metainfo)
    ox, oy = canvas.offset
    boxes[:, 0] = (boxes[:, 0] - ox) / canvas.scale[0]
    boxes[:, 1] = (boxes[:, 1] - oy) / canvas.scale[1]
    boxes[:, 2] /= canvas.scale[0]
    boxes[:, 3] /= canvas.scale[1]
    return {"img_id": image_id, "bboxes": boxes.tolist(), "scores": pred.scores.detach().cpu().tolist(),
            "labels": pred.labels.detach().cpu().tolist(), "source_stride": source,
            "canvas_offset": [ox, oy], "scale": list(canvas.scale), "canvas_shape": list(canvas.image.shape[:2])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODEL_SPECS, required=True)
    parser.add_argument("--pth-root", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--axis", choices=("x", "y"), default="x")
    parser.add_argument("--shift", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if not 0 <= args.shift < 64:
        raise ValueError("r006 shift must be an integer in [0, 64)")
    model, cfg = _load_model(args.model, args.pth_root, args.device)
    scale = tuple(cfg.test_dataloader.dataset.pipeline[1]["scale"])
    trace = SourceTrace(model, args.model)
    ids = [line.strip() for line in args.ids.read_text().splitlines() if line.strip()]
    if args.limit is not None:
        ids = ids[:args.limit]
    records = []
    try:
        for image_id in ids:
            image = cv2.imread(str(args.images / f"{image_id}.bmp"), cv2.IMREAD_COLOR)
            if image is None:
                raise FileNotFoundError(image_id)
            canvas = _resize_and_canvas(image, scale, args.axis, args.shift)
            records.append(_predict(model, trace, canvas, image_id, args.device))
    finally:
        trace.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("wb") as handle:
        pickle.dump({"protocol": "r006-canvas-inference-v1", "model": args.model,
                     "axis": args.axis, "shift": args.shift, "margin": MARGIN, "records": records}, handle)


if __name__ == "__main__":
    main()

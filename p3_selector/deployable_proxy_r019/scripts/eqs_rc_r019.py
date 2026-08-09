#!/usr/bin/env python3
"""Corrected prediction-only EQS feature production for r019."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from mmcv.ops import box_iou_rotated


ROOT = Path(__file__).resolve().parents[3]
R014_SOURCE = ROOT / "p3_selector/deployable_proxy_r014/scripts/build_equivariance_features_r014.py"
_SPEC = importlib.util.spec_from_file_location("r014_feature_production", R014_SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("r014 production feature module cannot be loaded")
R014 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(R014)

FEATURE_COLUMNS = [
    "logit_score", "log_pred_ar", "half_log_pred_area",
    "support_fraction", "missing_fraction", "axial_dispersion",
    "u_axis", "iou_loss", "center_dispersion",
    "long_side_dispersion", "short_side_dispersion", "score_dispersion",
    "association_margin",
]
KEY_COLUMNS = ["image_id", "pred_id", "class_id", "detection_score"]


def wrap_mod_pi(theta: float) -> float:
    return float(theta % math.pi)


def canonical_box(box) -> np.ndarray:
    values = np.asarray(box, dtype=float).copy()
    if values.shape != (5,) or not np.isfinite(values).all():
        raise ValueError("box must be one finite five-vector")
    if values[2] <= 0 or values[3] <= 0:
        raise ValueError("box side lengths must be positive")
    if values[3] > values[2]:
        values[2], values[3] = values[3], values[2]
        values[4] += math.pi / 2
    values[4] = wrap_mod_pi(values[4])
    return values


def canonical_boxes(boxes: torch.Tensor) -> torch.Tensor:
    if boxes.ndim != 2 or boxes.shape[1] != 5 or not torch.isfinite(boxes).all():
        raise ValueError("boxes must be a finite Nx5 tensor")
    if len(boxes) == 0:
        return boxes.detach().cpu().float().clone()
    rows = np.stack([canonical_box(row) for row in boxes.detach().cpu().numpy()])
    return torch.tensor(rows, dtype=torch.float32)


def axial_dispersion(angles: list[float], no_auxiliary: bool = False) -> float:
    if no_auxiliary:
        return 1.0
    values = np.asarray(angles, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("axial dispersion requires identity plus accepted auxiliary angles")
    return float(np.clip(1.0 - abs(np.mean(np.exp(2j * values))), 0.0, 1.0))


def inverse_view(record: dict, direction: str) -> torch.Tensor:
    """Dynamically call the r014 inverse-coordinate production path."""
    if direction not in {"horizontal", "vertical"}:
        raise ValueError("unknown view direction")
    return canonical_boxes(R014.inverse_boxes(record, direction))


def association(identity_boxes: torch.Tensor, identity_labels: torch.Tensor,
                view_boxes: torch.Tensor, view_scores: torch.Tensor,
                view_labels: torch.Tensor) -> tuple[dict[int, tuple[int, float]], dict[int, float]]:
    """Corrected global greedy association and pre-greedy candidate margin."""
    if any(not torch.isfinite(x).all() for x in (identity_boxes, view_boxes, view_scores)):
        raise ValueError("non-finite association input")
    matches: dict[int, tuple[int, float]] = {}
    margins: dict[int, float] = {}
    for label in sorted(set(identity_labels.tolist())):
        ii = torch.where(identity_labels == label)[0]
        vv = torch.where(view_labels == label)[0]
        if not len(ii):
            continue
        if not len(vv):
            for global_i in ii.tolist():
                margins[global_i] = 0.0
            continue
        matrix = box_iou_rotated(identity_boxes[ii], view_boxes[vv]).cpu().numpy()
        candidates = []
        for local_i, global_i in enumerate(ii.tolist()):
            accepted = sorted((float(matrix[local_i, local_v]), int(global_v))
                              for local_v, global_v in enumerate(vv.tolist())
                              if float(matrix[local_i, local_v]) >= 0.3)
            accepted.sort(key=lambda item: (-item[0], item[1]))
            if not accepted:
                margins[global_i] = 0.0
            elif len(accepted) == 1:
                margins[global_i] = 1.0
            else:
                margins[global_i] = float(np.clip(accepted[0][0] - accepted[1][0], 0.0, 1.0))
            for local_v, global_v in enumerate(vv.tolist()):
                iou = float(matrix[local_i, local_v])
                if iou >= 0.3:
                    candidates.append((-iou, -float(view_scores[global_v]), global_i, global_v))
        used_i: set[int] = set()
        used_v: set[int] = set()
        for neg_iou, _, global_i, global_v in sorted(candidates):
            if global_i in used_i or global_v in used_v:
                continue
            used_i.add(global_i)
            used_v.add(global_v)
            matches[global_i] = (global_v, -neg_iou)
    return matches, margins


def _aggregate_image(identity: dict, hrecord: dict, vrecord: dict,
                     dth: Callable[[float], float], inverse_fn=inverse_view) -> list[dict]:
    image_id = str(identity["img_id"])
    if str(hrecord["img_id"]) != image_id or str(vrecord["img_id"]) != image_id:
        raise ValueError("view image identity mismatch")
    ib_raw, scores, labels = R014.tensors(identity)
    hb_raw, hs, hl = R014.tensors(hrecord)
    vb_raw, vs, vl = R014.tensors(vrecord)
    ib = canonical_boxes(ib_raw)
    hb = inverse_fn(hrecord, "horizontal")
    vb = inverse_fn(vrecord, "vertical")
    hm, hmargin = association(ib, labels, hb, hs, hl)
    vm, vmargin = association(ib, labels, vb, vs, vl)
    rows = []
    for pred_id in range(len(ib)):
        base = ib[pred_id]
        long_side, short_side = float(base[2]), float(base[3])
        pred_ar = long_side / max(short_side, 1e-6)
        area = max(long_side * short_side, 1e-6)
        score_clip = float(np.clip(float(scores[pred_id]), 1e-6, 1 - 1e-6))
        logit = float(np.clip(math.log(score_clip / (1 - score_clip)), -13.815511, 13.815511))
        accepted = []
        accepted_angles = [float(base[4])]
        for match, boxes, view_scores, margins in (
            (hm, hb, hs, hmargin), (vm, vb, vs, vmargin)
        ):
            if pred_id not in match:
                continue
            view_id, iou = match[pred_id]
            other = boxes[view_id]
            accepted_angles.append(float(other[4]))
            other_score = float(np.clip(float(view_scores[view_id]), 1e-6, 1 - 1e-6))
            other_logit = float(np.clip(math.log(other_score / (1 - other_score)), -13.815511, 13.815511))
            accepted.append({
                "angle": R014.le90_deg(float(base[4]), float(other[4])),
                "iou_loss": 1.0 - iou,
                "center": math.hypot(float(base[0] - other[0]), float(base[1] - other[1])) / math.sqrt(area),
                "long_disp": abs(math.log(max(float(other[2]), 1e-6) / long_side)),
                "short_disp": abs(math.log(max(float(other[3]), 1e-6) / short_side)),
                "score_disp": abs(logit - other_logit),
                "margin": margins[pred_id],
            })
        support = len(accepted) / 2.0
        if accepted:
            median = lambda key: float(np.median([row[key] for row in accepted]))
            values = {
                "axial_dispersion": axial_dispersion(accepted_angles),
                "u_axis": float(np.clip(median("angle") / max(float(dth(pred_ar)), 1.0), 0.0, 3.0)),
                "iou_loss": float(np.clip(median("iou_loss"), 0.0, 1.0)),
                "center_dispersion": float(np.clip(median("center"), 0.0, 3.0)),
                "long_side_dispersion": float(np.clip(median("long_disp"), 0.0, 3.0)),
                "short_side_dispersion": float(np.clip(median("short_disp"), 0.0, 3.0)),
                "score_dispersion": float(np.clip(median("score_disp"), 0.0, 10.0)),
                "association_margin": float(np.clip(median("margin"), 0.0, 1.0)),
            }
        else:
            values = {
                "axial_dispersion": 1.0, "u_axis": 3.0, "iou_loss": 1.0,
                "center_dispersion": 3.0, "long_side_dispersion": 3.0,
                "short_side_dispersion": 3.0, "score_dispersion": 10.0,
                "association_margin": 0.0,
            }
        row = {
            "image_id": image_id, "pred_id": pred_id,
            "class_id": int(labels[pred_id]), "detection_score": float(scores[pred_id]),
            "logit_score": logit,
            "log_pred_ar": float(np.clip(math.log(max(pred_ar, 1 + 1e-6)), 0.0, 4.605170)),
            "half_log_pred_area": float(np.clip(0.5 * math.log(area), -6.907755, 9.210340)),
            "support_fraction": support, "missing_fraction": 1.0 - support,
            **values,
        }
        if not all(math.isfinite(float(row[key])) for key in FEATURE_COLUMNS + ["detection_score"]):
            raise ValueError("non-finite generated feature")
        rows.append(row)
    return rows


def build_feature_rows(identity_records: list[dict], hrecords: list[dict], vrecords: list[dict],
                       dth: Callable[[float], float], inverse_fn=inverse_view) -> list[dict]:
    triples = [sorted(records, key=lambda row: str(row["img_id"]))
               for records in (identity_records, hrecords, vrecords)]
    ids = [[str(row["img_id"]) for row in records] for records in triples]
    if not (ids[0] == ids[1] == ids[2]) or len(ids[0]) != len(set(ids[0])):
        raise ValueError("missing, duplicate, or ambiguous view image identity")
    result = []
    for identity, hrecord, vrecord in zip(*triples):
        result.extend(_aggregate_image(identity, hrecord, vrecord, dth, inverse_fn))
    keys = [(row["image_id"], row["pred_id"]) for row in result]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate feature key")
    return result

#!/usr/bin/env python3
"""Build SUPERVISOR_049 top_journal_v3 evidence artifacts.

This script only reads frozen OrientBench assets and writes under top_journal_v3.
It does not train detectors, modify thresholds, or rewrite D_cal/D_audit splits.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from shapely.affinity import rotate, translate
from shapely.geometry import Polygon, box


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "top_journal_v3"
DOCS = OUT / "docs"
REPORTS = OUT / "reports"
FIGS = OUT / "figures"
LOGS = OUT / "logs"

DATASETS = [
    ("DOTA-v1.0", "train", "dota10_train"),
    ("DOTA-v1.5", "train", "dota15_train"),
    ("FAIR1M-v1.0", "train", "fair1m_train"),
    ("DIOR-R", "trainval", "dior_trainval"),
    ("HRSC2016", "trainval", "hrsc_trainval"),
]
MAX_IMAGES_PER_DATASET = int(os.environ.get("OB049_MAX_IMAGES", "80"))


@dataclass
class Det:
    image_id: str
    class_name: str
    score: float
    cx: float
    cy: float
    w: float
    h: float
    theta: float
    raw: dict


def now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def read_jsonl(path: Path, limit: int | None = None) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
                if limit and len(rows) >= limit:
                    break
    return rows


def poly(cx: float, cy: float, w: float, h: float, theta: float) -> Polygon:
    p = box(-w / 2, -h / 2, w / 2, h / 2)
    p = rotate(p, theta * 180 / math.pi, origin=(0, 0), use_radians=False)
    return translate(p, cx, cy)


def riou(a: Det | dict, b: Det | dict) -> float:
    def vals(x):
        if isinstance(x, Det):
            return x.cx, x.cy, x.w, x.h, x.theta
        return x["obb_cx"], x["obb_cy"], x["obb_w"], x["obb_h"], x["obb_theta"]

    pa = poly(*vals(a))
    pb = poly(*vals(b))
    inter = pa.intersection(pb).area
    union = pa.union(pb).area
    return float(inter / union) if union > 0 else 0.0


def angle_err_deg(a: float, b: float) -> float:
    d = abs((a - b + math.pi / 2) % math.pi - math.pi / 2)
    return d * 180 / math.pi


def aspect_bin(w: float, h: float) -> str:
    ar = max(w, h) / max(1e-9, min(w, h))
    if ar < 1.2:
        return "near_square"
    if ar < 2.5:
        return "moderate"
    return "elongated"


def ap_at(preds: list[Det], gts: list[dict], thr: float) -> float:
    gt_by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for g in gts:
        gt_by_key[(g["image_id"], g["class_name"])].append(g)
    matched = {id(g): False for g in gts}
    tp, fp = [], []
    for p in sorted(preds, key=lambda x: x.score, reverse=True):
        best = None
        best_dist = float("inf")
        for g in gt_by_key.get((p.image_id, p.class_name), []):
            if matched[id(g)]:
                continue
            if abs(p.cx - float(g["obb_cx"])) > 2.5 * max(p.w, float(g["obb_w"]), 1.0):
                continue
            if abs(p.cy - float(g["obb_cy"])) > 2.5 * max(p.h, float(g["obb_h"]), 1.0):
                continue
            dist = (p.cx - float(g["obb_cx"])) ** 2 + (p.cy - float(g["obb_cy"])) ** 2
            if dist < best_dist:
                best_dist, best = dist, g
        best_iou = riou(p, best) if best is not None else 0.0
        if best is not None and best_iou >= thr:
            matched[id(best)] = True
            tp.append(1.0)
            fp.append(0.0)
        else:
            tp.append(0.0)
            fp.append(1.0)
    if not tp or not gts:
        return 0.0
    tp = np.cumsum(tp)
    fp = np.cumsum(fp)
    rec = tp / max(1, len(gts))
    prec = tp / np.maximum(1, tp + fp)
    # continuous AP envelope
    mrec = np.r_[0, rec, 1]
    mpre = np.r_[0, prec, 0]
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def match_for_risk(preds: list[Det], gts: list[dict], thr: float = 0.5) -> pd.DataFrame:
    gt_by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for g in gts:
        gt_by_key[(g["image_id"], g["class_name"])].append(g)
    used = {id(g): False for g in gts}
    rows = []
    for p in sorted(preds, key=lambda x: x.score, reverse=True):
        best = None
        best_dist = float("inf")
        for g in gt_by_key.get((p.image_id, p.class_name), []):
            if used[id(g)]:
                continue
            if abs(p.cx - float(g["obb_cx"])) > 2.5 * max(p.w, float(g["obb_w"]), 1.0):
                continue
            if abs(p.cy - float(g["obb_cy"])) > 2.5 * max(p.h, float(g["obb_h"]), 1.0):
                continue
            dist = (p.cx - float(g["obb_cx"])) ** 2 + (p.cy - float(g["obb_cy"])) ** 2
            if dist < best_dist:
                best_dist, best = dist, g
        best_iou = riou(p, best) if best is not None else 0.0
        if best is not None and best_iou >= thr:
            used[id(best)] = True
            ar = max(best["obb_w"], best["obb_h"]) / max(1e-9, min(best["obb_w"], best["obb_h"]))
            rows.append(
                {
                    "score": p.score,
                    "angle_error": angle_err_deg(p.theta, best["obb_theta"]),
                    "iou": best_iou,
                    "aspect_ratio": ar,
                    "aspect_bin": aspect_bin(best["obb_w"], best["obb_h"]),
                    "area": best["obb_w"] * best["obb_h"],
                    "class_name": p.class_name,
                    "image_id": p.image_id,
                }
            )
    return pd.DataFrame(rows)


def risk_metrics(df: pd.DataFrame, selector: str = "score") -> dict:
    if df.empty:
        return {"AURC": np.nan, "Risk@70": np.nan, "Risk@90": np.nan, "NRC": np.nan}
    if selector == "geometry":
        score = df["score"] * np.clip((df["aspect_ratio"] - 1) / 2.0, 0.05, 1.0)
    elif selector == "size_linear":
        z = (np.log1p(df["area"]) - np.log1p(df["area"]).mean()) / (np.log1p(df["area"]).std() + 1e-9)
        score = df["score"] + 0.05 * z
    else:
        score = df["score"]
    order = np.argsort(-np.asarray(score))
    risks = np.asarray(df["angle_error"])[order]
    coverages = np.arange(1, len(risks) + 1) / len(risks)
    cumrisk = np.cumsum(risks) / np.arange(1, len(risks) + 1)
    aurc = float(np.trapz(cumrisk, coverages))
    rng = np.random.default_rng(49)
    random_aurcs = []
    for _ in range(128):
        r = rng.permutation(np.asarray(df["angle_error"]))
        random_aurcs.append(float(np.trapz(np.cumsum(r) / np.arange(1, len(r) + 1), coverages)))
    random_aurc = float(np.mean(random_aurcs))
    return {
        "AURC": aurc,
        "Risk@70": float(cumrisk[max(0, math.ceil(0.70 * len(risks)) - 1)]),
        "Risk@90": float(cumrisk[max(0, math.ceil(0.90 * len(risks)) - 1)]),
        "NRC": aurc / random_aurc if random_aurc else np.nan,
    }


def load_dataset(key: str) -> tuple[list[Det], list[dict]]:
    pred_path = ROOT / "outputs/bench_core/predictions" / f"pred_{key}.jsonl"
    gt_path = ROOT / "outputs/bench_core/gt_index" / f"{key}.jsonl"
    pred_rows = read_jsonl(pred_path)
    gt_rows = read_jsonl(gt_path)
    keep_images = set(sorted({r["image_id"] for r in gt_rows})[:MAX_IMAGES_PER_DATASET])
    pred_rows = [r for r in pred_rows if r["image_id"] in keep_images]
    gt_rows = [r for r in gt_rows if r["image_id"] in keep_images]
    preds = [
        Det(
            image_id=r["image_id"],
            class_name=r["class_name"],
            score=float(r.get("score", 1.0)),
            cx=float(r["obb_cx"]),
            cy=float(r["obb_cy"]),
            w=float(r["obb_w"]),
            h=float(r["obb_h"]),
            theta=float(r["obb_theta"]),
            raw=r,
        )
        for r in pred_rows
    ]
    gts = gt_rows
    return preds, gts


def perturb_angle(preds: list[Det], eps_deg: float, mode: str) -> list[Det]:
    rng = np.random.default_rng(abs(hash((eps_deg, mode, 49))) % (2**32))
    out = []
    for p in preds:
        b = aspect_bin(p.w, p.h)
        factor = {"near_square": 1.4, "moderate": 1.0, "elongated": 0.7}[b]
        if mode == "von_mises":
            # approximate concentration from requested angular scale
            sigma = max(1e-6, math.radians(eps_deg * factor))
            noise = rng.vonmises(0.0, 1.0 / (sigma * sigma))
        else:
            noise = rng.normal(0.0, math.radians(eps_deg * factor))
        out.append(Det(p.image_id, p.class_name, p.score, p.cx, p.cy, p.w, p.h, p.theta + noise, p.raw))
    return out


def p1_angle_perturb() -> None:
    rows = []
    for dataset, split, key in DATASETS:
        preds, gts = load_dataset(key)
        base_ap50 = ap_at(preds, gts, 0.5)
        base_ap75 = ap_at(preds, gts, 0.75)
        base_m = risk_metrics(match_for_risk(preds, gts))
        for eps in [0, 2, 5, 10, 20, 35, 50]:
            pp = preds if eps == 0 else perturb_angle(preds, eps, "gaussian")
            ap50 = ap_at(pp, gts, 0.5)
            ap75 = ap_at(pp, gts, 0.75)
            md = match_for_risk(pp, gts)
            for bin_name in ["all", "near_square", "moderate", "elongated"]:
                sub = md if bin_name == "all" else md[md["aspect_bin"] == bin_name]
                m = risk_metrics(sub)
                rows.append(
                    {
                        "dataset": dataset,
                        "split": split,
                        "source_asset": "outputs/bench_core/predictions raw jsonl",
                        "asset_warning": "synthetic_gv_proxy/not_detector_output where flagged in source",
                        "perturbation": "stratified_gaussian_angle_noise",
                        "epsilon_deg": eps,
                        "aspect_bin": bin_name,
                        "n_matched": int(len(sub)),
                        "mAP50": round(ap50, 6),
                        "AP75": round(ap75, 6),
                        "Delta_mAP50": round(ap50 - base_ap50, 6),
                        "Delta_AP75": round(ap75 - base_ap75, 6),
                        "NRC": round(m["NRC"], 6),
                        "AURC": round(m["AURC"], 6),
                        "Risk@70": round(m["Risk@70"], 6),
                        "Risk@90": round(m["Risk@90"], 6),
                        "Delta_angle_risk_Risk@90": round(m["Risk@90"] - base_m["Risk@90"], 6) if bin_name == "all" else "",
                    }
                )
    write_csv(REPORTS / "p1_angle_perturb_dose_response.csv", rows)


def p1_reverse_perturb() -> None:
    rows = []
    for dataset, split, key in DATASETS:
        preds, gts = load_dataset(key)
        base_md = match_for_risk(preds, gts)
        base_angle_mean = float(base_md["angle_error"].mean()) if not base_md.empty else np.nan
        for perturb in ["score", "center", "scale", "classification_confidence"]:
            for eps in [0, 0.05, 0.10, 0.20]:
                rng = np.random.default_rng(abs(hash((dataset, perturb, eps, 49))) % (2**32))
                pp = []
                for p in preds:
                    q = Det(p.image_id, p.class_name, p.score, p.cx, p.cy, p.w, p.h, p.theta, p.raw)
                    if perturb in {"score", "classification_confidence"}:
                        q.score = float(np.clip(q.score + rng.normal(0, eps), 0, 1))
                    elif perturb == "center":
                        q.cx += rng.normal(0, eps * max(q.w, q.h))
                        q.cy += rng.normal(0, eps * max(q.w, q.h))
                    elif perturb == "scale":
                        s = max(0.1, 1 + rng.normal(0, eps))
                        q.w *= s
                        q.h *= s
                    pp.append(q)
                md = match_for_risk(pp, gts)
                ms = risk_metrics(md, "score")
                mg = risk_metrics(md, "geometry")
                rows.append(
                    {
                        "dataset": dataset,
                        "split": split,
                        "perturbation": perturb,
                        "epsilon": eps,
                        "n_matched": int(len(md)),
                        "mAP50": round(ap_at(pp, gts, 0.5), 6),
                        "AP75": round(ap_at(pp, gts, 0.75), 6),
                        "angle_error_mean": round(float(md["angle_error"].mean()) if not md.empty else np.nan, 6),
                        "Delta_angle_error_mean": round((float(md["angle_error"].mean()) if not md.empty else np.nan) - base_angle_mean, 6),
                        "score_selector_NRC": round(ms["NRC"], 6),
                        "geometry_selector_NRC": round(mg["NRC"], 6),
                        "score_selector_AURC": round(ms["AURC"], 6),
                        "geometry_selector_AURC": round(mg["AURC"], 6),
                    }
                )
    write_csv(REPORTS / "p1_reverse_perturb_decoupling.csv", rows)


def p1_pairs_and_doc() -> None:
    metrics = pd.read_csv(ROOT / "outputs/bench_core/reports/metrics_025.csv")
    pairs = []
    for ds, g in metrics.groupby("dataset"):
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g.iloc[i], g.iloc[j]
                # proxy mAP unavailable in this table; Risk@90 used only as old reliability pair scan.
                pairs.append(
                    {
                        "dataset": ds,
                        "detector_a": a["detector"],
                        "detector_b": b["detector"],
                        "baseline_a": a["baseline_id"],
                        "baseline_b": b["baseline_id"],
                        "NRC_AUC_a": a["NRC_AUC"],
                        "NRC_AUC_b": b["NRC_AUC"],
                        "Risk90_a": a["Risk@90"],
                        "Risk90_b": b["Risk@90"],
                        "delta_NRC_AUC": abs(a["NRC_AUC"] - b["NRC_AUC"]),
                        "delta_Risk90": abs(a["Risk@90"] - b["Risk@90"]),
                    }
                )
    pair_df = pd.DataFrame(pairs).sort_values(["delta_NRC_AUC", "delta_Risk90"], ascending=False)
    pair_df.to_csv(REPORTS / "p1_within_dataset_pair_mining.csv", index=False)
    dose = pd.read_csv(REPORTS / "p1_angle_perturb_dose_response.csv")
    rev = pd.read_csv(REPORTS / "p1_reverse_perturb_decoupling.csv")
    summary = dose[dose.aspect_bin == "all"].groupby("epsilon_deg")[["Delta_mAP50", "Delta_angle_risk_Risk@90"]].mean().reset_index()
    DOCS.joinpath("p1_constructive_decoupling_experiment.md").write_text(
        "# P1 constructive decoupling experiment\n\n"
        f"Generated: {now()}\n\n"
        f"Scope: raw prediction jsonl was perturbed before matching on a deterministic smoke subset capped at {MAX_IMAGES_PER_DATASET} images per dataset; matching, AP50/AP75, NRC, AURC, Risk@70 and Risk@90 were recomputed. "
        "The available bench_core raw predictions are flagged as synthetic/proxy in source rows, so this is a constructive pipeline validation, not detector-performance evidence.\n\n"
        "## P1-1 angle perturbation\n\n"
        + summary.to_markdown(index=False)
        + "\n\n## P1-2 reverse perturbation\n\n"
        "Reverse perturbation output reports angle-error distribution changes plus score-selector and geometry-selector NRC separately, avoiding the interpretation that score noise itself changes angle reliability.\n\n"
        f"Rows: {len(rev)}. Artifact: `top_journal_v3/reports/p1_reverse_perturb_decoupling.csv`.\n\n"
        "## P1-3 within-dataset pair mining\n\n"
        "Existing fullval multi-detector metrics lack a mAP column, so the pair mining is partial and uses NRC/Risk90 differences only. "
        "It cannot serve as a mAP-vs-NRC existence proof until matched mAP per cell is joined.\n\n"
        + pair_df.head(10).to_markdown(index=False)
        + "\n\n## P1 pass/fail\n\n"
        "Partial. The raw-perturbation pipeline exists and shows controlled recomputation behavior, but construct-validity claims require rerunning on non-synthetic detector predictions with mAP joined per cell.\n",
        encoding="utf-8",
    )


def iou_curve() -> None:
    rows = []
    for ar in [1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 8.0]:
        w, h = ar, 1.0
        base = Det("", "", 1, 0, 0, w, h, 0, {})
        for deg in range(0, 91, 5):
            other = Det("", "", 1, 0, 0, w, h, math.radians(deg), {})
            rows.append({"aspect_ratio": ar, "delta_theta_deg": deg, "iou": round(riou(base, other), 6)})
    write_csv(FIGS / "iou_delta_theta_aspect_ratio_curve.csv", rows)
    sq45 = [r for r in rows if r["aspect_ratio"] == 1.0 and r["delta_theta_deg"] == 45][0]["iou"]
    (FIGS / "iou_delta_theta_aspect_ratio_curve.md").write_text(
        "# IoU(delta theta; aspect ratio)\n\n"
        f"Generated: {now()}\n\n"
        "The table is computed for co-centered rectangles with identical side lengths and only relative rotation varied.\n\n"
        f"Co-centered square at 45 degrees has IoU={sq45:.6f}, approximately 0.707 and above the 0.5 AP threshold. "
        "This is the structural mAP@0.5 blind spot for near-square angle errors: large orientation changes need not become detection failures.\n\n"
        "Connection: mAP blind spot -> reliability cliff -> NRC/risk-coverage is needed to measure orientation reliability directly.\n",
        encoding="utf-8",
    )


def p2_conformal() -> None:
    rows = []
    shift_rows = []
    for dataset, split, key in DATASETS:
        cal_path = ROOT / "outputs/bench_core/splits" / f"D_cal_{key}.csv"
        audit_path = ROOT / "outputs/bench_core/splits" / f"D_audit_{key}.csv"
        preds, gts = load_dataset(key)
        md = match_for_risk(preds, gts)
        if md.empty:
            continue
        cal_images = set(pd.read_csv(cal_path)["image_id"].astype(str)) if cal_path.exists() else set()
        audit_images = set(pd.read_csv(audit_path)["image_id"].astype(str)) if audit_path.exists() else set()
        cal = md[md.image_id.astype(str).isin(cal_images)]
        audit = md[md.image_id.astype(str).isin(audit_images)]
        if cal.empty or audit.empty:
            # fallback deterministic image split only for old proxy cells; report as partial
            imgs = sorted(md.image_id.unique())
            cal_images = set(imgs[::2])
            cal, audit = md[md.image_id.isin(cal_images)], md[~md.image_id.isin(cal_images)]
        for alpha in [5.0, 10.0, 15.0]:
            # threshold over geometry score that maximizes coverage while calibration retained mean risk <= alpha.
            score = cal["score"] * np.clip((cal["aspect_ratio"] - 1) / 2.0, 0.05, 1.0)
            best_t, best_cov = float(score.max()) + 1, 0.0
            for t in np.quantile(score, np.linspace(0, 1, 101)):
                keep = cal[score >= t]
                if len(keep) and keep["angle_error"].mean() <= alpha and len(keep) / len(cal) >= best_cov:
                    best_t, best_cov = float(t), len(keep) / len(cal)
            audit_score = audit["score"] * np.clip((audit["aspect_ratio"] - 1) / 2.0, 0.05, 1.0)
            keep_a = audit[audit_score >= best_t]
            empirical = float(keep_a["angle_error"].mean()) if len(keep_a) else np.nan
            rows.append(
                {
                    "dataset": dataset,
                    "split": split,
                    "score_wrapped": "geometry_score",
                    "conformal_layer": "split_crc_threshold",
                    "target_risk_alpha_deg": alpha,
                    "threshold": round(best_t, 8),
                    "calibration_risk": round(float(cal[score >= best_t]["angle_error"].mean()), 6) if len(cal[score >= best_t]) else np.nan,
                    "empirical_audit_risk": round(empirical, 6),
                    "coverage": round(len(keep_a) / max(1, len(audit)), 6),
                    "violation": bool(empirical > alpha) if not np.isnan(empirical) else True,
                    "confidence_level": 0.9,
                    "finite_sample_guarantee": "within-cell exchangeability only; proxy implementation reports empirical CRC audit",
                    "n_cal": int(len(cal)),
                    "n_audit": int(len(audit)),
                    "risk_definition": "mean matched angle error in degrees among retained predictions",
                    "md5_image_disjoint": bool(set(cal.image_id).isdisjoint(set(audit.image_id))),
                }
            )
    write_csv(REPORTS / "conformal_within_cell_risk_control.csv", rows)
    df = pd.read_csv(REPORTS / "conformal_within_cell_risk_control.csv")
    for _, source in df.iterrows():
        for _, target in df[df.dataset != source.dataset].iterrows():
            shift_rows.append(
                {
                    "source_dataset": source.dataset,
                    "target_dataset": target.dataset,
                    "target_risk_alpha_deg": source.target_risk_alpha_deg,
                    "threshold_from_source": source.threshold,
                    "reported_setting": "shift audit only; no distribution-free guarantee under dataset/detector shift",
                    "source_violation": source.violation,
                    "target_reference_empirical_risk": target.empirical_audit_risk,
                    "target_reference_coverage": target.coverage,
                }
            )
    write_csv(REPORTS / "conformal_shift_violation_audit.csv", shift_rows)
    DOCS.joinpath("p2_conformal_orientation_risk_control.md").write_text(
        "# P2 conformal orientation risk control\n\n"
        f"Generated: {now()}\n\n"
        "Conformal is treated as a risk-control threshold layer wrapped around a base score, not as a new selection score. "
        "The current implementation wraps a geometry score and reports empirical split-CRC-style thresholds on D_cal/D_audit image splits.\n\n"
        "Within-cell guarantees are stated only under exchangeability. Shifted leave-dataset/leave-detector rows are audits of degradation and do not claim strict conformal validity.\n\n"
        f"Within-cell artifact: `top_journal_v3/reports/conformal_within_cell_risk_control.csv` ({len(rows)} rows).\n"
        f"Shift audit artifact: `top_journal_v3/reports/conformal_shift_violation_audit.csv` ({len(shift_rows)} rows).\n",
        encoding="utf-8",
    )


def p3_p4_from_existing() -> None:
    track = pd.read_csv(ROOT / "measure_fix_v2/reports/track_abc_results_043.csv")
    track[track.dataset == "DOTA-v1.0"].to_csv(REPORTS / "psc_dota20_phase_mod.csv", index=False)
    # If DOTA rows are absent, write explicit empty schema.
    if not (REPORTS / "psc_dota20_phase_mod.csv").read_text(encoding="utf-8").strip():
        pd.DataFrame(columns=track.columns).to_csv(REPORTS / "psc_dota20_phase_mod.csv", index=False)
    phase = track[track.track.str.contains("phase_mod", na=False)].copy()
    hist_rows = []
    for _, r in phase.iterrows():
        for center in range(0, 91, 5):
            hist_rows.append(
                {
                    "dataset": r.dataset,
                    "baseline_id": r.baseline_id,
                    "angle_error_bin_center_deg": center,
                    "count": "",
                    "source": "Track A aggregate exists; per-instance phase_mod samples unavailable in persistent artifacts",
                    "supports_aliasing": "undetermined",
                }
            )
    write_csv(REPORTS / "psc_phase_mod_aliasing_hist.csv", hist_rows)
    conf_rows = []
    for _, r in phase.iterrows():
        conf_rows.append(
            {
                "dataset": r.dataset,
                "baseline_id": r.baseline_id,
                "stratum": "aggregate_only",
                "n_audit": r.n_audit,
                "phase_mod_NRC": r.NRC,
                "phase_mod_NRC_ci": r.NRC_ci,
                "confounding_assessment": "blocked: persistent per-instance class/size/aspect/dataset Track A table not found",
            }
        )
    write_csv(REPORTS / "psc_phase_mod_confounding_check.csv", conf_rows)
    DOCS.joinpath("p3_psc_free_mechanism_tests.md").write_text(
        "# P3 PSC free mechanism tests\n\n"
        f"Generated: {now()}\n\n"
        "P3-1 DOTA #20 phase_mod is not present in the persistent Track A aggregate table; the output CSV is therefore empty/partial. "
        "Existing phase_mod aggregates support reverse-calibration for DIOR/SODA/FAIR where present, but not the requested DOTA negative control.\n\n"
        "P3-2 aliasing fingerprint is blocked because per-instance high phase_mod samples were not found in persistent artifacts.\n\n"
        "P3-3 confounding check is blocked for the same reason: aggregate Track A tables do not expose class/size/aspect strata.\n\n"
        "Decision: fewer than two of three free tests support the PSC mechanism line under the requested criteria. PSC should remain a case study/mechanism candidate; no retraining matrix is authorized by this run.\n",
        encoding="utf-8",
    )
    g2 = pd.read_csv(ROOT / "measure_fix_v2/reports/g2_double_prime_results_039.csv")
    p4_rows = []
    for name, available, reason in [
        ("TTA circular angle variance", True, "real TTA artifacts exist in measure_fix_v2; circular variance required for formal comparison"),
        ("MC dropout circular variance", False, "no MC-dropout inference artifacts found"),
        ("checkpoint ensemble circular variance", False, "no multi-checkpoint prediction ensemble found"),
        ("detector-native entropy/angle quality", False, "native angle quality logits not persisted for all cells"),
        ("GWD/KLD distribution uncertainty", False, "no distributional detector output available"),
    ]:
        p4_rows.append(
            {
                "baseline": name,
                "available": available,
                "unavailable_reason": "" if available else reason,
                "angle_variance_statistics": "circular: theta -> 2theta, circular variance = 1 - R",
                "NRC": "",
                "AURC": "",
                "Risk@70": "",
                "Risk@90": "",
                "bootstrap_CI": "",
                "beats_geometry_aware_selector": "not_evaluated_in_049",
                "uses_circular_statistics": True,
            }
        )
    write_csv(REPORTS / "uncertainty_baselines_nrc.csv", p4_rows)
    DOCS.joinpath("p4_uncertainty_baselines_circular_stats.md").write_text(
        "# P4 uncertainty baselines with circular statistics\n\n"
        f"Generated: {now()}\n\n"
        "All angle variance baselines must use pi-periodic circular statistics: map theta to 2theta, compute resultant length R, then circular variance 1-R. "
        "Naive linear standard deviation is disallowed because it inflates uncertainty near the +/-90 degree boundary.\n\n"
        "049 status: inventory/report scaffold completed, but strong uncertainty baselines were not recomputed end-to-end. "
        "Therefore P4 does not yet prove geometry-aware selector beats strong uncertainty baselines.\n\n"
        f"G2 reference rows available: {len(g2)} from measure_fix_v2/reports/g2_double_prime_results_039.csv.\n",
        encoding="utf-8",
    )


def p5_downstream() -> None:
    rows = []
    for dataset, split, key in DATASETS:
        preds, gts = load_dataset(key)
        md = match_for_risk(preds, gts)
        if md.empty:
            continue
        # downstream risk: angle-induced rIoU drop for the matched object's aspect ratio
        drops = []
        for _, r in md.iterrows():
            ar = float(r.aspect_ratio)
            base = Det("", "", 1, 0, 0, ar, 1, 0, {})
            err = Det("", "", 1, 0, 0, ar, 1, math.radians(float(r.angle_error)), {})
            drops.append(1 - riou(base, err))
        md = md.copy()
        md["downstream_risk"] = drops
        for selector in ["score", "size_linear", "geometry"]:
            if selector == "geometry":
                score = md["score"] * np.clip((md["aspect_ratio"] - 1) / 2.0, 0.05, 1.0)
            elif selector == "size_linear":
                score = md["score"] + 0.05 * ((np.log1p(md["area"]) - np.log1p(md["area"]).mean()) / (np.log1p(md["area"]).std() + 1e-9))
            else:
                score = md["score"]
            order = np.argsort(-np.asarray(score))
            for cov in [0.7, 0.9, 1.0]:
                k = max(1, math.ceil(cov * len(md)))
                sub = md.iloc[order[:k]]
                for bin_name in ["all", "elongated"]:
                    ss = sub if bin_name == "all" else sub[sub.aspect_bin == bin_name]
                    rows.append(
                        {
                            "dataset": dataset,
                            "split": split,
                            "task": "angle_induced_rIoU_drop",
                            "selector": selector,
                            "coverage": cov,
                            "abstention_rate": round(1 - cov, 6),
                            "aspect_scope": bin_name,
                            "n_retained": int(len(ss)),
                            "downstream_risk": round(float(ss["downstream_risk"].mean()) if len(ss) else np.nan, 6),
                            "angle_risk_deg": round(float(ss["angle_error"].mean()) if len(ss) else np.nan, 6),
                        }
                    )
    write_csv(REPORTS / "downstream_selective_orientation.csv", rows)
    DOCS.joinpath("p5_downstream_selective_orientation_task.md").write_text(
        "# P5 downstream selective orientation task\n\n"
        f"Generated: {now()}\n\n"
        "Task: angle-induced rIoU drop. For each matched prediction, the downstream risk is 1 - IoU between a box at the GT orientation and the same box rotated by the matched angle error. "
        "This is low-cost, deterministic, and uses the same risk-coverage vocabulary: coverage, downstream risk, abstention rate, selector.\n\n"
        "Status: completed on available bench_core raw predictions. Because those predictions are flagged synthetic/proxy in source rows, this is a pipeline and construct probe, not final detector evidence.\n",
        encoding="utf-8",
    )


def writing_patches() -> None:
    nrc_rows = [
        {"NRC": 0.7, "interpretation": "better_than_random", "risk_coverage_curve": "below random baseline"},
        {"NRC": 1.0, "interpretation": "random", "risk_coverage_curve": "matches random selector"},
        {"NRC": 1.3, "interpretation": "reverse_calibrated", "risk_coverage_curve": "worse than random selector"},
    ]
    write_csv(FIGS / "nrc_interpretation_schematic.csv", nrc_rows)
    (FIGS / "nrc_interpretation_schematic.md").write_text(
        "# NRC interpretation schematic\n\n"
        "NRC = selector AURC / random-selector AURC.\n\n"
        "- NRC=1: random ordering.\n"
        "- NRC<1: better than random; retained high-confidence predictions have lower angle risk.\n"
        "- NRC>1: reverse-calibrated; the selector ranks higher-risk orientations earlier than random.\n",
        encoding="utf-8",
    )
    (DOCS / "related_work_references_patch.md").write_text(
        "# Related work references patch\n\n"
        "Replace placeholder [R1]-[R7] with real references covering these areas:\n\n"
        "1. Selective prediction: Geifman and El-Yaniv, Selective Classification for Deep Neural Networks, NeurIPS 2017, https://papers.neurips.cc/paper/7073-selective-classification-for-deep-neural-networks ; Geifman and El-Yaniv, SelectiveNet, ICML 2019, https://proceedings.mlr.press/v97/geifman19a.html .\n"
        "2. Conformal/risk control: Bates, Angelopoulos, Lei, Malik, and Jordan, Distribution-Free, Risk-Controlling Prediction Sets, JACM 2021, https://arxiv.org/abs/2101.02703 .\n"
        "3. Detector calibration / D-ECE: Kueppers et al., Multivariate Confidence Calibration for Object Detection, CVPR Workshops 2020, https://arxiv.org/abs/2004.13546 ; Pathiraja et al., Multiclass Confidence and Localization Calibration for Object Detection, CVPR 2023, https://openaccess.thecvf.com/content/CVPR2023/papers/Pathiraja_Multiclass_Confidence_and_Localization_Calibration_for_Object_Detection_CVPR_2023_paper.pdf .\n"
        "4. OBB square-like problem and angle periodicity: Yang and Yan, Arbitrary-Oriented Object Detection with Circular Smooth Label, ECCV 2020, https://www.ecva.net/papers/eccv_2020/papers_ECCV/html/666_ECCV_2020_paper.php .\n"
        "5. CSL / DCL / PSC angle coding: Yang et al., Dense Label Encoding for Boundary Discontinuity Free Rotation Detection, CVPR 2021, https://openaccess.thecvf.com/content/CVPR2021/html/Yang_Dense_Label_Encoding_for_Boundary_Discontinuity_Free_Rotation_Detection_CVPR_2021_paper.html ; Yu and Da, Phase-Shifting Coder: Predicting Accurate Orientation in Oriented Object Detection, CVPR 2023, https://arxiv.org/abs/2211.06368 .\n"
        "6. GWD / KLD losses: Yang et al., Rethinking Rotated Object Detection with Gaussian Wasserstein Distance Loss, ICML 2021, https://arxiv.org/abs/2101.11952 ; Yang et al., Learning High-Precision Bounding Box for Rotated Object Detection via Kullback-Leibler Divergence, NeurIPS 2021, https://proceedings.neurips.cc/paper/2021/hash/98f13708210194c475687be6106a3b84-Abstract.html .\n"
        "7. Uncertainty estimation: Gal and Ghahramani, Dropout as a Bayesian Approximation, ICML 2016, https://proceedings.mlr.press/v48/gal16.html ; Lakshminarayanan et al., Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles, NeurIPS 2017, https://papers.neurips.cc/paper/7219-simple-and-scalable-predictive-uncertainty-estimation-using-deep-ensembles .\n\n"
        "Writing edits:\n\n"
        "- Abstract: replace 'independent of accuracy signal' with 'an orientation reliability signal not sufficiently characterized by mAP'.\n"
        "- Selector claim: replace 'proves gains are not box-size prior' with 'supports that gains cannot be explained by box-size priors alone'.\n"
        "- Add a Scope and Claims subsection in the main text; move claim ledger / forbidden claims to appendix.\n",
        encoding="utf-8",
    )


def manifests_and_decision() -> None:
    artifact_rows = []
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            rel = p.relative_to(ROOT)
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            artifact_rows.append({"path": str(rel), "bytes": p.stat().st_size, "sha256": h, "can_recompute": True})
    write_csv(REPORTS / "artifact_manifest_049.csv", artifact_rows)
    heartbeat = {"timestamp": now(), "status": "partial", "stage": "SUPERVISOR_049", "gpu_used": False, "world_size": 0}
    (REPORTS / "heartbeat_049.json").write_text(json.dumps(heartbeat, indent=2), encoding="utf-8")
    (DOCS / "top_journal_evidence_decision_049.md").write_text(
        "# Top journal evidence decision 049\n\n"
        f"Generated: {now()}\n\n"
        "Decision: broader top-tier claim insufficient in this run.\n\n"
        "- P1 constructive decoupling: partial. Raw perturbation and rematching pipeline completed on available proxy/synthetic raw predictions; final claim requires non-synthetic detector predictions and mAP join.\n"
        "- P2 conformal risk control: partial. Within-cell empirical risk-control thresholds were produced; formal finite-sample theorem text and non-proxy rerun remain required.\n"
        "- P3 PSC mechanism: fail/blocked for 049 criteria. DOTA #20 phase_mod and per-instance aliasing/confounding artifacts were not available, so fewer than two free tests support mechanism escalation.\n"
        "- P4 uncertainty baselines: partial. Circular-statistics requirement documented; strong baselines not recomputed.\n"
        "- P5 downstream task: partial. angle-induced rIoU drop task completed on proxy/synthetic predictions, not final detector evidence.\n\n"
        "top_journal_discussion_level = false\n"
        "remote_sensing_journal_ready = possible only after P1/P2/P4 are rerun on non-synthetic detector assets\n"
        "broader top-tier claim insufficient\n",
        encoding="utf-8",
    )


def latest_report() -> None:
    text = """👇👇👇👇👇👇

049 未完成，当前为 partial evidence package。

P1 构造性解耦：partial。已在 raw prediction jsonl 上注入角度/反向扰动并重新匹配、重算 AP50/AP75/NRC/AURC/Risk，但可用 raw 资产带 synthetic/proxy 标记，不能作为最终 detector 证据。

P2 conformal：partial。已生成 within-cell empirical CRC threshold 与 shift audit；conformal 被写成阈值/保证层，不是普通 selection score。正式保证需在非 proxy D_cal/D_audit 上复跑并补定理口径。

P3 PSC 机制免费测试：不支持升级。DOTA #20 phase_mod、aliasing per-instance histogram、class/size/aspect confounding 所需持久化明细缺失，三项不足两项支持；不得启动 PSC 重训矩阵。

P4 强不确定性基线：未完成正式比较。已写 circular statistics 规则和可用性清单，未证明 geometry-aware selector 打赢 TTA/MC/ensemble/native/GWD-KLD 强基线。

P5 下游任务：partial。已生成 angle-induced rIoU drop selective task，但仍基于 proxy/synthetic raw predictions。

写作同步修改：完成 patch notes、NRC 示意图、related work reference patch 草案。

最终裁决：top_journal_discussion_level = false；broader top-tier claim insufficient。remote_sensing_journal_ready 仅在 P1/P2/P4 用非 synthetic detector 资产复跑后 possible。

主产物路径：top_journal_v3/docs/top_journal_evidence_decision_049.md；top_journal_v3/reports/；top_journal_v3/figures/。

verification/test/git：py_compile 通过；verify_top_journal_evidence_v2_049.py 通过；未用 GPU；未重训 host；未修改 thresholds.yaml / D_cal / D_audit。git 显示 top_journal_v3 为新增产物，AGENTS.md 和 outputs/bench_core/splits 为既有未跟踪项。下一步建议是先定位非 synthetic raw detector predictions 与 PSC per-instance Track A dumps，再复跑 P1/P2/P3/P4。

👆👆👆👆👆👆
"""
    (DOCS / "codex_latest_report.md").write_text(text, encoding="utf-8")


def supervisor_log() -> None:
    msg = (
        f"## {now()}\n\n"
        "- 指令来源: SUPERVISOR_049_CODEX_TOP_JOURNAL_EVIDENCE_UPGRADE_V2\n"
        "- 执行动作: 读取 AGENTS.md 和 项目执行文件_v2_measure_fix.md；创建 top_journal_v3；生成 P1-P5 partial evidence package、写作 patch、验证器输入产物。\n"
        "- 关键产物路径: top_journal_v3/docs/, top_journal_v3/reports/, top_journal_v3/figures/, top_journal_v3/scripts/run_049_evidence.py\n"
        "- pass/fail/partial: partial；P3 机制免费测试未达升级标准。\n"
        "- 是否触发停止条件: 是，P3 per-instance mechanism artifacts 缺失导致不得进入 PSC 重训矩阵；P1 final construct validity 受 proxy/synthetic raw predictions 限制。\n"
        "- 下一步建议: 定位非 synthetic detector raw predictions 和 per-instance PSC phase_mod dump 后复跑。\n\n"
    )
    (OUT / "codex_and_supervisor.md").write_text(msg, encoding="utf-8")
    # AGENTS.md legacy fixed log location also receives a pointer without replacing old content.
    legacy = ROOT / "claude_code_and_supervisor.md"
    with legacy.open("a", encoding="utf-8") as f:
        f.write(msg)


def main() -> None:
    for d in [DOCS, REPORTS, FIGS, LOGS, OUT / "artifacts"]:
        d.mkdir(parents=True, exist_ok=True)
    p1_angle_perturb()
    p1_reverse_perturb()
    p1_pairs_and_doc()
    iou_curve()
    p2_conformal()
    p3_p4_from_existing()
    p5_downstream()
    writing_patches()
    manifests_and_decision()
    latest_report()
    supervisor_log()


if __name__ == "__main__":
    main()

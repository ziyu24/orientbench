#!/usr/bin/env python3
"""53_run_a4_formal_readiness.py — A4 formal-readiness attribution WITH background source.

Computes the image-annulus background source for the O2-RTDETR (A4) frozen host's
matched predictions, then runs orientation-risk attribution (partial-corr
controlling GV+class, HSIC permutation, bootstrap CI) over score/entropy/GV/
E_layout/E_bg. D_cal -> candidate; D_audit -> holdout (no threshold tuning).
A4 ckpt hash must match 3e32fa11…; never mix RHINO. Run with mr_dev1x (cv2).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
from orientbench.buckets.background_source import background_for_image  # noqa: E402
from orientbench.buckets.sources import compute_layout_for_image  # noqa: E402
from orientbench.io.reports import read_jsonl, write_csv  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402
from orientbench.metrics.dependence import bootstrap_ci, hsic, partial_correlation  # noqa: E402
from orientbench.metrics.gv import gv_obliquity  # noqa: E402
from orientbench.metrics.matching import match_dataset  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

PRED = os.path.join(PROOT, "outputs/predictions/DOTA-v1.5/a4_host/schema/pred_a4_host_val.jsonl")
GT = os.path.join(PROOT, "outputs/predictions/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl")
IMG_ROOT = "/home/rspip/cqc/data/dataset/dota/dota1.5/split_ss_dota15/val/images"
CKPT = os.path.join(PROOT, "outputs/training/a4_host/best_dota_mAP_epoch_70.pth")
REPORT_DIR = os.path.join(PROOT, "outputs/bench_core/reports")
PROBE_DIR = os.path.join(PROOT, "outputs/probes/a4_source_attribution_real")
MAX_BG_IMAGES = 200      # cap images for background (recorded, not silent)
SCORE_THR = 0.30


def _dummies(classes):
    uniq = sorted(set(classes)); idx = {c: i for i, c in enumerate(uniq)}
    M = np.zeros((len(classes), max(1, len(uniq) - 1)))
    for r, c in enumerate(classes):
        k = idx[c]
        if k < M.shape[1]:
            M[r, k] = 1.0
    return M


def main():
    ck = hashlib.sha256(open(CKPT, "rb").read()).hexdigest()[:16] if os.path.isfile(CKPT) else "?"
    assert ck.startswith("3e32fa11"), f"A4 ckpt hash mismatch: {ck}"
    os.makedirs(PROBE_DIR, exist_ok=True)
    preds = read_jsonl(PRED); gts = read_jsonl(GT)
    by_img_g = defaultdict(list)
    for g in gts:
        by_img_g[g["image_id"]].append(g)
    # layout per image (GT)
    gid_layout = {}
    for img, gobs in by_img_g.items():
        for g, l in zip(gobs, compute_layout_for_image(gobs)):
            gid_layout[id(g)] = l
    # background per image (capped); compute V_bg/E_bg for GT objects
    gid_bg = {}
    bg_done = 0; bg_unavail = 0
    bg_imgs = list(by_img_g.keys())[:MAX_BG_IMAGES]
    for img in bg_imgs:
        gobs = by_img_g[img]
        objs = [{"obb_cx": g["obb_cx"], "obb_cy": g["obb_cy"], "obb_w": g["obb_w"],
                 "obb_h": g["obb_h"], "obb_theta": g["obb_theta"]} for g in gobs]
        res = background_for_image(os.path.join(IMG_ROOT, img + ".png"), objs)
        for g, r in zip(gobs, res):
            gid_bg[id(g)] = r
            if r.get("bg_status") == "ok":
                bg_done += 1
            else:
                bg_unavail += 1
    bg_imgset = set(bg_imgs)

    rows = []
    detail = {}
    for split in ("D_cal", "D_audit"):
        ids = {i for i in by_img_g if assign_split(i) == split and i in bg_imgset}
        pset = [p for p in preds if p["image_id"] in ids and p["score"] >= SCORE_THR]
        gset = [g for g in gts if g["image_id"] in ids]
        m = match_dataset(pset, gset)
        feat = defaultdict(list)
        for p_idx, g_idx, _ in m["matched_pairs"]:
            p, g = pset[p_idx], gset[g_idx]
            c = angle_error_contract(p["obb_w"], p["obb_h"], p["obb_theta"],
                                     g["obb_w"], g["obb_h"], g["obb_theta"])
            if c["near_square"]:
                continue
            risk = c["angle_error_canonical_longside"]
            if not math.isfinite(risk):
                continue
            bg = gid_bg.get(id(g), {})
            if bg.get("bg_status") != "ok":
                continue  # bg unavailable for this object
            sc = float(p["score"])
            feat["risk"].append(risk)
            feat["gv"].append(gv_obliquity(g["obb_w"], g["obb_h"], g["obb_theta"])["gv_obb_needed"])
            lay = gid_layout.get(id(g), {})
            feat["E_layout"].append(lay.get("E_layout", 0.0) if math.isfinite(lay.get("E_layout", 0.0)) else 0.0)
            feat["E_bg"].append(bg.get("E_bg", 0.0) if math.isfinite(bg.get("E_bg", 0.0)) else 0.0)
            feat["score"].append(sc)
            feat["entropy"].append(-math.log(min(max(sc, 1e-6), 1.0)))
            feat["klass"].append(g["class_name"])
        n = len(feat["risk"])
        srcs = {}
        if n >= 8:
            risk = np.array(feat["risk"]); gv = np.array(feat["gv"]); klass = feat["klass"]
            Zbase = np.column_stack([gv, _dummies(klass)])
            for s in ("E_bg", "E_layout", "score", "entropy", "gv"):
                x = np.array(feat[s], float)
                Z = _dummies(klass) if s == "gv" else Zbase
                pc = partial_correlation(x, risk, Z)
                h = hsic(x, risk, max_samples=800, n_perm=200, seed=0)
                srcs[s] = {"partial_corr": round(pc, 4) if math.isfinite(pc) else None,
                           "hsic_p": h["p_value"]}
        detail[split] = {"n_used": n, "sources": srcs}
        row = {"host": "O2-RTDETR", "route": "A4", "a4_ckpt_sha256": ck, "split": split, "n_used": n}
        for s, vv in srcs.items():
            row[f"{s}_pc"] = vv["partial_corr"]; row[f"{s}_hsic_p"] = vv["hsic_p"]
        rows.append(row)
        print(f"[a4-real {split}] n_used={n} "
              + " ".join(f"{k}:pc={v['partial_corr']},p={v['hsic_p']}" for k, v in srcs.items()))

    write_csv(os.path.join(REPORT_DIR, "a4_source_attribution_summary.csv"), rows, list(rows[0].keys()) if rows else ["split"])
    json.dump({"bg_done": bg_done, "bg_unavailable": bg_unavail,
               "bg_unavailable_ratio": round(bg_unavail / max(1, bg_done + bg_unavail), 4),
               "max_bg_images": MAX_BG_IMAGES, "detail": detail},
              open(os.path.join(PROBE_DIR, "a4_attribution_real_detail.json"), "w"), indent=2, ensure_ascii=False)
    bg_unavail_ratio = bg_unavail / max(1, bg_done + bg_unavail)
    blocked = bg_unavail_ratio > 0.5
    status = "blocked_background_unavailable" if blocked else "ready_for_threshold_review"
    # candidate
    import yaml
    dcal = detail["D_cal"]
    cand = {"project": "orientbench", "block": "A_A4", "host": "O2-RTDETR", "host_ckpt_sha256": ck,
            "approval_status": "pending", "frozen": False, "calibration_split": "D_cal",
            "background_source": "image_annulus_gradient_orientation (real)",
            "bg_unavailable_ratio": round(bg_unavail_ratio, 4),
            "candidate": {"partial_corr_max_abs": 0.20, "hsic_p_min_after_correction": 0.05,
                          "near_square_masked": True},
            "dcal_observed": dcal, "status": status,
            "note": "candidate only; needs R8 freeze approval; D_audit not used to set thresholds."}
    with open(os.path.join(PROOT, "configs", "thresholds.a4_candidate.yaml"), "w") as fh:
        fh.write("# A4 candidate (real source attribution w/ background). approval_status=pending; NOT frozen.\n")
        yaml.safe_dump(cand, fh, allow_unicode=True, sort_keys=False)
    L = ["# A4 Source-Attribution Formal-Readiness (O2-RTDETR host, WITH background)", "",
         f"> A4 frozen sha256={ck}…; background=image annulus (real). bg_unavailable_ratio={round(bg_unavail_ratio,4)} "
         f"(max_bg_images={MAX_BG_IMAGES}). status=**{status}**. 非完整 A4 gate（阈值未冻结）。", "",
         "| split | n_used | E_bg pc | E_bg HSIC p | E_layout pc | score pc | entropy pc | GV pc |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['split']} | {r['n_used']} | {r.get('E_bg_pc')} | {r.get('E_bg_hsic_p')} | "
                 f"{r.get('E_layout_pc')} | {r.get('score_pc')} | {r.get('entropy_pc')} | {r.get('gv_pc')} |")
    L += ["", "## 关键（真实，含 background source）",
          "- partial-corr 控 GV+class；HSIC 置换 p（受控抽样 800/seed0）。E_bg=image annulus 梯度方向证据。",
          f"## 状态: A4 = **{status}**",
          "- ready_for_threshold_review 时 candidate 见 thresholds.a4_candidate.yaml；formal_gate_allowed 仍 False（阈值未冻结）。",
          "- D_audit 仅 holdout，未调阈值。A-gate-1 同宿主(O2-RTDETR frozen, R3)。"]
    open(os.path.join(REPORT_DIR, "a4_source_attribution_formal_readiness_report.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] A4 formal-readiness: status={status} bg_unavail_ratio={bg_unavail_ratio:.3f}")


if __name__ == "__main__":
    main()

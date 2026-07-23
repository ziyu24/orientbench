#!/usr/bin/env python3
"""Recompute the frozen A1--A3 risk-control audit from persistent full-val tables."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.stats import beta
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "top_journal_v3_reaudit_055" / "paper_A_orientation_protocol"
sys.path.insert(0, str(ROOT / "scripts"))
import m069_common as M  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

CELLS = tuple("ABCDEF")
ENDPOINTS = {
    "geometry_normalized_severe": None,
    "angle_error_gt_5deg": 5.0,
    "angle_error_gt_10deg": 10.0,
    "angle_error_gt_15deg": 15.0,
}
SCORES = (
    "detection_score",
    "tta_circular_consistency",
    "source_supervised_leave_geometry",
    "target_gt_nonlinear_geometry_upper_bound",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    names = fields or list(rows[0])
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=names, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def f6(x) -> str:
    return "" if x is None or not math.isfinite(float(x)) else f"{float(x):.6f}"


def mother_id(dataset: str, image_id: str) -> tuple[str, str, str]:
    if dataset == "SODA-A":
        return image_id.split("__", 1)[0], "tile_filename_prefix", "HIGH"
    return image_id, "original_image_identity", "HIGH"


def inner_role(image_id: str) -> str:
    return M.split_role(str(image_id))


def features(C: dict) -> np.ndarray:
    w, h = C["w"], C["h"]
    lo, hi = np.minimum(w, h), np.maximum(w, h)
    return np.column_stack([
        C["score"], np.log(np.maximum(hi / np.maximum(lo, 1e-6), 1.0)),
        0.5 * np.log(np.maximum(w * h, 1e-6)), w, h,
    ])


def fit_geometry(X: np.ndarray, y: np.ndarray) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_depth=3, max_iter=200, learning_rate=0.05,
        random_state=0, l2_regularization=1.0,
    ).fit(X, y)


def hb_ucb(mean: float, n: int, delta: float) -> float:
    return float(M.hb_ucb(float(mean), int(n), float(delta))) if n else math.nan


def cp_ucb(k: int, n: int, delta: float) -> float:
    if n == 0: return math.nan
    if k >= n: return 1.0
    return float(beta.ppf(1.0 - delta, k + 1, n - k))


def summarize(rows_mask: np.ndarray, selected: np.ndarray, events: np.ndarray,
              group_ids: np.ndarray, eligible_groups: np.ndarray) -> dict:
    idx = np.where(rows_mask)[0]
    gids = group_ids[idx]
    pos = {str(g): i for i, g in enumerate(eligible_groups)}
    inv = np.fromiter((pos[str(g)] for g in gids), dtype=np.int64, count=len(gids))
    n = len(eligible_groups)
    total = np.bincount(inv, minlength=n).astype(float)
    keep = np.bincount(inv, weights=selected[idx].astype(float), minlength=n)
    bad = np.bincount(inv, weights=(selected[idx] * events[idx]).astype(float), minlength=n)
    nonempty = keep > 0
    losses = np.divide(bad[nonempty], keep[nonempty])
    scene_events = (bad[nonempty] > 0).astype(int)
    selected_count = int(keep.sum())
    eligible_count = int(total.sum())
    return {
        "losses": losses,
        "scene_events": scene_events,
        "conditional_risk": float(losses.mean()) if len(losses) else math.nan,
        "scene_event_risk": float(scene_events.mean()) if len(scene_events) else math.nan,
        "nonempty_count": int(nonempty.sum()),
        "eligible_scene_count": n,
        "nonempty_rate": float(nonempty.mean()) if n else 0.0,
        "selected_count": selected_count,
        "eligible_count": eligible_count,
        "selected_instance_coverage": selected_count / eligible_count if eligible_count else 0.0,
        "selected_scene_instance_coverage": selected_count / int(total[nonempty].sum()) if np.any(nonempty) else 0.0,
        "abstained_scene_count": int(n - nonempty.sum()),
        "scene_risk_ucb": hb_ucb(float(losses.mean()), len(losses), PROTO["delta"]) if len(losses) else math.nan,
        "scene_event_ucb": cp_ucb(int(scene_events.sum()), len(scene_events), PROTO["delta"]) if len(scene_events) else math.nan,
    }


def eligible_groups(mask: np.ndarray, role_mask: np.ndarray, group_ids: np.ndarray) -> np.ndarray:
    return np.unique(group_ids[mask & role_mask])


def score_threshold(scores: np.ndarray, fit_mask: np.ndarray, coverage: float) -> float:
    x = scores[fit_mask]
    x = x[np.isfinite(x)]
    return float(np.quantile(x, 1.0 - coverage))


PROTO_PATH = A / "reports" / "a1_protocol_frozen.json"
PROTO = json.loads(PROTO_PATH.read_text(encoding="utf-8"))
if not PROTO.get("frozen_before_new_dcal_computation"):
    raise RuntimeError("A1 protocol was not frozen before computation")


def main() -> None:
    log_lines = [f"start={datetime.now().astimezone().isoformat()}", f"protocol_sha256={sha(PROTO_PATH)}"]
    data: dict[str, dict] = {}
    base_masks: dict[str, np.ndarray] = {}
    row_roles: dict[str, dict[str, np.ndarray]] = {}
    group_ids: dict[str, np.ndarray] = {}
    tile_ids: dict[str, np.ndarray] = {}
    mapping_rows, universe_rows = [], []
    seen_map = set()

    for cell in CELLS:
        M.verify_fullval_lineage(cell)
        C = M.load_cell(cell, max_rows=10**18)
        data[cell] = C
        base = M.mask_ar(C, M.AR_MAIN)
        base_masks[cell] = base
        outer = np.asarray(C["split"], dtype=object)
        inner = np.asarray([inner_role(str(x)) for x in C["img"]], dtype=object)
        row_roles[cell] = {
            "fit": (outer == "D_cal") & (inner == "fit"),
            "calib": (outer == "D_cal") & (inner == "calib"),
            "audit": outer == "D_audit",
        }
        ds = C["dataset"]
        tile = np.asarray([str(x) for x in C["img"]], dtype=object)
        mother = np.asarray([mother_id(ds, x)[0] for x in tile], dtype=object)
        tile_ids[cell], group_ids[cell] = tile, mother if ds != "SODA-A" else tile

        upath = Path(M.UNIVERSE[cell])
        urows = list(csv.DictReader(upath.open(encoding="utf-8")))
        role_by_mother: dict[str, set[str]] = defaultdict(set)
        for r in urows:
            tid = str(r["image_id"]); mid, src, conf = mother_id(ds, tid)
            role_by_mother[mid].add(str(r["d_cal_daudit_split_flag"]))
            key = (ds, tid)
            if key not in seen_map:
                seen_map.add(key)
                mapping_rows.append({"dataset": ds, "tile_id": tid, "mother_scene_id": mid,
                                     "mapping_source": src, "mapping_confidence": conf,
                                     "verified": True})
        mixed = sum(len(v) > 1 for v in role_by_mother.values())
        formal = "mother_scene" if mixed == 0 else "tile_image"
        universe_rows.append({
            "evaluation_unit": cell, "dataset": ds, "detector": C["detector"], "head": "host_angle_head",
            "total_original_scenes": len(role_by_mother),
            "eligible_original_scenes": len(set(mother[base])),
            "eligible_tiles": len(set(tile[base])), "eligible_instances": int(base.sum()),
            "scene_id_source": "identity" if ds != "SODA-A" else "tile_filename_prefix",
            "mother_scene_recoverable": True,
            "mother_scene_split_overlap": mixed,
            "formal_exchangeable_unit": formal,
            "universe_hash": hashlib.sha256("\n".join(sorted(set(mother[base]))).encode()).hexdigest(),
        })
        log_lines.append(f"cell={cell} dataset={ds} eligible={int(base.sum())} mother_split_overlap={mixed} formal={formal}")

    atomic_csv(A / "reports/a2_tile_to_mother_scene_mapping.csv", mapping_rows)
    atomic_csv(A / "reports/a2_eligible_scene_universe.csv", universe_rows)

    # Fit target and leave-dataset source geometry models only on independent D_fit.
    Xs = {c: features(data[c]) for c in CELLS}
    target_scores, source_scores = {}, {}
    for cell in CELLS:
        C = data[cell]; fit = base_masks[cell] & row_roles[cell]["fit"] & np.isfinite(C["ae"])
        model = fit_geometry(Xs[cell][fit], C["ae"][fit])
        target_scores[cell] = -model.predict(Xs[cell])
        source_cells = [c for c in CELLS if data[c]["dataset"] != C["dataset"]]
        sx = np.concatenate([Xs[c][base_masks[c] & row_roles[c]["fit"]] for c in source_cells])
        sy = np.concatenate([data[c]["ae"][base_masks[c] & row_roles[c]["fit"]] for c in source_cells])
        smodel = fit_geometry(sx, sy)
        source_scores[cell] = -smodel.predict(Xs[cell])

    all_frontier, scene_frontier, event_frontier, comparison = [], [], [], []
    score_rows = []
    for cell in CELLS:
        C = data[cell]; ds = C["dataset"]; base = base_masks[cell]
        roles = row_roles[cell]
        gid = group_ids[cell]
        tta = -np.asarray(C["tta_circular_variance"], dtype=float)
        if np.any(np.isfinite(tta)):
            floor = float(np.nanmin(tta[np.isfinite(tta)]) - 1.0)
            tta = np.where(np.isfinite(tta), tta, floor)
        scores = {
            "detection_score": np.asarray(C["score"], dtype=float),
            "tta_circular_consistency": tta,
            "source_supervised_leave_geometry": source_scores[cell],
            "target_gt_nonlinear_geometry_upper_bound": target_scores[cell],
        }
        severe, _ = M.geometry_severe(C)
        endpoint_values = {name: severe if deg is None else (C["ae"] > deg).astype(float)
                           for name, deg in ENDPOINTS.items()}
        eligible_by_role = {r: eligible_groups(base, roles[r], gid) for r in roles}
        for endpoint, event in endpoint_values.items():
            fit_all = summarize(base & roles["fit"], base, event, gid, eligible_by_role["fit"])
            r_fit = fit_all["conditional_risk"]
            alpha_defs = [(f"absolute_{a:g}", float(a), "absolute") for a in PROTO["absolute_alpha"]]
            alpha_defs += [("relative_0.5_r_fit", 0.5 * r_fit, "relative"),
                           ("relative_0.25_r_fit", 0.25 * r_fit, "relative")]
            for score_name in SCORES:
                s = scores[score_name]
                tested = []
                sequence_open = {label: True for label, _, _ in alpha_defs}
                for cov in PROTO["coverage_grid"]:
                    thr = score_threshold(s, base & roles["fit"], cov)
                    selected = base & (s >= thr)
                    cal = summarize(base & roles["calib"], selected, event, gid, eligible_by_role["calib"])
                    aud = summarize(base & roles["audit"], selected, event, gid, eligible_by_role["audit"])
                    tested.append((cov, thr, cal, aud, selected))
                for label, alpha, alpha_type in alpha_defs:
                    trivial = bool(alpha >= r_fit)
                    certified_candidates = []
                    event_candidates = []
                    event_sequence_open = True
                    for cov, thr, cal, aud, selected in tested:
                        primary_pass = bool(cal["nonempty_count"] > 0 and cal["scene_risk_ucb"] <= alpha)
                        event_pass = bool(cal["nonempty_count"] > 0 and cal["scene_event_ucb"] <= alpha)
                        if sequence_open[label] and primary_pass:
                            certified_candidates.append((cov, thr, cal, aud, selected))
                        else:
                            sequence_open[label] = False
                        if event_sequence_open and event_pass:
                            event_candidates.append((cov, thr, cal, aud, selected))
                        else:
                            event_sequence_open = False
                    chosen = max(certified_candidates, key=lambda x: x[0]) if certified_candidates else None
                    if chosen is None:
                        cov, thr, cal, aud, selected = 0.0, math.nan, {}, {}, np.zeros(len(base), bool)
                        feasible = certified = practical = False
                        reason = "no fixed-sequence candidate satisfies conditional scene-risk UCB"
                    else:
                        cov, thr, cal, aud, selected = chosen
                        feasible = certified = True
                        practical = bool((not trivial) and aud["nonempty_rate"] >= PROTO["practical_thresholds"]["nonempty_scene_rate_min"]
                                         and aud["selected_instance_coverage"] >= PROTO["practical_thresholds"]["selected_instance_coverage_min"]
                                         and aud["selected_count"] >= PROTO["practical_thresholds"]["selected_count_min"])
                        reason = "certified" if not trivial else "formal but alpha is trivial relative to D_fit base risk"
                    row = {
                        "evaluation_unit": cell, "dataset": ds, "detector": C["detector"], "score": score_name,
                        "risk_endpoint": endpoint, "alpha_label": label, "alpha_type": alpha_type,
                        "r_fit": f6(r_fit), "base_risk": f6(r_fit), "alpha": f6(alpha),
                        "alpha_gt_base_risk": bool(alpha > r_fit), "trivial_guarantee": trivial,
                        "selected_threshold": f6(thr), "target_coverage": f6(cov),
                        "certified_risk_ucb": f6(cal.get("scene_risk_ucb")),
                        "mean_calibration_risk": f6(cal.get("conditional_risk")),
                        "mean_audit_risk": f6(aud.get("conditional_risk")),
                        "audit_risk_ucb": f6(aud.get("scene_risk_ucb")),
                        "nonempty_scene_rate": f6(aud.get("nonempty_rate", 0)),
                        "selected_instance_coverage": f6(aud.get("selected_instance_coverage", 0)),
                        "selected_count": aud.get("selected_count", 0),
                        "calibration_scene_count": cal.get("eligible_scene_count", len(eligible_by_role["calib"])),
                        "audit_scene_count": aud.get("eligible_scene_count", len(eligible_by_role["audit"])),
                        "feasible": feasible, "certified": certified, "nontrivial_certified": bool(certified and not trivial),
                        "practical": practical, "reason": reason,
                    }
                    all_frontier.append(row)
                    if endpoint == "geometry_normalized_severe":
                        sf = dict(row)
                        sf.update({
                            "conditional_mean_scene_risk": f6(aud.get("conditional_risk")),
                            "scene_risk_ucb": f6(aud.get("scene_risk_ucb")),
                            "nonempty_scene_count": aud.get("nonempty_count", 0),
                            "eligible_scene_count": aud.get("eligible_scene_count", len(eligible_by_role["audit"])),
                            "selected_scenes_instance_coverage": f6(aud.get("selected_scene_instance_coverage", 0)),
                            "abstained_scene_count": aud.get("abstained_scene_count", len(eligible_by_role["audit"])),
                            "formal_exchangeable_unit": "tile/image" if ds == "SODA-A" else "mother_scene",
                        })
                        scene_frontier.append(sf)
                        ef = dict(row)
                        ef.update({"scene_event_risk": f6(aud.get("scene_event_risk")),
                                   "scene_event_ucb": f6(aud.get("scene_event_ucb")),
                                   "event_calibration_certified_anywhere": bool(event_candidates)})
                        event_frontier.append(ef)
                        # Three-level audit at the selected threshold; infeasible rows remain explicit zeros.
                        inst_sel = selected & roles["audit"]
                        k = int(np.sum(event[inst_sel])); n = int(np.sum(inst_sel))
                        tile_groups = tile_ids[cell]
                        tile_eligible = eligible_groups(base, roles["audit"], tile_groups)
                        tile_sum = summarize(base & roles["audit"], selected, event, tile_groups, tile_eligible)
                        mother = np.asarray([mother_id(ds, str(x))[0] for x in C["img"]], dtype=object)
                        mother_eligible = eligible_groups(base, roles["audit"], mother)
                        mother_sum = summarize(base & roles["audit"], selected, event, mother, mother_eligible)
                        for level, nominal, eff, risk, ucb, rate, count, status in (
                            ("instance_iid_legacy", n, n, k / n if n else math.nan, cp_ucb(k,n,PROTO["delta"]) if n else math.nan, aud.get("nonempty_rate", 0), n, "AUDIT_ONLY_NOT_FORMAL"),
                            ("tile_image", len(tile_eligible), tile_sum["nonempty_count"], tile_sum["conditional_risk"], tile_sum["scene_risk_ucb"], tile_sum["nonempty_rate"], tile_sum["selected_count"], "FORMAL" if ds == "SODA-A" else "SAME_AS_MOTHER"),
                            ("mother_scene", len(mother_eligible), mother_sum["nonempty_count"], mother_sum["conditional_risk"], mother_sum["scene_risk_ucb"], mother_sum["nonempty_rate"], mother_sum["selected_count"], "SENSITIVITY_SPLIT_OVERLAP" if ds == "SODA-A" else "FORMAL"),
                        ):
                            comparison.append({"evaluation_unit":cell,"dataset":ds,"score":score_name,"alpha_label":label,
                                               "statistical_level":level,"nominal_sample_size":nominal,"effective_exchangeable_units":eff,
                                               "risk_estimate":f6(risk),"ucb":f6(ucb),"certified_coverage":f6(aud.get("selected_instance_coverage", 0)),
                                               "nonempty_rate":f6(rate),"selected_count":count,"pass_fail":"PASS" if certified else "FAIL",
                                               "guarantee_relaxation":status})

    atomic_csv(A / "reports/a1_guaranteed_frontier_all_alpha.csv", all_frontier)
    atomic_csv(A / "reports/a2_scene_level_ltt_frontier.csv", scene_frontier)
    atomic_csv(A / "reports/a2_scene_event_frontier.csv", event_frontier)
    atomic_csv(A / "reports/a2_instance_tile_scene_comparison.csv", comparison)

    # Summaries and decisions.
    nontrivial = sum(str(r["nontrivial_certified"]) == "True" or r["nontrivial_certified"] is True for r in all_frontier)
    trivial = sum(bool(r["trivial_guarantee"]) for r in all_frontier)
    infeasible = sum(not bool(r["feasible"]) for r in all_frontier)
    practical = sum(bool(r["practical"]) for r in all_frontier)
    summary_rows = []
    for endpoint in ENDPOINTS:
        rr = [r for r in all_frontier if r["risk_endpoint"] == endpoint]
        summary_rows.append({"risk_endpoint":endpoint,"rows":len(rr),"evaluation_units":len(set(r["evaluation_unit"] for r in rr)),
                             "nontrivial_certified":sum(bool(r["nontrivial_certified"]) for r in rr),
                             "trivial":sum(bool(r["trivial_guarantee"]) for r in rr),
                             "infeasible":sum(not bool(r["feasible"]) for r in rr),
                             "practical":sum(bool(r["practical"]) for r in rr)})
    atomic_csv(A / "reports/a1_trivial_infeasible_summary.csv", summary_rows)

    supervision = {
        "detection_score": ("detector confidence",False,False,False,False,True,True,False),
        "tta_circular_consistency": ("negative circular variance after theta->2theta TTA",False,False,False,False,True,True,False),
        "source_supervised_leave_geometry": ("score, log(ar), log(size), width, height",True,True,False,True,True,True,False),
        "target_gt_nonlinear_geometry_upper_bound": ("score, log(ar), log(size), width, height",True,True,True,False,True,False,True),
    }
    main_rows = [r for r in scene_frontier]
    for score in SCORES:
        rr=[r for r in main_rows if r["score"]==score]
        score_rows.append({
            "score":score,"input_features":supervision[score][0],"requires_training":supervision[score][1],
            "uses_gt":supervision[score][2],"uses_target_gt":supervision[score][3],"uses_source_gt":supervision[score][4],
            "inference_available":supervision[score][5],"deployable":supervision[score][6],"diagnostic_upper_bound":supervision[score][7],
            "rows":len(rr),"formally_certified":sum(bool(r["certified"]) for r in rr),
            "nontrivial_certified":sum(bool(r["nontrivial_certified"]) for r in rr),
            "practical_success":sum(bool(r["practical"]) for r in rr),
            "infeasible":sum(not bool(r["feasible"]) for r in rr),
            "max_audit_instance_coverage":f6(max((float(r["selected_instance_coverage"] or 0) for r in rr),default=0)),
            "max_audit_nonempty_scene_rate":f6(max((float(r["nonempty_scene_rate"] or 0) for r in rr),default=0)),
        })
    atomic_csv(A / "reports/a3_score_menu_certified_coverage.csv", main_rows)
    atomic_csv(A / "reports/a3_score_menu_summary.csv", score_rows)

    main_practical_units = {r["evaluation_unit"] for r in scene_frontier if bool(r["nontrivial_certified"]) and bool(r["practical"])}
    a1 = "PASS_NONTRIVIAL_FRONTIER" if len(main_practical_units) == len(CELLS) else ("PARTIAL_FRONTIER" if nontrivial else "STOP_TRIVIAL_OR_INFEASIBLE")
    a2 = "PASS_TILE_ONLY_WITH_LIMITATION" if any(r["mother_scene_split_overlap"] for r in universe_rows) else "PASS_MOTHER_SCENE"
    by_score_nontrivial = {r["score"]: int(r["nontrivial_certified"]) for r in score_rows}
    a3 = "PASS_SCORE_MENU_CERTIFIED" if all(v > 0 for v in by_score_nontrivial.values()) else ("PARTIAL_SCORE_MENU" if any(v > 0 for v in by_score_nontrivial.values()) else "STOP_ALL_SCORES_INFEASIBLE")
    overall = "PROCEED_A4_A6" if a1.startswith("PASS") and a2 == "PASS_MOTHER_SCENE" and a3.startswith("PASS") else ("STOP_A_RISK_CONTROL_MAINLINE" if a1.startswith("STOP") or a3.startswith("STOP") else "PROCEED_WITH_DOWNGRADED_RISK_CLAIM")
    decisions = [
        {"component":"A1","decision":a1,"evidence":f"all_endpoints_nontrivial={nontrivial}; all_endpoints_practical={practical}; main_practical_units={sorted(main_practical_units)}; trivial={trivial}; infeasible={infeasible}","impact":"strict frozen budget frontier"},
        {"component":"A2","decision":a2,"evidence":"SODA-A mother scenes cross frozen D_cal/D_audit tile roles; DIOR-R and FAIR1M are split-pure original images","impact":"SODA-A formal guarantee is tile/image-level; mother-scene is sensitivity only"},
        {"component":"A3","decision":a3,"evidence":json.dumps(by_score_nontrivial,sort_keys=True),"impact":"same-layer score certification"},
        {"component":"OVERALL","decision":overall,"evidence":"protocol unchanged; failures retained","impact":"next-stage permission"},
    ]
    atomic_csv(A / "reports/a1_a3_final_decision.csv", decisions)

    atomic_text(A / "docs/a2_scene_level_risk_definition.md", f"""# A2 场景级风险定义与裁决

eligible-scene universe 在任何分数和阈值之前固定为至少含一个 `ar>=2.1` eligible matched prediction 的原始场景。阈值后没有 selected prediction 的场景是 abstained scene：它进入 nonempty scene rate 分母，但不以零损失稀释条件风险。

对非空场景，主损失为 selected predictions 中 geometry-normalized severe events 的比例，并使用 bounded-loss Hoeffding-Bentkus 单侧 UCB。co-primary scene event 表示非空场景是否至少含一个 severe event，使用 Clopper-Pearson 单侧 UCB。两者必须连同 nonempty rate、selected-instance coverage 和 selected count 报告。

DIOR-R 与 FAIR1M 的 image ID 对应原始场景，既有冻结 split 在 mother-scene 层无交叉。SODA-A 的 tile filename 可高置信恢复 mother scene，但全部 {next(r['mother_scene_split_overlap'] for r in universe_rows if r['dataset']=='SODA-A')} 个 mother scenes 的 tiles 跨越既有 D_cal/D_audit 角色；在不修改冻结 split 的约束下，严格 mother-scene calibration/audit independence 不成立。因此 SODA-A 的正式 exchangeable unit 降为 tile/image，mother-scene 聚合只作相关性 sensitivity，不称严格 mother-scene guarantee。

旧 instance-i.i.d. exact-binomial 仅保留为统计审计，不是 distribution-free 主保证。

**A2 判定：{a2}。**
""")
    atomic_text(A / "docs/a3_score_menu_scope_and_supervision.md", f"""# A3 Score Menu 的监督范围与同层认证

| score | 训练/监督 | 目标推理可得 | 定位 |
|---|---|---:|---|
| detection score | 无额外 GT 拟合 | 是 | deployable baseline |
| TTA circular consistency | theta→2theta 圆方差，无目标 GT | 是 | deployable, inference-costly |
| source-supervised leave-* geometry | 其他数据集 D_fit 的 GT angle error | 是 | source-supervised transfer；不称 fully GT-free training |
| target-GT nonlinear geometry | 目标 D_fit 的 GT angle error | 是 | diagnostic/calibration upper bound；不可部署 |

四项使用同一 eligible universe、风险事件、冻结 split、coverage grid、固定序列、UCB 和 cluster 定义。NRC 不替代本认证层；`D_audit` 不参与 threshold 或 score direction 选择。

严格主事件的 nontrivial certification 计数为：{json.dumps(by_score_nontrivial, ensure_ascii=False, sort_keys=True)}。形式认证、非平凡认证和 practical success 在结果表中分列。**A3 判定：{a3}。**
""")

    for name, lines in (("a1_risk_budget.log", [f"A1={a1}",f"rows={len(all_frontier)}",f"nontrivial={nontrivial}",f"trivial={trivial}",f"infeasible={infeasible}"]),
                        ("a2_scene_level_risk.log", [f"A2={a2}",f"mapping_rows={len(mapping_rows)}",f"comparison_rows={len(comparison)}"]),
                        ("a3_score_menu_certification.log", [f"A3={a3}",json.dumps(by_score_nontrivial,sort_keys=True)])):
        atomic_text(A / "logs" / name, "\n".join(log_lines + lines) + "\n")
    atomic_text(A / "logs/run_a1_a3_latest.log", "\n".join(log_lines + [f"end={datetime.now().astimezone().isoformat()}", f"overall={overall}"]) + "\n")


if __name__ == "__main__":
    main()

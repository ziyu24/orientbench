"""m2_g2doubleprime_ar21.py — G2_double_prime under a matched-GT ar>=2.1 evaluation mask with FIXED
prediction-box area bins (small/medium/large, defined before any audit viewing). Per cell x size-bin: detection_score,
score+log(ar) linear, score+log(ar)+log(size) linear, nonlinear geometry. Linear/nonlinear fit on D_cal-fit
-> GT angle error (calibration/upper-bound); eval on D_audit. Paired NRC difference (nonlinear vs
score+ar+size linear) with image-cluster bootstrap CI + AURC/Risk diffs. Decision: does nonlinear geometry
survive fixed-size-bin control, >=2 cells consistent, bootstrap-supported, not single-bin/near-square driven.
"""
import os, sys, csv, json, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/scripts")
import m069_common as M
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage, aurc
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
DOC = f"{ROOT}/docs"
LOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/m069"
os.makedirs(LOG, exist_ok=True)
SIZE_BINS = ["small", "medium", "large"]
SIZE_BIN_BOUNDS = {
    "small": (0.0, 32.0 * 32.0),
    "medium": (32.0 * 32.0, 96.0 * 96.0),
    "large": (96.0 * 96.0, float("inf")),
}


def lg(m):
    open(f"{LOG}/m2.log", "a").write(f"[{time.strftime('%F %T')}] {m}\n"); print(m, flush=True)


def feats(C, idx, kind):
    w = C["w"][idx]; h = C["h"][idx]
    # Selector covariates must be prediction-time geometry.  ``C['ar']`` and
    # ``C['size']`` are deliberately the matched-GT geometry used to define the
    # well-posed evaluation region/event and must not enter a deployable feature.
    log_ar = np.log(C["pred_ar"][idx])
    log_sz = 0.5*np.log(C["pred_size"][idx])
    sc = C["score"][idx]
    if kind == "score_ar":
        return np.column_stack([sc, log_ar])
    if kind == "score_ar_size":
        return np.column_stack([sc, log_ar, log_sz])
    return np.column_stack([sc, log_ar, log_sz, w, h])  # nonlinear feature set


def linscore(C, fit_idx, eval_idx, kind):
    Xf = feats(C, fit_idx, kind); yf = C["ae"][fit_idx]
    ss = StandardScaler().fit(Xf)
    reg = LinearRegression().fit(ss.transform(Xf), yf)
    return -reg.predict(ss.transform(feats(C, eval_idx, kind)))


def nlscore(C, fit_idx, eval_idx):
    Xf = feats(C, fit_idx, "nl"); yf = C["ae"][fit_idx]
    reg = HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.05,
                                        random_state=0, l2_regularization=1.0).fit(Xf, yf)
    return -reg.predict(feats(C, eval_idx, "nl"))


def paired_nrc_diff_ci(imgs, s_a, s_b, risk, n=1000, seed=7):
    """bootstrap CI of NRC(s_a)-NRC(s_b) (a=linear, b=nonlinear); positive => nonlinear better."""
    imgs = np.asarray(imgs); uniq = np.unique(imgs); by = {u: np.where(imgs == u)[0] for u in uniq}
    rng = np.random.RandomState(seed)
    replicate_seeds = rng.randint(0, np.iinfo(np.int32).max, size=n)

    def replicate(rep_seed):
        local = np.random.RandomState(int(rep_seed))
        pick = local.choice(uniq, len(uniq), replace=True)
        idx = np.concatenate([by[u] for u in pick])
        if idx.size < 50:
            return float("nan")
        try:
            va = nrc_auc(s_a[idx], risk[idx])["nrc_auc"]; vb = nrc_auc(s_b[idx], risk[idx])["nrc_auc"]
            if np.isfinite(va) and np.isfinite(vb):
                return float(va - vb)
        except Exception:
            pass
        return float("nan")

    workers = min(max(1, int(os.environ.get("M069_BOOTSTRAP_WORKERS", "40"))), n)
    if workers == 1:
        vals = [value for value in map(replicate, replicate_seeds) if np.isfinite(value)]
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="m2-bootstrap") as pool:
            vals = [value for value in pool.map(replicate, replicate_seeds) if np.isfinite(value)]
    if not vals:
        return (float("nan"), float("nan"), float("nan"))
    return (round(float(np.mean(vals)), 4), round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4))


def run():
    rows = []; interval_rows = []
    for cell in M.FROZEN_CELLS:
        M.verify_fullval_lineage(cell)
        C = M.load_cell(cell)
        fit, cal, aud = M.role_masks(C)
        if np.any(~np.isfinite(C["pred_ar"])) or np.any(~np.isfinite(C["pred_size"])):
            raise RuntimeError(f"{cell}: nonfinite prediction geometry in formal matched rows")
        expected_bins = np.where(C["pred_size"] < 32.0**2, "small",
                                 np.where(C["pred_size"] < 96.0**2, "medium", "large"))
        if not np.array_equal(expected_bins, C["pred_size_bin"]):
            raise RuntimeError(f"{cell}: prediction size-bin labels disagree with frozen numeric bounds")
        base = M.mask_ar(C, M.AR_MAIN)
        for sb in SIZE_BINS:
            # ar>=2.1 is a matched-GT identifiability mask; the fixed size bin
            # and every fitted geometry covariate are prediction-side only.
            binm = base & (C["pred_size_bin"] == sb)
            fit_idx = np.where(binm & fit)[0]
            aud_idx = np.where(binm & aud)[0]
            lower, upper = SIZE_BIN_BOUNDS[sb]
            observed = C["pred_size"][binm]
            interval_rows.append(dict(
                cell=cell, size_bin=sb, lower_area_inclusive=lower,
                mask_definition="matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square",
                upper_area_exclusive=("inf" if not np.isfinite(upper) else upper),
                observed_size_min=(round(float(np.nanmin(observed)), 2) if observed.size else ""),
                observed_size_max=(round(float(np.nanmax(observed)), 2) if observed.size else ""),
                n_total=int(binm.sum()), n_fit=int(fit_idx.size), n_audit=int(aud_idx.size),
                status=("eligible" if fit_idx.size >= 150 and aud_idx.size >= 100 else "insufficient_preregistered_minimum"),
                frozen="canonical prediction-box area bins: <32^2, [32^2,96^2), >=96^2; fixed before audit",
            ))
            if fit_idx.size < 150 or aud_idx.size < 100:
                lg(f"{cell}/{sb} too few fit={fit_idx.size} aud={aud_idx.size} -> skip")
                continue
            risk = C["ae"][aud_idx]; imgs = C["img"][aud_idx]
            s_det = C["score"][aud_idx]
            s_lar = linscore(C, fit_idx, aud_idx, "score_ar")
            s_lars = linscore(C, fit_idx, aud_idx, "score_ar_size")
            s_nl = nlscore(C, fit_idx, aud_idx)
            def q(s):
                return round(float(nrc_auc(s, risk)["nrc_auc"]), 4)
            nrc_det, nrc_lar, nrc_lars, nrc_nl = q(s_det), q(s_lar), q(s_lars), q(s_nl)
            dmean, dlo, dhi = paired_nrc_diff_ci(imgs, s_lars, s_nl, risk)  # linear(score+ar+size) - nonlinear
            aurc_diff = round(float(aurc(s_lars, risk) - aurc(s_nl, risk)), 4)
            r70_diff = round(float(risk_at_coverage(s_lars, risk, 0.7) - risk_at_coverage(s_nl, risk, 0.7)), 4)
            r90_diff = round(float(risk_at_coverage(s_lars, risk, 0.9) - risk_at_coverage(s_nl, risk, 0.9)), 4)
            nl_better = bool(dlo > 0)
            rows.append(dict(cell=cell, dataset=C["dataset"], detector=C["detector"], size_bin=sb,
                             ar_threshold=M.AR_MAIN, n_instances=int(aud_idx.size),
                             mask_definition="matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square",
                             retained_count=int(aud_idx.size),
                             retained_ratio=(round(float(aud_idx.size / aud.sum()), 6) if aud.sum() else 0.0),
                             n_images=int(len(np.unique(imgs))), nrc_detection=nrc_det,
                             nrc_linear_score_ar=nrc_lar, nrc_linear_score_ar_size=nrc_lars,
                             nrc_nonlinear_geometry=nrc_nl, paired_nrc_diff_lin_minus_nl=dmean,
                             ci_lo=dlo, ci_hi=dhi, nonlinear_better_sig=nl_better,
                             aurc_diff=aurc_diff, risk70_diff=r70_diff, risk90_diff=r90_diff,
                             fit_target="target-domain GT angle error (calibration/upper-bound)",
                             evaluation_mask_geometry="matched_GT_aspect_ratio",
                             selector_geometry="prediction_box_only",
                             fixed_size_bin_geometry="prediction_box_area",
                             bootstrap_unit="evaluation_image_cluster",
                             bootstrap_replicates=1000,
                             source_lineage="m069_fullval_same_forward",
                             selector_fit_split="D_cal-fit", conformal_calibration_split="D_cal-calib (not used by M2)",
                             evaluation_split="D_audit"))
            lg(f"{cell}/{sb} det={nrc_det} lar={nrc_lar} lars={nrc_lars} nl={nrc_nl} diff={dmean}[{dlo},{dhi}] sig={nl_better}")
    with open(f"{REP}/m2_g2doubleprime_ar21.csv", "w", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(f"{REP}/m2_g2doubleprime_cell_bin_intervals.csv", "w", newline="") as f:
        if interval_rows:
            w = csv.DictWriter(f, fieldnames=list(interval_rows[0].keys())); w.writeheader(); w.writerows(interval_rows)
    # decision
    cells_ok = {}
    for r in rows:
        cells_ok.setdefault(r["cell"], []).append(r["nonlinear_better_sig"])
    # a cell "supports" if nonlinear beats score+ar+size linear in >=2 of its size bins (not single-bin driven)
    supporting = [c for c, v in cells_ok.items() if sum(v) >= 2]
    n_bins_total = len(rows); n_bins_sig = sum(1 for r in rows if r["nonlinear_better_sig"])
    passfail = "PASS" if (len(supporting) >= 2 and n_bins_sig >= 3) else "FAIL"
    verdict_note = ("fixed-size-bin 内 nonlinear geometry 稳定优于 score+ar+size linear，>=2 cells 且非单一 size-bin 驱动"
                    if passfail == "PASS" else
                    "固定 size bin 后优势不足（<2 cells 或多为单一 bin）-> geometry score 整体降附录，正文不主张 geometry-specific gain")
    with open(f"{REP}/m2_g2doubleprime_decision.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["decision", "supporting_cells", "n_bins_total", "n_bins_nonlinear_sig", "note"])
        w.writerow([passfail, "|".join(sorted(supporting)), n_bins_total, n_bins_sig, verdict_note])
    doc = [f"# M2：ar≥2.1 固定 size-bin 下的 G2_double_prime\n",
           f"- 主口径 ar≥2.1；size bins 为冻结的既有 small/medium/large（在查看 D_audit 前已定义）。",
           f"- ar≥2.1 是 matched-GT 的朝向可辨识性评估掩码；固定 size-bin 与 selector 的 ar/size/w/h 特征全部由预测框计算，不把 GT 几何作为 selector 输入。",
           f"- 比较 detection / score+log(ar) linear / score+log(ar)+log(size) linear / nonlinear geometry；线性与非线性同拆分、同 D_cal-fit 拟合目标（目标域 GT 角度误差 → calibration/upper-bound），D_audit 评估。",
           f"- 通过依据是配对 NRC 差（linear score+ar+size 减 nonlinear）图像级 bootstrap CI 下界>0，不采用 feature importance。",
           f"- 支持 cells（≥2 size-bin 显著）：{sorted(supporting) or '无'}；显著 bin 数 {n_bins_sig}/{n_bins_total}。",
           f"- **M2 判定：{passfail}** — {verdict_note}\n",
           "## cell × size-bin 结果（ar≥2.1）",
           "| cell | size-bin | n | det NRC | +ar linear | +ar+size linear | nonlinear | (lin−nl) diff [CI] | nl 更优? |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        doc.append(f"| {r['cell']} | {r['size_bin']} | {r['n_instances']} | {r['nrc_detection']} | "
                   f"{r['nrc_linear_score_ar']} | {r['nrc_linear_score_ar_size']} | {r['nrc_nonlinear_geometry']} | "
                   f"{r['paired_nrc_diff_lin_minus_nl']} [{r['ci_lo']},{r['ci_hi']}] | {r['nonlinear_better_sig']} |")
    open(f"{DOC}/m2_g2doubleprime_ar21_size_control.md", "w").write("\n".join(doc))
    print(f"M2_DONE {passfail} supporting={sorted(supporting)} sig_bins={n_bins_sig}/{n_bins_total}", flush=True)


if __name__ == "__main__":
    run()

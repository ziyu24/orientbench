"""m069_common.py — shared backbone for command 069: cell registry, matched-dump loader,
ar>=2.1 masking, frozen geometry-normalized severe event, image-level Hoeffding-Bentkus LTT,
image-cluster bootstrap, deterministic D_cal fit/calib re-split, theta->2theta circular stats.
Env: mr_dev1x. No detector retrain; frozen thresholds/splits untouched.
"""
import os, sys, json, math, hashlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np

ROOT = "/home/rspip/cqc/pro/study/orientbench"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/scripts")
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage, aurc
from derive_delta_theta_075 import load_interpolator

MT = f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
M069_FULL = f"{ROOT}/outputs/persistent_artifacts/m069_fullval_reliability"
# Legacy 052 uncertainty tables remain available only for provenance audits.  Main
# 069 computation reads phase/TTA fields from the same lineage-clean forward dump.
PHASE_CSV = f"{ROOT}/top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv"
TTA_CSV = f"{ROOT}/top_journal_v3/reports/tta_circular_variance_full_052.csv"
DOTA_CLEAN = f"{ROOT}/top_journal_v3_reaudit_055/reports/m_dota_clean_perinstance"  # produced by pipeline

# cell_key -> (dataset, detector_label, matched_jsonl_path, has_phase_mod)
CELLS = {
    "A": ("DIOR-R", "rotated_retinanet_psc", f"{M069_FULL}/A/matched_fullval.jsonl", True),
    "B": ("DIOR-R", "oriented_rcnn", f"{M069_FULL}/B/matched_fullval.jsonl", False),
    "C": ("DIOR-R", "rotated_rtmdet_s", f"{M069_FULL}/C/matched_fullval.jsonl", False),
    "D": ("FAIR1M-v1.0", "rotated_retinanet_psc", f"{M069_FULL}/D/matched_fullval.jsonl", True),
    "E": ("SODA-A", "rotated_retinanet_psc", f"{M069_FULL}/E/matched_fullval.jsonl", True),
    "F": ("SODA-A", "oriented_rcnn", f"{M069_FULL}/F/matched_fullval.jsonl", False),
    # DOTA clean full-val cells (per-instance dumped by pipeline step m_dota_dump)
    "G_dota_orcnn": ("DOTA-v1.0", "oriented_rcnn", f"{DOTA_CLEAN}/DOTA_orcnn.jsonl", False),
    "H_dota_rtmdet": ("DOTA-v1.0", "rotated_rtmdet_m", f"{DOTA_CLEAN}/DOTA_rtmdet.jsonl", False),
}
FROZEN_CELLS = ["A", "B", "C", "D", "E", "F"]
DOTA_CELLS = ["G_dota_orcnn", "H_dota_rtmdet"]
PSC_CELLS = ["A", "D", "E"]
UNIVERSE = {c: f"{M069_FULL}/{c}/image_universe.csv" for c in FROZEN_CELLS}
MANIFEST = {c: f"{M069_FULL}/{c}/manifest.json" for c in FROZEN_CELLS}
FULLVAL_EXPECTED = {
    "A": (11738, 124445), "B": (11738, 124445), "C": (11738, 124445),
    "D": (4362, 78644), "E": (22994, 449644), "F": (22994, 449644),
}

_DTH = load_interpolator()
def delta_theta_075(ar):
    return _DTH(ar)

AR_MAIN = 2.1
AR_SENS = [1.6, 1.3]


def _obb_wh(o):
    return float(o["obb_w"]), float(o["obb_h"])


CACHE_DIR = f"{ROOT}/top_journal_v3_reaudit_055/reports/m069_cellcache"
CACHE_SCHEMA_VERSION = "v2_pred_gt_geometry"


def _geometry_from_wh(width, height):
    """Return (long/short aspect ratio, area, fixed size bin) or NaNs.

    The full-val A--F writer stores its legacy ``aspect_ratio``/``size`` fields
    from the matched GT, whereas the DOTA writer historically stored those
    fields from the prediction.  Deriving both geometries from the serialized
    boxes here prevents that lineage difference from leaking into formal masks
    or selector features.
    """
    width, height = float(width), float(height)
    if not (math.isfinite(width) and math.isfinite(height)) or min(width, height) <= 0:
        return float("nan"), float("nan"), ""
    area = width * height
    aspect = max(width, height) / min(width, height)
    size_bin = "small" if area < 32.0**2 else ("medium" if area < 96.0**2 else "large")
    return aspect, area, size_bin


def load_cell(cell, max_rows=0):
    """Load a matched dump with explicit prediction and target geometry.

    ``ar``/``size``/``size_bin`` are the matched-GT evaluation geometry;
    ``pred_*`` fields are prediction-time selector geometry.  Keeping these
    roles explicit prevents the historically mixed A--F/DOTA serialized fields
    from changing the formal mask or leaking GT geometry into a selector.
    """
    ds, det, path, _ = CELLS[cell]
    if not max_rows:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cpath = f"{CACHE_DIR}/{cell}.{CACHE_SCHEMA_VERSION}.npz"
        if os.path.isfile(cpath) and os.path.getmtime(cpath) >= os.path.getmtime(path):
            z = np.load(cpath, allow_pickle=True)
            return {k: (str(z[k]) if k in ("dataset", "detector", "cell") else z[k]) for k in z.files}
    (score, ae, ar, nsq, size, img, split, w, h, cls, sbin, pid, phase, tta,
     gt_w, gt_h, pred_ar, pred_size, pred_sbin, gt_ar, gt_size, gt_sbin) = ([] for _ in range(22))
    n = 0
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            try:
                pw, ph = _obb_wh(d["pred_obb"])
            except Exception:
                pw, ph = float("nan"), float("nan")
            try:
                gw, gh = _obb_wh(d["gt_obb"])
            except Exception:
                gw, gh = float("nan"), float("nan")
            par, psz, psb = _geometry_from_wh(pw, ph)
            gar, gsz, gsb = _geometry_from_wh(gw, gh)
            # Formal region/event geometry is target geometry.  Fall back to the
            # serialized legacy fields only for artifacts that lack GT w/h.
            if not math.isfinite(gar):
                gar = float(d["aspect_ratio"])
            if not math.isfinite(gsz):
                gsz = float(d.get("size", float("nan")))
                gsb = str(d.get("size_bin", ""))
            score.append(float(d["score"]))
            ae.append(float(d["angle_error"]))
            ar.append(gar)
            nsq.append(bool(d["near_square"]))
            size.append(gsz)
            img.append(str(d["image_id"]))
            split.append(str(d.get("d_cal_daudit_split_flag", d.get("split", ""))))
            w.append(pw); h.append(ph); gt_w.append(gw); gt_h.append(gh)
            pred_ar.append(par); pred_size.append(psz); pred_sbin.append(psb)
            gt_ar.append(gar); gt_size.append(gsz); gt_sbin.append(gsb)
            cls.append(str(d.get("class", "")))
            sbin.append(gsb)
            pid.append(str(d.get("pred_id", n)))
            try:
                phase.append(float(d.get("phase_mod", float("nan"))))
            except (TypeError, ValueError):
                phase.append(float("nan"))
            try:
                tta.append(float(d.get("tta_circular_variance", float("nan"))))
            except (TypeError, ValueError):
                tta.append(float("nan"))
            n += 1
            if max_rows and n >= max_rows:
                break
    out = dict(cell=cell, dataset=ds, detector=det,
               score=np.array(score), ae=np.array(ae), ar=np.array(ar),
               near_square=np.array(nsq), size=np.array(size), img=np.array(img, dtype=object),
               split=np.array(split, dtype=object), w=np.array(w), h=np.array(h), pred_id=np.array(pid, dtype=object),
               cls=np.array(cls, dtype=object), size_bin=np.array(sbin, dtype=object),
               gt_w=np.array(gt_w), gt_h=np.array(gt_h),
               pred_ar=np.array(pred_ar), pred_size=np.array(pred_size),
               pred_size_bin=np.array(pred_sbin, dtype=object),
               gt_ar=np.array(gt_ar), gt_size=np.array(gt_size),
               gt_size_bin=np.array(gt_sbin, dtype=object),
               phase_mod=np.array(phase), tta_circular_variance=np.array(tta))
    if not max_rows:
        try:
            np.savez(f"{CACHE_DIR}/{cell}.{CACHE_SCHEMA_VERSION}.npz", **out)
        except Exception:
            pass
    return out


def load_universe(cell):
    """Return the complete per-cell image universe used by image-level risk."""
    import csv as _csv
    path = UNIVERSE[cell]
    if not os.path.isfile(path):
        raise FileNotFoundError(f"missing full image universe for {cell}: {path}")
    rows = list(_csv.DictReader(open(path)))
    if not rows:
        raise RuntimeError(f"empty image universe for {cell}: {path}")
    return dict(
        img=np.array([str(r["image_id"]) for r in rows], dtype=object),
        split=np.array([str(r["d_cal_daudit_split_flag"]) for r in rows], dtype=object),
        n_gt=np.array([int(r["n_gt"]) for r in rows]),
        n_predictions=np.array([int(r["n_predictions"]) for r in rows]),
        image_path=np.array([str(r.get("image_path", "")) for r in rows], dtype=object),
    )


def verify_fullval_lineage(cell):
    """Fail closed unless the persisted full-validation input and hashes agree."""
    if cell not in MANIFEST:
        return True
    import hashlib as _hashlib
    mp = MANIFEST[cell]
    if not os.path.isfile(mp):
        raise FileNotFoundError(f"missing full-val manifest for {cell}: {mp}")
    meta = json.load(open(mp))
    if meta.get("status") != "complete":
        raise RuntimeError(f"incomplete full-val manifest for {cell}: {meta.get('status')}")
    if meta.get("tta_enabled") is not True:
        raise RuntimeError(f"formal full-val artifact has TTA disabled for {cell}")
    for path, expected in ((CELLS[cell][2], meta.get("matched_sha256")),
                           (UNIVERSE[cell], meta.get("universe_sha256"))):
        h = _hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        if not expected or h.hexdigest() != expected:
            raise RuntimeError(f"lineage SHA mismatch for {cell}: {path}")
    if (meta.get("n_images"), meta.get("n_gt")) != FULLVAL_EXPECTED[cell]:
        raise RuntimeError(
            f"full-validation cardinality mismatch for {cell}: "
            f"{(meta.get('n_images'), meta.get('n_gt'))} != {FULLVAL_EXPECTED[cell]}"
        )
    return True


def join_phase_mod(cell):
    """image_id::pred_id -> phase_mod for a PSC cell (from frozen per-instance CSV)."""
    import csv as _csv
    ds, det, _, has = CELLS[cell]
    if not has:
        return {}
    want = {"A": "DIOR-R/22", "D": "FAIR1M-v1.0/24", "E": "SODA-A/23"}[cell]
    out = {}
    with open(PHASE_CSV) as f:
        for r in _csv.DictReader(f):
            if r["cell_id"] != want:
                continue
            try:
                out[f'{r["image_id"]}::{r["pred_id"]}'] = float(r["phase_mod"])
            except Exception:
                pass
    return out


def join_tta_neg_cv(cell):
    """image_id::pred_id -> -circular_variance (theta->2theta) selection score."""
    import csv as _csv
    want = {"A": "DIOR-R/22", "B": "DIOR-R/3", "C": "DIOR-R/61",
            "D": "FAIR1M-v1.0/24", "E": "SODA-A/23", "F": "SODA-A/4"}.get(cell)
    if want is None:
        return {}
    out = {}
    with open(TTA_CSV) as f:
        for r in _csv.DictReader(f):
            if r["cell_id"] != want:
                continue
            try:
                out[f'{r["image_id"]}::{r["pred_id"]}'] = -float(r["circular_variance"])
            except Exception:
                pass
    return out


# ---------------- masking ----------------
def mask_ar(C, thr):
    return (C["ar"] >= thr) & (~C["near_square"]) & np.isfinite(C["ae"])


def geometry_severe(C):
    """severe event: angle_error > delta_theta_0.75(ar). Vectorized over cell arrays."""
    dth = np.array([delta_theta_075(a) for a in C["ar"]])
    return (C["ae"] > dth).astype(float), dth


# ---------------- deterministic fit/calib re-split of D_cal ----------------
def split_role(img_id, seed="m069"):
    """Deterministic: D_cal images -> 'fit' or 'calib' by hash; stable across runs."""
    hh = hashlib.md5(f"{seed}:{img_id}".encode()).hexdigest()
    return "fit" if (int(hh[:8], 16) % 2 == 0) else "calib"


def role_masks(C):
    """Returns boolean masks: fit (D_cal-fit), calib (D_cal-calib), audit (D_audit)."""
    is_cal = C["split"] == "D_cal"
    is_aud = C["split"] == "D_audit"
    roles = np.array([split_role(i) for i in C["img"]])
    fit = is_cal & (roles == "fit")
    calib = is_cal & (roles == "calib")
    return fit, calib, is_aud


# ---------------- image-cluster bootstrap for NRC ----------------
def boot_nrc_ci(imgs, scores, risks, n=1000, seed=12345):
    imgs = np.asarray(imgs); scores = np.asarray(scores); risks = np.asarray(risks)
    uniq = np.unique(imgs); by = {u: np.where(imgs == u)[0] for u in uniq}
    rng = np.random.RandomState(seed)
    replicate_seeds = rng.randint(0, np.iinfo(np.int32).max, size=n)

    def replicate(rep_seed):
        local = np.random.RandomState(int(rep_seed))
        pick = local.choice(uniq, len(uniq), replace=True)
        idx = np.concatenate([by[u] for u in pick])
        if idx.size < 50:
            return float("nan")
        try:
            v = nrc_auc(scores[idx], risks[idx])["nrc_auc"]
            if np.isfinite(v):
                return float(v)
        except Exception:
            pass
        return float("nan")

    workers = min(max(1, int(os.environ.get("M069_BOOTSTRAP_WORKERS", "40"))), n)
    if workers == 1:
        raw = map(replicate, replicate_seeds)
        vals = [value for value in raw if np.isfinite(value)]
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="m069-bootstrap") as pool:
            vals = [value for value in pool.map(replicate, replicate_seeds) if np.isfinite(value)]
    if not vals:
        return (float("nan"), float("nan"))
    return (round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4))


# ---------------- Hoeffding-Bentkus UCB / LTT for bounded [0,1] loss ----------------
def _h1(a, b):
    a = min(max(a, 1e-12), 1 - 1e-12); b = min(max(b, 1e-12), 1 - 1e-12)
    return a * math.log(a / b) + (1 - a) * math.log((1 - a) / (1 - b))


def hb_pvalue(Rhat, alpha, n):
    """Hoeffding-Bentkus p-value for H0: true bounded-mean risk >= alpha, given empirical Rhat over n.
    Reject H0 (certify risk<alpha) if p<=delta. Rhat,alpha in [0,1]. Uses Bentkus binomial-of-bound
    (valid for bounded losses), NOT an exact binomial on the loss itself."""
    from scipy.stats import binom
    if n <= 0:
        return 1.0
    if Rhat >= alpha:
        return 1.0
    hoeff = math.exp(-n * _h1(Rhat, alpha))
    bentkus = math.e * binom.cdf(math.ceil(n * Rhat), n, alpha)
    return float(min(1.0, hoeff, bentkus))


def hb_ucb(Rhat, n, delta=0.10):
    """One-sided (1-delta) upper confidence bound on true risk given empirical Rhat over n (bounded [0,1])."""
    lo, hi = Rhat, 1.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if hb_pvalue(Rhat, mid, n) <= delta:  # can still reject at this alpha => ucb below mid
            hi = mid
        else:
            lo = mid
    return hi


def image_level_risk(loss_per_instance, retained_mask, img_ids):
    """L_I = fraction of retained instances in image I that are severe (empty -> 0).
    loss_per_instance: 0/1 severe flags over ALL instances (in the current mask region);
    retained_mask: which of those are retained by the score threshold. Returns (image_ids_arr, L_arr)."""
    imgs = np.asarray(img_ids)
    sev = np.asarray(loss_per_instance)
    ret = np.asarray(retained_mask)
    uniq = np.unique(imgs)
    L = np.zeros(len(uniq)); order = {}
    for k, u in enumerate(uniq):
        order[u] = k
    for u in uniq:
        idx = np.where(imgs == u)[0]
        r = ret[idx]
        if r.sum() == 0:
            L[order[u]] = 0.0
        else:
            L[order[u]] = float(sev[idx][r].mean())
    return uniq, L

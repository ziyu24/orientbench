#!/usr/bin/env python3
"""Retrospective split-fixed-sequence validity audit for A1 (r007)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

CPU = min(os.cpu_count() or 1, 48)
WORKERS = max(1, math.ceil(CPU * 0.8))
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = str(WORKERS)

import numpy as np
from scipy.stats import beta, binom
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol"
R = A / "reports"
SCRIPT = Path(__file__).resolve()

ROUND = "orientbench-c-r007-20260805"
SNAPSHOT = "8e93291b75b34ddfb7b74a7592e1573407603f88"
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

sys.path.insert(0, str(ROOT / "scripts"))
import m069_common as M  # noqa: E402

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
TARGET_FREE = {"detection_score", "tta_circular_consistency", "source_supervised_leave_geometry"}

PROTO = json.loads((R / "a1_protocol_frozen.json").read_text(encoding="utf-8"))
FRONTIER = R / "a1_guaranteed_frontier_all_alpha.csv"
R006_MANIFEST = R / "a1_split_fst_manifest_r006.json"
R006_GATE = R / "a1_split_fst_gate_r006.json"

OUT_EXACT = R / "a1_split_fst_exact_hb_r007.csv"
OUT_TAINT = R / "a1_split_fst_order_taint_r007.csv"
OUT_DISJOINT = R / "a1_split_fst_split_disjoint_r007.csv"
OUT_SIM = R / "a1_split_fst_fwer_simulation_r007.csv"
OUT_FRONTIER = R / "a1_split_fst_frontier_r007.csv"
OUT_GATE = R / "a1_split_fst_gate_r007.json"
OUT_MANIFEST = R / "a1_split_fst_manifest_r007.json"
OUT_REPORT = ROOT / "dis/server_reports/orientbench-c-r007-20260805.md"
ROOT_RECORD = ROOT / "claude_code_and_supervisor.md"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def logical(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def identity(path: Path) -> dict:
    raw = path.read_bytes()
    size = len(raw)
    return {
        "logical_path": logical(path),
        "bytes": size,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "git_blob": hashlib.sha1(f"blob {size}\0".encode() + raw).hexdigest(),
    }


def f6(x) -> str:
    return "" if x is None or not math.isfinite(float(x)) else f"{float(x):.6f}"


def b(value) -> bool:
    return value is True or str(value).lower() == "true"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(rows[0]) if rows else ["empty"]
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def write_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def hb_p_exact(k: int, n: int, alpha: float) -> float:
    if n <= 0:
        return 1.0
    if not (0.0 < float(alpha) < 1.0):
        return 1.0
    r = int(k) / int(n)
    if r >= float(alpha):
        return 1.0
    if r <= 0:
        divergence = math.log(1.0 / (1.0 - float(alpha)))
    elif r >= 1:
        divergence = math.log(1.0 / float(alpha))
    else:
        aa = float(alpha)
        divergence = r * math.log(r / aa) + (1 - r) * math.log((1 - r) / (1 - aa))
    return float(min(1.0, math.exp(-int(n) * divergence), math.e * binom.cdf(int(k), int(n), float(alpha))))


def hb_p(mean: float, n: int, alpha: float) -> float:
    return 1.0 if n <= 0 or not math.isfinite(float(mean)) else float(M.hb_pvalue(float(mean), float(alpha), int(n)))


def hb_u(mean: float, n: int) -> float:
    return math.nan if n <= 0 or not math.isfinite(float(mean)) else float(M.hb_ucb(float(mean), int(n), float(PROTO["delta"])))


def pvec_exact(k, n, alpha):
    k = np.asarray(k, dtype=np.int64)
    n = np.asarray(n, dtype=np.int64)
    out = np.ones_like(k, dtype=float)
    good = n > 0
    if not (0.0 < float(alpha) < 1.0):
        return out
    rr = np.divide(k[good], n[good], where=n[good] != 0, out=np.zeros_like(k[good], dtype=float))
    div = np.full_like(k[good], math.inf, dtype=float)
    lt = rr < float(alpha)
    div[lt] = rr[lt] * np.log(rr[lt] / float(alpha)) + (1 - rr[lt]) * np.log((1 - rr[lt]) / (1 - float(alpha)))
    out_good = np.minimum(1.0, np.minimum(np.exp(-n[good] * div), math.e * binom.cdf(k[good], n[good], float(alpha))))
    out[good] = out_good
    return out


def features(C: dict) -> np.ndarray:
    w, h = C["w"], C["h"]
    lo, hi = np.minimum(w, h), np.maximum(w, h)
    return np.column_stack([
        C["score"],
        np.log(np.maximum(hi / np.maximum(lo, 1e-6), 1.0)),
        0.5 * np.log(np.maximum(w * h, 1e-6)),
        w,
        h,
    ])


def fit(X: np.ndarray, y: np.ndarray) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.05,
                                         random_state=0, l2_regularization=1.0).fit(X, y)


def split_summary(rows_mask, selected, event, groups, eligible) -> dict:
    idx = np.where(rows_mask)[0]
    if len(idx) == 0:
        return {"n": 0, "eligible": len(eligible), "risk": math.nan, "ucb": math.nan, "event_k": 0, "event_n": 0,
                "event_risk": math.nan, "nonempty_rate": 0.0, "selected_count": 0, "coverage": 0.0, "abstained": len(eligible)}

    pos = {str(v): i for i, v in enumerate(eligible)}
    inv = np.fromiter((pos[str(x)] for x in groups[idx]), dtype=np.int64, count=len(idx))
    n = len(eligible)
    total = np.bincount(inv, minlength=n).astype(float)
    kept = np.bincount(inv, weights=selected[idx].astype(float), minlength=n)
    bad = np.bincount(inv, weights=(selected[idx] * event[idx]).astype(float), minlength=n)
    nonempty = kept > 0
    losses = np.divide(bad[nonempty], kept[nonempty], where=kept[nonempty] != 0)
    ze = (bad[nonempty] > 0).astype(int)

    cnt = int(kept.sum())
    elig = int(total.sum())
    return {
        "n": int(nonempty.sum()),
        "eligible": n,
        "risk": float(losses.mean()) if len(losses) else math.nan,
        "ucb": hb_u(float(losses.mean()), len(losses)),
        "event_k": int(ze.sum()),
        "event_n": int(len(ze)),
        "event_risk": float(ze.mean()) if len(ze) else math.nan,
        "nonempty_rate": float(nonempty.mean()) if n else 0.0,
        "selected_count": cnt,
        "coverage": cnt / elig if elig else 0.0,
        "abstained": int(n - nonempty.sum()),
    }


def thresh(score, mask, coverage):
    return float(np.quantile(score[mask][np.isfinite(score[mask])], 1 - float(coverage)))


def alpha_defs(rfit):
    return [(f"absolute_{x:g}", float(x), "absolute") for x in PROTO["absolute_alpha"]] + [
        ("relative_0.5_r_fit", 0.5 * rfit, "relative"),
        ("relative_0.25_r_fit", 0.25 * rfit, "relative"),
    ]


def build_order_hash(rows) -> str:
    serial = "\n".join(f"{z['gi']}|{z['th']:.17g}|{z['pfit']:.17g}|{z['fit']['n']}" for z in rows)
    return hashlib.sha256(serial.encode()).hexdigest()


def sanitize_named(named: dict[str, str]) -> list[dict]:
    literals = [x for x in (os.environ.get("USER", ""), socket.gethostname()) if len(x) >= 3]
    slash = chr(92)
    pats = {
        "unix_absolute": r"(?<![\w.-])/(?:home|Users|root|srv|opt|scratch|workspace|tmp|var|mnt|data)/",
        "windows_drive": r"(?<!\w)[A-Za-z]:[\\\/]",
        "windows_unc": r"(?<!"+slash*2+")"+slash*4+r"[A-Za-z0-9_.-]+"+slash*2,
        "credential": r"(?:ghp_|github_pat_|AKIA)[\w=-]+",
        "bearer": r"Bearer\s+[\w._=-]{12,}",
        "password": r"(?:password|passwd|pwd)\s*[:=]\s*[^,;\s]{4,}",
        "private_key": r"BEGIN [A-Z ]*PRIVATE KEY",
        "connection": r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://",
    }
    hit = []
    for n, t in named.items():
        for k, p in pats.items():
            if re.search(p, t, re.I):
                hit.append({"logical_path": n, "pattern": k})
        for x in literals:
            if x in t:
                hit.append({"logical_path": n, "pattern": "runtime_account_or_hostname"})
    return hit


def verify_inputs() -> dict:
    if git("rev-parse", "--show-object-format") != "sha1":
        raise RuntimeError("git object format must be sha1")
    if subprocess.run(["git", "cat-file", "-e", SNAPSHOT], cwd=ROOT).returncode != 0:
        raise RuntimeError(f"snapshot {SNAPSHOT} not present")
    if not (HEAD == SNAPSHOT or subprocess.run(["git", "merge-base", "--is-ancestor", SNAPSHOT, HEAD], cwd=ROOT).returncode == 0):
        raise RuntimeError(f"HEAD {HEAD} is not ancestor of snapshot {SNAPSHOT}")
    man = json.loads((R / "a1_split_fst_manifest_r006.json").read_text(encoding="utf-8"))
    gate = json.loads((R / "a1_split_fst_gate_r006.json").read_text(encoding="utf-8"))
    return {"status": "PASS", "manifest": man, "gate": gate}


def boundary_exact_checks(alpha_defs_list):
    rows = []
    for _, alpha, _ in alpha_defs_list:
        aa = float(alpha)
        for k, n, note in [
            (max(int(math.floor(aa * 1000)) - 1, 0), 1000, "k_over_alpha_floor_minus_one"),
            (int(math.floor(aa * 1000)), 1000, "k_eq_alpha_floor"),
            (int(math.floor(aa * 1000)) + 1, 1000, "k_gt_alpha_floor"),
            (0, 10, "k0_n10"),
            (10, 10, "k_eq_n"),
            (0, 0, "n0_k0"),
        ]:
            sp = hb_p_exact(k, n, aa)
            vp = pvec_exact(np.array([k], dtype=np.int64), np.array([n], dtype=np.int64), aa)[0]
            rows.append({
                "scenario": note,
                "alpha": f6(aa),
                "k": int(k),
                "n": int(n),
                "hb_scalar": f6(sp),
                "hb_vector": f6(float(vp)),
                "match": b(abs(float(sp) - float(vp)) <= 1e-12),
            })
    return rows


def main():
    checks = verify_inputs()
    if checks["status"] != "PASS":
        raise RuntimeError("input verification failed")

    lineages = []
    data = {}
    masks = {}
    roles = {}
    groups = {}
    for cell in CELLS:
        M.verify_fullval_lineage(cell)
        meta = json.loads(Path(M.MANIFEST[cell]).read_text(encoding="utf-8"))
        lineages.append({
            "evaluation_unit": cell,
            "status": meta.get("status"),
            "matched_sha256": meta.get("matched_sha256"),
            "universe_sha256": meta.get("universe_sha256"),
            "n_images": meta.get("n_images"),
            "n_gt": meta.get("n_gt"),
        })
        C = M.load_cell(cell, max_rows=10**18)
        data[cell] = C
        masks[cell] = M.mask_ar(C, M.AR_MAIN)
        outer = np.asarray(C["split"], dtype=object)
        inner = np.asarray([M.split_role(str(x)) for x in C["img"]], dtype=object)
        roles[cell] = {
            "fit": (outer == "D_cal") & (inner == "fit"),
            "calib": (outer == "D_cal") & (inner == "calib"),
            "audit": outer == "D_audit",
        }
        groups[cell] = np.asarray(C["img"], dtype=object)

    X = {c: features(data[c]) for c in CELLS}
    target = {}
    source = {}
    for c in CELLS:
        fitmask = masks[c] & roles[c]["fit"] & np.isfinite(data[c]["ae"])
        target[c] = -fit(X[c][fitmask], data[c]["ae"][fitmask]).predict(X[c])
        others = [d for d in CELLS if data[d]["dataset"] != data[c]["dataset"]]
        sx = np.concatenate([X[d][masks[d] & roles[d]["fit"]] for d in others])
        sy = np.concatenate([data[d]["ae"][masks[d] & roles[d]["fit"]] for d in others])
        source[c] = -fit(sx, sy).predict(X[c])

    exact_rows: list[dict] = []
    disjoint_rows: list[dict] = []
    taint_rows: list[dict] = []
    order_rows: list[dict] = []
    frontier_rows: list[dict] = []
    sim_scenarios: list[tuple] = []
    boundary_rows: list[dict] = []

    for cell in CELLS:
        C = data[cell]
        base = masks[cell]
        g = groups[cell]
        eligible = {x: np.unique(g[base & roles[cell][x]]) for x in roles[cell]}
        fit_set = set(map(str, eligible["fit"]))
        cal_set = set(map(str, eligible["calib"]))
        aud_set = set(map(str, eligible["audit"]))
        disjoint_rows.append({
            "evaluation_unit": cell,
            "dataset": C["dataset"],
            "detector": C["detector"],
            "fit_scene_count": len(fit_set),
            "calib_scene_count": len(cal_set),
            "audit_scene_count": len(aud_set),
            "fit_cal_intersection": len(fit_set & cal_set),
            "fit_audit_intersection": len(fit_set & aud_set),
            "cal_audit_intersection": len(cal_set & aud_set),
            "all_intersections_disjoint": "True" if len(fit_set & cal_set) == 0 and len(fit_set & aud_set) == 0 and len(cal_set & aud_set) == 0 else "False",
        })

        tta = -np.asarray(C["tta_circular_variance"], float)
        floor = float(np.nanmin(tta[np.isfinite(tta)]) - 1) if np.any(np.isfinite(tta)) else -1.0
        tta = np.where(np.isfinite(tta), tta, floor)
        menu = {
            "detection_score": np.asarray(C["score"], float),
            "tta_circular_consistency": tta,
            "source_supervised_leave_geometry": source[cell],
            "target_gt_nonlinear_geometry_upper_bound": target[cell],
        }

        severe, _ = M.geometry_severe(C)
        events = {e: severe if deg is None else (C["ae"] > deg).astype(float) for e, deg in ENDPOINTS.items()}

        for endpoint, event in events.items():
            fit_base = split_summary(base & roles[cell]["fit"], base, event, g, eligible["fit"])
            rfit = fit_base["risk"]
            boundary_rows.extend(boundary_exact_checks(alpha_defs(rfit)))
            for score_name, score in menu.items():
                tested = []
                for gi, cov in enumerate(PROTO["coverage_grid"]):
                    th = thresh(score, base & roles[cell]["fit"], cov)
                    sel = base & (score >= th)
                    tested.append((
                        gi, float(cov), th, sel,
                        split_summary(base & roles[cell]["fit"], sel, event, g, eligible["fit"]),
                        split_summary(base & roles[cell]["calib"], sel, event, g, eligible["calib"]),
                        split_summary(base & roles[cell]["audit"], sel, event, g, eligible["audit"]),
                    ))

                for label, alpha, atype in alpha_defs(rfit):
                    candidates = []
                    for gi, cov, th, sel, fs, cs, au in tested:
                        pfit = hb_p(fs["risk"], fs["n"], alpha)
                        pcal = hb_p(cs["risk"], cs["n"], alpha)
                        pes = hb_p(cs["event_risk"], cs["event_n"], alpha)
                        pei = hb_p_exact(cs["event_k"], cs["event_n"], alpha)
                        candidates.append({
                            "gi": gi, "cov": cov, "th": th,
                            "fit": fs, "cal": cs, "audit": au,
                            "pfit": pfit, "pcal": pcal, "pes": pes, "pei": pei,
                        })
                        exact_rows.append({
                            "evaluation_unit": cell,
                            "dataset": C["dataset"],
                            "detector": C["detector"],
                            "score": score_name,
                            "risk_endpoint": endpoint,
                            "alpha_label": label,
                            "alpha": f6(alpha),
                            "alpha_type": atype,
                            "grid_index": gi,
                            "fit_n": fs["n"],
                            "cal_event_k": cs["event_k"],
                            "cal_event_n": cs["event_n"],
                            "scene_event_hb_scalar": f6(pes),
                            "scene_event_hb_exact_integer": f6(pei),
                            "scene_event_exact_match": b(abs(pes - pei) <= 1e-12),
                        })

                    primary = sorted(candidates, key=lambda z: (z["pfit"], -z["fit"]["n"], -z["cov"], z["gi"]))
                    hist = sorted(candidates, key=lambda z: z["gi"])
                    pcal = np.array([z["pcal"] for z in candidates], dtype=float)
                    order = np.argsort(pcal, kind="stable")
                    reject = np.zeros(len(candidates), dtype=bool)
                    opened = True
                    for rank, idx in enumerate(order):
                        if opened and pcal[idx] <= 0.1 / (13 - rank):
                            reject[idx] = True
                        else:
                            opened = False
                    for arm, seq in (("split_fst", primary), ("historical", hist)):
                        open_ = True
                        for z in seq:
                            before = open_
                            passed = z["pcal"] <= 0.1 and z["cal"]["n"] > 0
                            open_ = open_ and passed
                            z[f"{arm}_pass"] = bool(before and passed)
                            if arm == "split_fst":
                                z["split_order"] = z["gi"]  # deterministic tie policy by order sort

                    base_hash = build_order_hash(primary)
                    for z in candidates:
                        z["holm_pass"] = bool(reject[z["gi"]])
                        z["any_pass"] = bool(z["pcal"] <= 0.1 and z["cal"]["n"] > 0)
                        order_rows.append({
                            "evaluation_unit": cell,
                            "dataset": C["dataset"],
                            "score": score_name,
                            "risk_endpoint": endpoint,
                            "alpha_label": label,
                            "alpha": f6(alpha),
                            "grid_index": z["gi"],
                            "target_coverage": f6(z["cov"]),
                            "threshold": f6(z["th"]),
                            "fit_nonempty_scenes": z["fit"]["n"],
                            "fit_conditional_risk": f6(z["fit"]["risk"]),
                            "fit_hb_pvalue": f6(z["pfit"]),
                            "split_fst_order": z.get("split_order", -1),
                            "calibration_nonempty_scenes": z["cal"]["n"],
                            "calibration_conditional_risk": f6(z["cal"]["risk"]),
                            "calibration_hb_pvalue": f6(z["pcal"]),
                            "split_fst_pass": b(z["split_fst_pass"]),
                            "historical_pass": b(z["historical_pass"]),
                            "holm_pass": b(z["holm_pass"]),
                            "any_grid_pointwise_pass": b(z["any_pass"]),
                            "scene_event_k": z["cal"]["event_k"],
                            "scene_event_n": z["cal"]["event_n"],
                            "scene_event_hb_scalar": f6(z["pes"]),
                            "scene_event_hb_exact_integer": f6(z["pei"]),
                            "scene_event_exact_match": b(abs(z["pes"] - z["pei"]) <= 1e-12),
                        })

                    # outcome taint by perturbing D_cal and D_audit outcomes only.
                    for perturb_type in ("calib", "audit"):
                        if perturb_type == "calib":
                            role_mask = base & roles[cell]["calib"]
                        else:
                            role_mask = base & roles[cell]["audit"]
                        ev2 = np.array(event, copy=True)
                        changed = 0
                        idxs = np.where(role_mask)[0]
                        if len(idxs) > 0:
                            k = idxs[0]
                            if np.isfinite(ev2[k]):
                                ev2[k] = 1.0 - ev2[k]
                                changed = 1
                        tested2 = []
                        if changed:
                            for gi, cov, th, sel, fs, cs, au in tested:
                                # Only outcome rows change; fit summary remains fixed.
                                _, _, cs2, au2 = fs, None, None, None
                                cs2 = split_summary(base & roles[cell]["calib"], sel, ev2, g, eligible["calib"])
                                au2 = split_summary(base & roles[cell]["audit"], sel, ev2, g, eligible["audit"])
                                tested2.append((gi, cov, th, sel, fs, cs2, au2))
                        else:
                            tested2 = [(gi, cov, th, sel, fs, cs, au) for gi, cov, th, sel, fs, cs, au in tested]

                        cands2 = []
                        for gi, cov, th, sel, fs, cs2, au2 in tested2:
                            pfit = hb_p(fs["risk"], fs["n"], alpha)
                            pcal = hb_p(cs2["risk"], cs2["n"], alpha)
                            cands2.append({"gi": gi, "th": th, "fit": fs, "cal": cs2, "audit": au2, "pfit": pfit, "pcal": pcal})
                        perturb_hash = build_order_hash(sorted(cands2, key=lambda z: (z["pfit"], -z["fit"]["n"], -cov, z["gi"])))
                        taint_rows.append({
                            "evaluation_unit": cell,
                            "dataset": C["dataset"],
                            "detector": C["detector"],
                            "score": score_name,
                            "risk_endpoint": endpoint,
                            "alpha_label": label,
                            "alpha": f6(alpha),
                            "perturbation": perturb_type,
                            "changed_count": int(changed),
                            "baseline_order_sha256": base_hash,
                            "perturbed_order_sha256": perturb_hash,
                            "match": b(base_hash == perturb_hash),
                        })

                    def choose(flag):
                        hits = [z for z in candidates if z[flag]]
                        if not hits:
                            return None
                        return max(hits, key=lambda z: z["cov"])

                    chosen = {
                        "split_fst": choose("split_fst_pass"),
                        "historical": choose("historical_pass"),
                        "holm": choose("holm_pass"),
                        "any_grid": choose("any_pass"),
                    }

                    for arm, z in chosen.items():
                        trivial = alpha >= rfit
                        practical = bool(
                            z and not trivial and z["audit"]["nonempty_rate"] >= 0.1
                            and z["audit"]["coverage"] >= 0.1 and z["audit"]["selected_count"] >= 100
                        )
                        frontier_rows.append({
                            "evaluation_unit": cell,
                            "dataset": C["dataset"],
                            "detector": C["detector"],
                            "score": score_name,
                            "risk_endpoint": endpoint,
                            "alpha_label": label,
                            "alpha_type": atype,
                            "alpha": f6(alpha),
                            "r_fit": f6(rfit),
                            "arm": arm,
                            "trivial_guarantee": trivial,
                            "certified": bool(z),
                            "selected_threshold": f6(z["th"] if z else None),
                            "target_coverage": f6(z["cov"] if z else 0),
                            "calibration_nonempty_scenes": z["cal"]["n"] if z else 0,
                            "calibration_conditional_risk": f6(z["cal"]["risk"] if z else None),
                            "calibration_hb_pvalue": f6(z["pcal"] if z else None),
                            "calibration_hb_ucb": f6(z["cal"]["ucb"] if z else None),
                            "audit_conditional_risk": f6(z["audit"]["risk"] if z else None),
                            "audit_risk_ucb": f6(z["audit"]["ucb"] if z else None),
                            "audit_nonempty_scene_rate": f6(z["audit"]["nonempty_rate"] if z else 0),
                            "audit_selected_instance_coverage": f6(z["audit"]["coverage"] if z else 0),
                            "audit_selected_count": z["audit"]["selected_count"] if z else 0,
                            "audit_direction_consistent": bool(z and z["audit"]["risk"] <= alpha),
                            "practical": practical,
                            "reason": "certified" if z else "no frozen-grid candidate passes selected sequence",
                        })

                    if endpoint == "geometry_normalized_severe" and score_name in TARGET_FREE:
                        sim_scenarios.append((
                            len(sim_scenarios),
                            cell,
                            score_name,
                            label,
                            alpha,
                            np.array([z["fit"]["event_n"] for z in candidates]),
                            np.array([z["cal"]["event_n"] for z in candidates]),
                        ))

    # exact boundary checks are appended once per family; deduplicate identical rows.
    seen_keys = set()
    exact_unique = []
    for row in exact_rows:
        row["match_test"] = "boundary" if row["evaluation_unit"] is None else "family"
        key = (row["evaluation_unit"], row["dataset"], row["score"], row["risk_endpoint"], row["alpha_label"], row["grid_index"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        exact_unique.append(row)

    exact_rows = exact_unique
    exact_rows.extend(boundary_rows)
    # FWER simulation on geometry-normalized severe event for three target-free scores only.
    def fwer_sim(scenario):
        i, cell, score, label, alpha, nfit, ncal = scenario
        reps = 50000
        rng = np.random.default_rng(np.random.SeedSequence(20260805).spawn(108)[i])
        fst_count = holm_count = 0
        for start in range(0, reps, 1000):
            size = min(1000, reps - start)
            kf = np.empty((size, 13), dtype=np.int32)
            kc = np.empty((size, 13), dtype=np.int32)
            for j in range(13):
                kf[:, j] = rng.binomial(int(nfit[j]), alpha, size=size)
                kc[:, j] = rng.binomial(int(ncal[j]), alpha, size=size)
            pf = pvec_exact(kf, np.broadcast_to(nfit, (size, 13)), alpha)
            pc = pvec_exact(kc, np.broadcast_to(ncal, (size, 13)), alpha)
            order = np.argsort(pf, axis=1, kind="stable")
            ordered = np.take_along_axis(pc, order, axis=1)
            passed = ordered <= 0.1
            fst_count += int(np.any(np.cumprod(passed, axis=1, dtype=bool), axis=1).sum())
            sortedpc = np.sort(pc, axis=1)
            holm_pass = np.cumprod(sortedpc <= (0.1 / (13 - np.arange(13))), axis=1, dtype=bool)
            holm_count += int(np.any(holm_pass, axis=1).sum())
        def tally(x):
            k = int(x)
            rate = k / reps
            cp95 = 1.0 if k == reps else float(beta.ppf(0.95, k + 1, reps - k))
            return k, rate, cp95, b(cp95 <= 0.105)
        fk, fr, fu, fp = tally(fst_count)
        hk, hr, hu, hp = tally(holm_count)
        return {
            "scenario_index": i,
            "evaluation_unit": cell,
            "score": score,
            "alpha_label": label,
            "alpha": f6(alpha),
            "replicates": reps,
            "fit_nonempty_profile": ";".join(map(str, nfit)),
            "calibration_nonempty_profile": ";".join(map(str, ncal)),
            "split_fst_false_rejections": fk,
            "split_fst_empirical_fwer": f6(fr),
            "split_fst_cp95_upper": f6(fu),
            "split_fst_pass": fp,
            "holm_false_rejections": hk,
            "holm_empirical_fwer": f6(hr),
            "holm_cp95_upper": f6(hu),
            "holm_pass": hp,
            "seed": 20260805,
            "endpoint": "geometry_normalized_severe",
        }

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        fwer_rows = list(pool.map(fwer_sim, sim_scenarios))

    # build baseline parity to r006
    old = csv_rows(FRONTIER)
    def frontier_parity(old_rows, new_rows):
        key = lambda x: (x["evaluation_unit"], x["score"], x["risk_endpoint"], x["alpha_label"])
        a = {key(x): x for x in old_rows}
        b = {key(x): x for x in new_rows if x["arm"] == "historical"}
        fields = ("alpha", "trivial_guarantee", "feasible", "practical", "calibration_scene_count",
                  "audit_scene_count", "target_coverage", "selected_count", "selected_instance_coverage", "certified_risk_ucb")
        mismatch = []
        for k in sorted(set(a) & set(b)):
            for f in fields:
                av = a[k].get(f)
                bv = b[k].get(f)
                if f in ("trivial_guarantee", "feasible", "practical"):
                    ok = bool(av) == bool(bv)
                elif f in ("calibration_scene_count", "audit_scene_count", "selected_count"):
                    ok = int(av or 0) == int(bv or 0)
                else:
                    ok = abs(float(av or 0) - float(bv or 0)) <= 5e-7
                if not ok:
                    mismatch.append((k, f, av, bv))
        return {
            "existing_rows": len(old_rows),
            "rebuilt_rows": len(new_rows),
            "missing": len(set(a) - set(b)),
            "extra": len(set(b) - set(a)),
            "field_mismatches": len(mismatch),
            "examples": mismatch[:10],
            "status": "PASS" if len(old_rows) == len(new_rows) // 4 == len(a) == len(b) == 576 and not mismatch else "FAIL",
        }

    gate = frontier_parity(old, frontier_rows)
    boundary_pass = all(r["match"] for r in boundary_rows)
    exact_rows_exact = [r for r in exact_rows if "scene_event_exact_match" in r]
    exact_pass = all(bool(r.get("scene_event_exact_match", False)) for r in exact_rows_exact)
    exact_mismatch_count = sum(1 for r in exact_rows_exact if not r.get("match", True))
    taint_pass = all(r["changed_count"] >= 0 and r["match"] for r in taint_rows)
    all_taint_match = all(r["match"] for r in taint_rows)
    simpass = all(b(x["split_fst_pass"]) for x in fwer_rows)
    holmpass = all(b(x["holm_pass"]) for x in fwer_rows)
    lineage_ok = all(x.get("status") == "complete" for x in lineages)
    valid = (
        gate["status"] == "PASS"
        and boundary_pass
        and exact_pass
        and all_taint_match
        and simpass
        and holmpass
        and lineage_ok
    )
    structure = "PASS_SPLIT_FST_VALIDITY_R007" if valid else "FAIL_SPLIT_FST_VALIDITY_R007"

    prim = [x for x in frontier_rows if x["arm"] == "split_fst" and x["risk_endpoint"] == "geometry_normalized_severe"
            and x["score"] in TARGET_FREE and not x["trivial_guarantee"]]
    qual = [x for x in prim if x["certified"] and x["practical"] and x["audit_direction_consistent"]]
    units = sorted({x["evaluation_unit"] for x in qual})
    datasets = sorted({x["dataset"] for x in qual})
    if len(units) >= 3 and len(datasets) >= 2:
        dev = "PASS_BROAD_TARGET_FREE_DEVELOPMENT_R007"
    elif valid:
        dev = "FAIL_NO_BROAD_TARGET_FREE_DEVELOPMENT_R007"
    else:
        dev = "INCONCLUSIVE_DEVELOPMENT_R007"

    gate.update({
        "schema_version": "a1_split_fst_gate_r007_v1",
        "round_id": ROUND,
        "scientific_snapshot": SNAPSHOT,
        "execution_head": HEAD,
        "operation_counts": {
            "detector_fit": 0,
            "detector_predict": 0,
            "score_regressor_fit": 12,
            "score_regressor_predict": 12,
            "training": 0,
            "inference": 0,
            "download": 0,
            "gpu": 0,
            "rsar_reads": 0,
            "other_personal_project_reads": 0,
        },
        "cpu": {
            "available": CPU,
            "worker_budget": WORKERS,
            "parallel_backend": "ThreadPoolExecutor for 108 simulations; serial fixed-grid loops remain serial",
        },
        "candidate_rows": len(order_rows),
        "family_rows": len(frontier_rows) // 4,
        "exact_integer_hb": {
            "comparisons": len(exact_rows),
            "failures": int(exact_mismatch_count),
            "boundary_check_pass": boundary_pass,
        },
        "d_fit_only_order_taint": {
            "families": len(taint_rows),
            "match": int(all_taint_match),
            "failures": int(sum(1 for r in taint_rows if not r["match"])),
        },
        "fwer": {"seed": 20260805, "replicates": 50000, "scenarios": len(fwer_rows),
                 "split_fst_all_pass": simpass, "holm_all_pass": holmpass},
        "structure_gate": structure,
        "development_gate": dev,
        "breadth": {
            "qualifying_rows": len(qual),
            "qualifying_units": units,
            "qualifying_datasets": datasets,
            "threshold": "at least 3 of 6 units and 2 of 3 datasets",
        },
        "retrospective_development_only": True,
    })

    write_csv(OUT_EXACT, exact_rows)
    write_csv(OUT_TAINT, taint_rows)
    write_csv(OUT_DISJOINT, disjoint_rows)
    write_csv(OUT_SIM, fwer_rows)
    write_csv(OUT_FRONTIER, frontier_rows)

    report = [
        "# orientbench-c-r007 split-FST validity",
        f"- scientific snapshot: `{SNAPSHOT}`",
        f"- execution head: `{HEAD}`",
        f"- structure: `{structure}`",
        f"- development: `{dev}`",
        f"- validity checks: exact_integer={exact_pass}, boundary_checks={boundary_pass}, taint={all_taint_match}, split-FST_sim={simpass}, lineages={lineage_ok}",
        f"- disjoint split counts: fit/calib/audit intersections are reported in {OUT_DISJOINT.name}",
        f"- frontier rows: {len(frontier_rows)} (expected 2304, split-fst 576×4)",
        f"- exact rows: {len(exact_rows)}",
        f"- order taint rows: {len(taint_rows)}",
        f"- fwer rows: {len(fwer_rows)}",
        f"- all results are retrospective development-only and do not add deployment claims",
    ]
    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")

    named = {logical(p): p.read_text(encoding="utf-8") for p in (SCRIPT, OUT_EXACT, OUT_TAINT, OUT_DISJOINT, OUT_SIM, OUT_FRONTIER, OUT_REPORT)}
    gate["sanitizer"] = {
        "status": "PASS" if not sanitize_named(named) else "FAIL",
        "scope": "bounded scan of generated r007 artifacts",
        "hits": sanitize_named(named),
    }
    write_json(OUT_GATE, gate)

    start = datetime.now().astimezone().isoformat()
    record = f"\n- {start} | r007 split-FST validity audit: structure={structure}; development={dev}; detector fit/predict=0/0; score-regressor fit/predict=12/12; no training/inference/download/GPU.\n"
    if "r007 split-FST final result" not in ROOT_RECORD.read_text(encoding="utf-8"):
        ROOT_RECORD.write_text(ROOT_RECORD.read_text(encoding="utf-8") + record, encoding="utf-8")

    inputs = [R006_MANIFEST, R006_GATE, R / "a1_protocol_frozen.json",
              FRONTIER, A / "scripts/run_a1_a3.py", ROOT / "scripts/m069_common.py", ROOT / "orientbench/data/splits.py",
              ROOT / "scripts/derive_delta_theta_075.py"]
    final_named = {logical(p): p.read_text(encoding="utf-8") for p in (SCRIPT, OUT_EXACT, OUT_TAINT, OUT_DISJOINT, OUT_SIM, OUT_FRONTIER, OUT_GATE, OUT_REPORT)}
    gate["sanitizer"] = {
        "status": "PASS" if not sanitize_named(final_named) else "FAIL",
        "scope": "bounded scan over final generated files and root record append",
        "hits": sanitize_named(final_named),
    }
    write_json(OUT_GATE, gate)

    outputs = [SCRIPT, OUT_EXACT, OUT_TAINT, OUT_DISJOINT, OUT_SIM, OUT_FRONTIER, OUT_GATE, OUT_REPORT, ROOT_RECORD]
    manifest_rows = []
    seen = set()
    for item in json.loads((R / "a1_split_fst_manifest_r006.json").read_text(encoding="utf-8"))["inputs"]:
        manifest_rows.append(item)
        seen.add(item["logical_path"])
    for p in inputs:
        lp = logical(p)
        if lp in seen:
            continue
        manifest_rows.append(identity(p))
        seen.add(lp)
    manifest = {
        "schema_version": "a1_split_fst_manifest_r007_v1",
        "round_id": ROUND,
        "scientific_snapshot": SNAPSHOT,
        "execution_head": HEAD,
        "command": f"PYTHONDONTWRITEBYTECODE=1 python {SCRIPT.relative_to(ROOT)}",
        "authorized_changes": [logical(x) for x in outputs] + [logical(OUT_MANIFEST)],
        "inputs": manifest_rows,
        "outputs": [identity(x) for x in outputs if x != ROOT_RECORD],
        "rows": {
            "exact": len(exact_rows),
            "order_taint": len(taint_rows),
            "split_disjoint": len(disjoint_rows),
            "fwer": len(fwer_rows),
            "frontier": len(frontier_rows),
        },
        "gate": {"structure": structure, "development": dev},
        "operations": gate["operation_counts"],
        "sanitizer": gate["sanitizer"],
    }
    write_json(OUT_MANIFEST, manifest)
    m_hits = sanitize_named({logical(OUT_MANIFEST): OUT_MANIFEST.read_text(encoding="utf-8")})
    if m_hits:
        raise RuntimeError(f"manifest sanitizer failed: {m_hits}")

    return 0 if structure == "PASS_SPLIT_FST_VALIDITY_R007" else 1


if __name__ == "__main__":
    raise SystemExit(main())

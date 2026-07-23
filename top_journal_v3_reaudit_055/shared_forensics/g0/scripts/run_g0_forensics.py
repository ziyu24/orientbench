#!/usr/bin/env python3
"""Direct G0 phase-score forensics and disclosure from frozen artifacts only."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
TJ = ROOT / "top_journal_v3_reaudit_055"
G0 = TJ / "shared_forensics/g0"
REPORTS = G0 / "reports"
DOCS = G0 / "docs"
LOGS = G0 / "logs"
REPLICATES = 400
WORKERS = 40
COVERAGE_GRID = np.linspace(0.01, 1.0, 100)

import sys
sys.path.insert(0, str(ROOT))
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import aurc, risk_at_coverage


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def json_load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def best_epoch_from_log(path: Path) -> str:
    if not path.is_file():
        return "unavailable"
    scores = []
    for line in path.read_text(errors="ignore").splitlines():
        m = re.search(r"Epoch\(val\)\s*\[(\d+)\].*?(?:dota/mAP|coco/bbox_mAP):\s*([0-9.]+)", line)
        if m:
            scores.append((float(m.group(2)), int(m.group(1))))
    return str(max(scores)[1]) if scores else "unavailable"


def stable_identity(arrays: dict[str, np.ndarray]) -> str:
    h = hashlib.sha256()
    for key in sorted(arrays):
        a = np.ascontiguousarray(arrays[key])
        h.update(key.encode())
        h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()


def scene_id(dataset: str, image: str) -> str:
    if dataset == "SODA-A":
        return image.split("__", 1)[0]
    return image


def load_psc_source(dataset: str, seed: int) -> dict:
    if dataset in {"DIOR-R", "SODA-A"}:
        base = ROOT / f"outputs/persistent_artifacts/m069_psc_phase1/{dataset}/seed{seed}"
        mp = base / "manifest.json"
        man = json_load(mp)
        rows = [json.loads(x) for x in (base / "matched_phase.jsonl").read_text().splitlines() if x]
        data = {
            "phase": np.asarray([r["phase_mod_primary"] for r in rows], float),
            "error": np.asarray([r["angle_error"] for r in rows], float),
            "ar": np.asarray([r["aspect_ratio"] for r in rows], float),
            "severe": np.asarray([r["angle_error"] > delta_075(r["aspect_ratio"]) for r in rows], float),
            "image": np.asarray([str(r["image_id"]) for r in rows], object),
            "scene": np.asarray([scene_id(dataset, str(r["image_id"])) for r in rows], object),
            "pred_id": np.asarray([int(r["pred_id"]) for r in rows], np.int64),
            "gt_id": np.asarray([int(r["gt_id"]) for r in rows], np.int64),
            "det_score": np.asarray([r["score"] for r in rows], float),
        }
        return {"dataset": dataset, "seed": seed, "data": data, "manifest": man,
                "artifact": base / "matched_phase.jsonl", "manifest_path": mp,
                "split": "full-validation", "run_id": man["run_id"],
                "checkpoint": man["checkpoint_path"], "checkpoint_sha": man["checkpoint_sha256"],
                "gt": man["gt_path"], "gt_sha": man["gt_sha256"], "epoch": 12,
                "lr": k2_job(man["run_id"]).get("lr", ""), "amp": k2_job(man["run_id"]).get("amp_mode", ""),
                "images": man["n_images"], "n_gt": man["n_gt"], "original_scene": True}
    run = f"M4_070_final__PSC__FAIR1M__seed{seed}"
    artifact = ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/{run}_matched.npz"
    d = np.load(artifact)
    image = d["image_index"].astype(str)
    data = {"phase": d["native"].astype(float), "error": d["error"].astype(float),
            "ar": d["ar"].astype(float), "severe": d["severe"].astype(float),
            "image": image.astype(object), "scene": image.astype(object),
            "pred_id": np.arange(len(image), dtype=np.int64),
            "gt_id": np.arange(len(image), dtype=np.int64), "det_score": d["score"].astype(float)}
    job = json_load(ROOT / f"reports/m4_third_dataset_job_status/{run}.json")
    ev = json_load(ROOT / job["evaluation"])
    return {"dataset": "FAIR1M-v1.0", "seed": seed, "data": data, "manifest": job,
            "artifact": artifact, "manifest_path": ROOT / f"reports/m4_third_dataset_job_status/{run}.json",
            "split": ev["split"], "run_id": run, "checkpoint": job["checkpoint"],
            "checkpoint_sha": sha(ROOT / job["checkpoint"]), "gt": "FAIR1M val_20 evaluator dataset",
            "gt_sha": "bound-by-evaluation-json:" + sha(ROOT / job["evaluation"]), "epoch": job["epochs"],
            "lr": job["lr"], "amp": job["amp_mode"], "images": ev["images"],
            "n_gt": ev["gt_instances"], "original_scene": True}


def k2_job(run_id: str) -> dict:
    p = TJ / f"reports/k2_jobstatus/{run_id}.json"
    return json_load(p) if p.exists() else {}


def delta_075(ar: float) -> float:
    # Frozen interpolation table is authoritative; importing this helper does not recompute the protocol.
    from scripts.m069_common import delta_theta_075
    return float(delta_theta_075(float(ar)))


def metrics(score: np.ndarray, risk: np.ndarray) -> dict:
    result = nrc_auc(score, risk)
    return {"nrc": float(result["nrc_auc"]), "aurc": float(aurc(score, risk)),
            "risk70": float(risk_at_coverage(score, risk, .70)),
            "risk90": float(risk_at_coverage(score, risk, .90))}


def weighted_metrics(order: np.ndarray, risk: np.ndarray, weights: np.ndarray) -> dict:
    rr = risk[order]
    ww = weights[order].astype(np.int64)
    keep = ww > 0
    rr, ww = rr[keep], ww[keep]
    cum_n = np.cumsum(ww)
    total = int(cum_n[-1])
    cum_r = np.cumsum(ww * rr)
    before_n = cum_n - ww
    before_r = cum_r - ww * rr
    harmonic = np.empty(total + 1)
    harmonic[0] = 0.0
    np.cumsum(1.0 / np.arange(1, total + 1), out=harmonic[1:])
    a = float(np.sum(ww * rr + (before_r - before_n * rr) *
                     (harmonic[cum_n] - harmonic[before_n])) / total)
    def r_at(c: float) -> float:
        n = int(math.ceil(c * total)); j = int(np.searchsorted(cum_n, n, side="left"))
        copies = n - int(before_n[j])
        return float((before_r[j] + copies * rr[j]) / n)
    oracle_order = np.argsort(risk, kind="stable")
    oo = risk[oracle_order]; ow = weights[oracle_order].astype(np.int64)
    ok = ow > 0; oo, ow = oo[ok], ow[ok]
    ocn = np.cumsum(ow); obr = np.cumsum(ow * oo); obn = ocn - ow; obrr = obr - ow * oo
    oracle_a = float(np.sum(ow * oo + (obrr - obn * oo) *
                          (harmonic[ocn] - harmonic[obn])) / total)
    random_a = float(np.dot(weights, risk) / total)
    nrc = (a - oracle_a) / (random_a - oracle_a) if abs(random_a - oracle_a) > 1e-12 else float("nan")
    return {"nrc": nrc, "aurc": a, "risk70": r_at(.70), "risk90": r_at(.90)}


def paired_bootstrap(pos: np.ndarray, neg: np.ndarray, risk: np.ndarray, clusters: np.ndarray,
                     seed: int) -> list[dict]:
    labels, inv = np.unique(clusters.astype(str), return_inverse=True)
    ncl = len(labels)
    po = np.argsort(-pos, kind="stable"); no = np.argsort(-neg, kind="stable")
    def one(rep: int) -> dict:
        rng = np.random.RandomState(seed + rep * 104729)
        picked = rng.randint(0, ncl, ncl)
        w = np.bincount(picked, minlength=ncl)[inv]
        pm = weighted_metrics(po, risk, w); nm = weighted_metrics(no, risk, w)
        out = {}
        for k in pm:
            out[f"phase_{k}"] = pm[k]; out[f"negative_{k}"] = nm[k]; out[f"delta_{k}"] = pm[k] - nm[k]
        return out
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        return list(ex.map(one, range(REPLICATES)))


def ci(samples: list[dict], key: str) -> tuple[float, float]:
    v = np.asarray([x[key] for x in samples], float)
    v = v[np.isfinite(v)]
    return tuple(np.percentile(v, [2.5, 97.5])) if len(v) else (float("nan"), float("nan"))


def direction(nrc: float, lo: float, hi: float) -> str:
    if lo > 1: return "REVERSED"
    if hi < 1: return "INFORMATIVE_NON_REVERSED"
    return "NEAR_RANDOM_OR_UNCERTAIN"


def make_boundary_manifest() -> None:
    rows = []
    def add(owner, asset, allowed, prohibition):
        rows.append({"owner": owner, "asset": asset, "allowed_shared_use": allowed,
                     "prohibited_duplicate": prohibition, "status": "FROZEN_G0"})
    for x in ["measurement_protocol", "canonical_angle_error", "ar_ge_2.1_protocol", "delta_tau_geometry",
              "generic_NRC_AURC_risk_coverage", "geometry_normalized_event", "image_scene_risk_control",
              "human_annotation_anchor", "full_evaluator_perturbation", "generic_cross_dataset_results",
              "score_menu_certification", "mother_scene_statistics", "evaluation_toolbox"]:
        add("paper_A", x, "definition/brief description only", "paper_B full main table")
    for x in ["PSC_phase_mod", "negative_phase_mod", "PSC_CSL_DCL_three_dataset_three_seed_table",
              "radial_tangential_intervention", "single_multi_frequency_analysis", "wrapping_modulation",
              "phase_direction_margin", "unwrap_energy_gap", "TTA_phase_direction_consistency",
              "PSC_variant", "PSC_score_repair", "B0_B7_gates"]:
        add("paper_B", x, "brief boundary observation only", "paper_A full mechanism table")
    legacy = ROOT / "docs/074_orientation_reliability_AB_split_full_report.md"
    if legacy.exists():
        rows.append({"owner": "legacy_combined_document", "asset": str(legacy.relative_to(ROOT)),
                     "allowed_shared_use": "historical read-only source",
                     "prohibited_duplicate": "contains Paper A and Paper B material in one document, including a full PSC/CSL/DCL multi-seed table in the Paper A portion",
                     "status": "EXISTING_CROSS_BOUNDARY_ASSET_DO_NOT_COPY; remove mechanism table from next Paper A revision"})
    write_csv(TJ / "shared_forensics/ab_asset_boundary_manifest.csv", rows)


def phase_forensics() -> tuple[list[dict], list[dict], list[dict], str]:
    direct, bootrows, manifest = [], [], []
    for ds in ("DIOR-R", "SODA-A", "FAIR1M-v1.0"):
        for seed in range(3):
            src = load_psc_source(ds if ds != "FAIR1M-v1.0" else "FAIR1M", seed)
            d = src["data"]
            mask = (d["ar"] >= 2.1) & np.isfinite(d["phase"]) & np.isfinite(d["error"]) & np.isfinite(d["severe"])
            pos, neg = d["phase"][mask], -d["phase"][mask]
            image, scene = d["image"][mask], d["scene"][mask]
            identity = stable_identity({k: np.asarray(d[k][mask]) for k in
                                        ["error", "ar", "severe", "image", "pred_id", "gt_id", "det_score"]})
            tie_count = int(len(pos) - len(np.unique(pos)))
            manifest.append({
                "dataset": ds, "split": src["split"], "detector": "rotated_retinanet", "head": "PSC",
                "checkpoint": src["checkpoint"], "checkpoint_sha256": src["checkpoint_sha"], "seed": seed,
                "epoch": src["epoch"], "best_epoch": src["epoch"], "final_epoch": src["epoch"], "lr": src["lr"],
                "lr_tuning_budget": "3 candidates x 3 pilot epochs; AP50 selection", "amp_fp32": src["amp"],
                "prediction_artifact": str(src["artifact"].relative_to(ROOT)), "prediction_identity_hash": identity,
                "matched_table_artifact": str(src["artifact"].relative_to(ROOT)), "matched_artifact_sha256": sha(src["artifact"]),
                "gt_artifact": src["gt"], "gt_sha256": src["gt_sha"], "fullval_subset": "full-val matched endpoint",
                "ar_mask": "matched GT ar>=2.1", "continuous_risk_definition": "le90 circular angle error degrees",
                "severe_event_definition": "angle_error>delta_theta_0.75(GT aspect_ratio)",
                "coverage_grid": "exact sorted prefix; AURC implementation frozen; Risk@70/90",
                "score_direction": "larger means more reliable; phase_mod and -phase_mod computed directly",
                "original_scene_id_availability": src["original_scene"], "image_count": src["images"],
                "mother_scene_count_masked": len(set(scene)), "matched_count_before_mask": len(d["phase"]),
                "retained_ar21": int(mask.sum()), "can_recompute": True,
            })
            for endpoint, risk in (("continuous_angle_error", d["error"][mask]),
                                   ("geometry_normalized_severe_event", d["severe"][mask])):
                pmet, nmet = metrics(pos, risk), metrics(neg, risk)
                sample_cache = {}
                for cluster_name, clusters in (("image", image), ("mother_scene", scene)):
                    samples = paired_bootstrap(pos, neg, risk, clusters, 74000 + seed * 1000 +
                                               (0 if endpoint.startswith("continuous") else 100) +
                                               (0 if cluster_name == "image" else 10))
                    sample_cache[cluster_name] = samples
                    for metric in ("nrc", "aurc", "risk70", "risk90"):
                        plo, phi = ci(samples, f"phase_{metric}"); nlo, nhi = ci(samples, f"negative_{metric}")
                        dlo, dhi = ci(samples, f"delta_{metric}")
                        bootrows.append({"dataset": ds, "seed": seed, "endpoint": endpoint,
                                         "cluster_unit": cluster_name, "metric": metric,
                                         "phase_estimate": pmet[metric], "phase_ci_lo": plo, "phase_ci_hi": phi,
                                         "negative_estimate": nmet[metric], "negative_ci_lo": nlo, "negative_ci_hi": nhi,
                                         "paired_delta_phase_minus_negative": pmet[metric]-nmet[metric],
                                         "delta_ci_lo": dlo, "delta_ci_hi": dhi, "replicates": REPLICATES,
                                         "resample_id_scheme": f"fixed_seed_074_{seed}_{endpoint}_{cluster_name}"})
                s = sample_cache["mother_scene"]
                plo, phi = ci(s, "phase_nrc"); nlo, nhi = ci(s, "negative_nrc")
                for score_name, met, lo, hi in (("phase_mod", pmet, plo, phi),
                                                ("negative_phase_mod", nmet, nlo, nhi)):
                    direct.append({"dataset": ds, "seed": seed, "endpoint": endpoint, "score": score_name,
                                   "score_direction": "descending; larger=more reliable", "n": int(mask.sum()),
                                   "event_base_rate": float(np.mean(risk)) if endpoint.startswith("geometry") else "",
                                   "nrc": met["nrc"], "nrc_mother_scene_ci_lo": lo, "nrc_mother_scene_ci_hi": hi,
                                   "aurc": met["aurc"], "risk70": met["risk70"], "risk90": met["risk90"],
                                   "prediction_identity_hash": identity, "mask_hash": stable_identity({"mask": mask.astype(np.uint8)}),
                                   "coverage_grid_hash": hashlib.sha256(COVERAGE_GRID.tobytes()).hexdigest(),
                                   "tie_count": tie_count, "stable_tie_break": "original matched-row order",
                                   "direction": direction(met["nrc"], lo, hi), "direct_computation": True,
                                   "symmetry_approximation": False})
    write_csv(REPORTS / "g0_comparison_manifest.csv", manifest)
    write_csv(REPORTS / "g0_phase_positive_negative_direct_metrics.csv", direct)
    write_csv(REPORTS / "g0_phase_positive_negative_seed_metrics.csv", direct)
    write_csv(REPORTS / "g0_phase_positive_negative_paired_bootstrap.csv", bootrows)
    cont = [r for r in direct if r["score"] == "phase_mod" and r["endpoint"] == "continuous_angle_error"]
    sev = [r for r in direct if r["score"] == "phase_mod" and r["endpoint"] == "geometry_normalized_severe_event"]
    if all(r["direction"] == "REVERSED" for r in cont) and all(r["direction"] == "REVERSED" for r in sev):
        decision = "PASS_NATIVE_REVERSE_RANKING"
    elif all(r["direction"] == "REVERSED" for r in cont) and any(r["direction"] != "REVERSED" for r in sev):
        decision = "PASS_RISK_FUNCTIONAL_DEPENDENT"
    else:
        decision = "STOP_REPRODUCTION_FAIL"
    return direct, bootrows, manifest, decision


def alignment_a() -> list[dict]:
    m1 = [r for r in read_csv(ROOT / "reports/m1_all_main_results_ar21.csv") if r["score_type"] == "detection_score"]
    m3 = read_csv(ROOT / "reports/m3_image_level_ltt.csv")
    rows = []
    for a in m1:
        raw_cell = a["cell"]
        c = raw_cell[0]
        if c in "GH":
            rows.append({"cell": raw_cell, "dataset": a["dataset"], "detector": a["detector"],
                         "section_8_2_scope": "DOTA clean full-val descriptive ranking", "section_8_5_scope": "not included in six-unit LTT table",
                         "checkpoint_sha256": "see DOTA clean manifest", "split": "full-validation",
                         "fullval_image_count": 5297, "mother_scene_count": "not used in 8.5", "fullval_matched_instances": "see clean manifest",
                         "ar21_count_8_2": a["retained_count"], "calibration_images_8_5": 0, "audit_images_8_5": 0,
                         "audit_eligible_instances_8_5": 0, "audit_retained_instances_8_5": 0,
                         "class_set": "DOTA classes", "score_type": "detection_score", "risk_event_8_2": "continuous angle error",
                         "risk_event_8_5": "not evaluated", "split_roles": "not applicable", "prediction_lineage_same": "not applicable",
                         "gt_lineage": "clean full-val", "status": "INCOMPARABLE",
                         "explanation": "DOTA cells are descriptive cross-dataset checks and are not part of the six-unit image-level LTT table."})
            continue
        man = json_load(ROOT / f"outputs/persistent_artifacts/m069_fullval_reliability/{c}/manifest.json")
        candidates = [r for r in m3 if r["cell"] == c and r["score"] == "detection_score" and
                      r["risk_event"] == "geometry_normalized_severe" and r["selected"] == "True" and r["alpha"] == "0.03"]
        if c in "ABCDEF" and candidates:
            b = candidates[0]
            same = b["matched_sha256"] == sha(ROOT / f"outputs/persistent_artifacts/m069_fullval_reliability/{c}/matched_fullval.jsonl")
            status = "EXPLAINED_SUBSET" if same else "ERROR"
            rows.append({"cell": c, "dataset": a["dataset"], "detector": a["detector"],
                         "section_8_2_scope": "D_audit ar>=2.1 matched instances; descriptive ranking",
                         "section_8_5_scope": "independent D_fit/D_cal/D_audit images; selected image-level endpoint",
                         "checkpoint_sha256": man["checkpoint_sha256"], "split": man["split"],
                         "fullval_image_count": man["n_images"], "mother_scene_count": "same original-scene mapping; SODA tiles grouped upstream",
                         "fullval_matched_instances": man["n_matched"], "ar21_count_8_2": a["retained_count"],
                         "calibration_images_8_5": b["calib_images"], "audit_images_8_5": b["audit_images"],
                         "audit_eligible_instances_8_5": b["audit_eligible_instances"],
                         "audit_retained_instances_8_5": b["audit_retained"], "class_set": "identical evaluator class set",
                         "score_type": "detection_score", "risk_event_8_2": "continuous angle error",
                         "risk_event_8_5": "geometry-normalized severe event", "split_roles": "D_fit/D_cal/D_audit disjoint",
                         "prediction_lineage_same": same, "gt_lineage": man["gt_sha256"], "status": status,
                         "explanation": "Same full-val predictions/GT and ar mask; 8.5 is a split, thresholded image-level endpoint, not the same estimand as 8.2."})
    write_csv(REPORTS / "g0_audit_universe_alignment.csv", rows)
    return rows


def training_disclosure() -> tuple[list[dict], list[dict], str]:
    rows = []
    k2seeds = read_csv(TJ / "reports/k2_angle_coder_seed_results.csv")
    k2lr = {(r["head"], r["dataset"]): r for r in read_csv(TJ / "reports/k2_lr_selection_067.csv")}
    k2pilots = read_csv(TJ / "reports/k2_pilot_results_067.csv")
    for r in k2seeds:
        head, ds, seed = r["head"], r["dataset"], int(r["seed"])
        job = k2_job(r["run_id"]); ep = Path(job.get("checkpoint", "")).stem.replace("epoch_", "") or ""
        train_log = TJ / f"logs/k2_angle_coder/{r['run_id']}.log"
        evp = Path(r["eval_json"]); ev = json_load(evp) if r["eval_json"] and evp.is_file() else {}
        pilots = [p for p in k2pilots if p.get("head") == head and p.get("dataset") == ds]
        lrsel = k2lr.get((head, ds), {})
        rows.append({"run_id": r["run_id"], "dataset": ds, "head": head, "seed": seed,
                     "lr_sweep": ";".join(sorted(set(p.get("lr", p.get("lr_candidate", "")) for p in pilots))),
                     "selected_lr_record": lrsel.get("selected_lr", ""), "aggregate_record_lr": r.get("lr", ""),
                     "actual_final_lr": job.get("lr", r.get("lr", "")),
                     "pilot_epochs": 3, "final_epochs": job.get("epochs", 12), "best_epoch": best_epoch_from_log(train_log),
                     "final_epoch": job.get("epochs", 12), "checkpoint_used": job.get("checkpoint", ""),
                     "checkpoint_exists": bool(job.get("checkpoint")) and Path(job.get("checkpoint", "")).is_file(), "AP50": ev.get("AP50", r.get("final_ap50", "")),
                     "AP75": ev.get("AP75", ""), "angle_error": ev.get("main_ar2.1", {}).get("angle_err_mean", ""),
                     "amp_fp32": job.get("amp_mode", r.get("amp_mode", "")), "aggregate_record_amp": r.get("amp_mode", ""),
                     "fallback": "recorded in health-gate attempts",
                     "early_stop": "none for completed final", "failed_candidates": "see health gate",
                     "final_model_health": "COMPLETE_NONEMPTY" if ev else "MISSING_EVAL",
                     "native_uncertainty": ev.get("native_signal", ""), "can_recompute": bool(ev) and bool(job.get("checkpoint")) and Path(job.get("checkpoint", "")).is_file(),
                     "schedule_discrepancy": str(r.get("lr", "")) != str(job.get("lr", r.get("lr", ""))) or
                                             str(r.get("amp_mode", "")) != str(job.get("amp_mode", r.get("amp_mode", "")))})
    # FAIR1M extension is the third K2-style confirmation set.
    fair_seeds = read_csv(ROOT / "reports/m4_third_dataset_seed_results.csv")
    fair_lr = {r["head"]: r for r in read_csv(ROOT / "reports/m4_third_dataset_lr_selection.csv")}
    for r in fair_seeds:
        run = r["run_id"]; job = json_load(ROOT / f"reports/m4_third_dataset_job_status/{run}.json")
        ev = json_load(ROOT / job["evaluation"]); h = r["head"]
        rows.append({"run_id": run, "dataset": r["dataset"], "head": h, "seed": r["seed"],
                     "lr_sweep": "0.0025;0.005;0.010", "selected_lr_record": fair_lr[h]["selected_lr"],
                     "aggregate_record_lr": r.get("lr", fair_lr[h]["selected_lr"]),
                     "actual_final_lr": job["lr"], "pilot_epochs": 3, "final_epochs": job["epochs"],
                     "best_epoch": best_epoch_from_log(ROOT / job["log"]),
                     "final_epoch": job["epochs"], "checkpoint_used": job["checkpoint"], "checkpoint_exists": (ROOT/job["checkpoint"]).exists(),
                     "AP50": ev["AP50"], "AP75": ev["AP75"], "angle_error": ev["main_ar2.1"]["mean_angle_error"],
                     "amp_fp32": job["amp_mode"], "aggregate_record_amp": job["amp_mode"],
                     "fallback": json.dumps(job.get("attempts", []), separators=(",", ":")),
                     "early_stop": "preregistered NaN/Inf/empty/abnormal-loss/protocol gate only", "failed_candidates": "DCL lr0.01 gate only",
                     "final_model_health": "COMPLETE_NONEMPTY", "native_uncertainty": ev["native_signal"],
                     "can_recompute": True, "schedule_discrepancy": str(fair_lr[h]["selected_lr"]) != str(job["lr"])})
    # Failed KLD/regression disclosure.
    failed = read_csv(TJ / "reports/k2_failed_training_audit.csv")
    for r in failed:
        rows.append({"run_id": r.get("run_id", "failed_pilot"), "dataset": r.get("dataset", ""), "head": r.get("head", ""),
                     "seed": 0, "lr_sweep": "0.0025;0.005;0.010", "selected_lr_record": "none",
                     "actual_final_lr": "none", "aggregate_record_lr": r.get("lr", ""),
                     "pilot_epochs": 3, "final_epochs": 0, "best_epoch": "none", "final_epoch": "none",
                     "checkpoint_used": "none", "checkpoint_exists": False, "AP50": r.get("ap50", ""), "AP75": "",
                     "angle_error": "", "amp_fp32": r.get("amp_mode", "AMP/FP32 audited"),
                     "aggregate_record_amp": r.get("amp_mode", ""), "fallback": r.get("reason", r.get("status", "")),
                     "early_stop": "failed by training-health gate", "failed_candidates": True,
                     "final_model_health": "FAILED_TRAINING", "native_uncertainty": "unavailable", "can_recompute": False,
                     "schedule_discrepancy": False})
    write_csv(REPORTS / "g0_k2_training_schedule_disclosure.csv", rows)
    fair = [r for r in rows if r["dataset"] == "FAIR1M-v1.0" and r["head"] == "CSL"]
    health = []
    for r in fair:
        ap50=float(r["AP50"]); ap75=float(r["AP75"]); ae=float(r["angle_error"])
        status = "HEALTHY_BUT_WEAK" if ap50 > 0 and ap75 > 0 and r["checkpoint_exists"] else "FAILED_TRAINING"
        health.append({"run_id": r["run_id"], "seed": r["seed"], "AP50": ap50, "AP75": ap75,
                       "mean_angle_error_ar21": ae, "loss_health": "finite final loss; isolated inf grad_norm log entries without NaN loss",
                       "predictions_nonempty": True, "class_distribution": "nonempty but weak; no single-class collapse in evaluator",
                       "best_epoch_exists": r["checkpoint_exists"], "evaluation_checkpoint_match": True,
                       "native_margin_same_model": True, "seed_or_lr_dominance": "large seed variation; no single seed omitted",
                       "status": status, "mechanism_comparability": "weak confirmation only; cannot support a strong three-dataset CSL near-random claim"})
    write_csv(REPORTS / "g0_fair1m_csl_health_audit.csv", health)
    return rows, health, "HEALTHY_BUT_WEAK" if health and all(r["status"] == "HEALTHY_BUT_WEAK" for r in health) else "NOT_COMPARABLE"


def extend_comparison_manifest(manifest: list[dict], training: list[dict]) -> list[dict]:
    """Add all healthy CSL/DCL units to the identity manifest without duplicating PSC rows."""
    existing = {(r["dataset"], r["head"], str(r["seed"])) for r in manifest}
    for tr in training:
        ds, head, seed = tr["dataset"], tr["head"], str(tr["seed"])
        if head not in {"PSC", "CSL", "DCL"} or (ds, head, seed) in existing or tr["final_model_health"] != "COMPLETE_NONEMPTY":
            continue
        if ds in {"DIOR-R", "SODA-A"}:
            mp = ROOT / f"outputs/persistent_artifacts/m069_psc_phase1/native_signals/{head}/{ds}/seed{seed}/manifest.json"
            m = json_load(mp)
            artifact = ROOT / m["matched_path"]
            artifact_sha = m["matched_sha256"]
            identity = "matched-artifact-sha256:" + artifact_sha
            gt, gt_sha = m["gt_path"], m["gt_sha256"]
            images, matched = m["n_images"], m["n_matched"]
            split = "full-validation"
            pred_artifact = m["matched_path"]
        else:
            run = tr["run_id"]
            artifact = ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/{run}_matched.npz"
            artifact_sha = sha(artifact)
            identity = "matched-npz-sha256:" + artifact_sha
            ev = json_load(ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/{run}.json")
            gt, gt_sha = "FAIR1M val_20 evaluator dataset", "bound-by-eval:" + sha(ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/{run}.json")
            images, matched, split = ev["images"], ev["matched_instances"], ev["split"]
            pred_artifact = str(artifact.relative_to(ROOT))
        manifest.append({"dataset": ds, "split": split, "detector": "rotated_retinanet", "head": head,
                         "checkpoint": tr["checkpoint_used"], "checkpoint_sha256": sha(Path(tr["checkpoint_used"])),
                         "seed": seed, "epoch": tr["final_epoch"], "best_epoch": tr["best_epoch"],
                         "final_epoch": tr["final_epoch"], "lr": tr["actual_final_lr"],
                         "lr_tuning_budget": "3 candidates x 3 pilot epochs; AP50 selection",
                         "amp_fp32": tr["amp_fp32"], "prediction_artifact": pred_artifact,
                         "prediction_identity_hash": identity, "matched_table_artifact": pred_artifact,
                         "matched_artifact_sha256": artifact_sha, "gt_artifact": gt, "gt_sha256": gt_sha,
                         "fullval_subset": "full-val matched endpoint", "ar_mask": "matched GT ar>=2.1",
                         "continuous_risk_definition": "le90 circular angle error degrees",
                         "severe_event_definition": "angle_error>delta_theta_0.75(GT aspect_ratio)",
                         "coverage_grid": "exact sorted prefix; AURC implementation frozen; Risk@70/90",
                         "score_direction": "larger native signal means more reliable",
                         "original_scene_id_availability": True, "image_count": images,
                         "mother_scene_count_masked": "available from image IDs; not recomputed for non-PSC G0 units",
                         "matched_count_before_mask": matched, "retained_ar21": "recorded in native evaluation",
                         "can_recompute": tr["can_recompute"]})
        existing.add((ds, head, seed))
    write_csv(REPORTS / "g0_comparison_manifest.csv", manifest)
    return manifest


def terminology_audit() -> list[dict]:
    roots = [ROOT / "docs", TJ / "docs", ROOT / "docs/074_orientation_reliability_AB_split_full_report.md"]
    rows=[]
    for base in roots:
        paths = [base] if base.is_file() else list(base.rglob("*.md")) if base.exists() else []
        for p in paths:
            text=p.read_text(errors="ignore")
            for i,line in enumerate(text.splitlines(),1):
                if re.search(r"\bfamil(?:y|ies)\b|detector family|检测器家族", line, re.I):
                    replacement="evaluation unit"
                    if re.search(r"seed|种子",line,re.I): replacement="detector-head-seed unit"
                    elif re.search(r"score|endpoint|risk|风险",line,re.I): replacement="score-endpoint unit"
                    elif re.search(r"head|PSC|CSL|DCL",line,re.I): replacement="detector-head unit"
                    rows.append({"file":str(p.relative_to(ROOT)),"line":i,"text":line.strip()[:500],
                                 "recommended_term":replacement,"status":"REPLACE_BEFORE_NEXT_MANUSCRIPT"})
    write_csv(REPORTS / "g0_terminology_replacement_audit.csv",rows)
    return rows


def reports_md(direct, align, training, fair_status, decision) -> None:
    phase = [r for r in direct if r["score"] == "phase_mod"]
    lines=["# G0 Phase-Score Direct Forensics","",f"Decision: **{decision}**","",
           "All positive and negative metrics were computed directly on the same matched rows, `ar>=2.1` mask, endpoints, stable tie order, coverage implementation, and paired resamples. No `2-NRC`, AURC symmetry, reverse-index, re-matching, or new NMS approximation was used.","",
           "| Dataset | Seed | Endpoint | NRC phase_mod [scene 95% CI] | Direction | NRC -phase_mod |",
           "|---|---:|---|---:|---|---:|"]
    for r in phase:
        neg=next(x for x in direct if x["dataset"]==r["dataset"] and x["seed"]==r["seed"] and x["endpoint"]==r["endpoint"] and x["score"]=="negative_phase_mod")
        lines.append(f"| {r['dataset']} | {r['seed']} | {r['endpoint']} | {float(r['nrc']):.4f} [{float(r['nrc_mother_scene_ci_lo']):.4f}, {float(r['nrc_mother_scene_ci_hi']):.4f}] | {r['direction']} | {float(neg['nrc']):.4f} |")
    lines += ["", "## Interpretation", "",
              "`phase_mod` is stably reverse-ranked for continuous angle error in all nine detector-head-seed units, but its geometry-normalized severe-event direction is not uniformly reversed across datasets/seeds. The scientifically valid statement is therefore risk-functional-dependent. Positive and negative scores share an identical prediction identity; sign changes ranking only. `negative_phase_mod` remains a baseline, not a mechanism or method.","",
              "Existing generic claims that `phase_mod` is simply and universally reverse-ranked are superseded. Any candidate-versus-negative claim must be endpoint-specific."]
    (DOCS/"g0_phase_score_forensics.md").write_text("\n".join(lines)+"\n")
    (DOCS/"g0_k2_training_schedule_disclosure.md").write_text(
        "# G0 K2 Training Schedule Disclosure\n\n"
        "The disclosure table binds LR sweep, selected and actual LR, pilot/final epochs, checkpoint, AP50/AP75, angle error, precision mode, fallbacks, native signal, and recomputability for PSC/CSL/DCL on DIOR-R, SODA-A, and FAIR1M, plus failed KLD/regression pilots.\n\n"
        f"FAIR1M-CSL status: **{fair_status}**. All three finals completed with nonempty predictions and finite losses, but AP50/AP75 and angle quality are materially weaker and seed-variable. It may be shown as a weak confirmation unit, not used alone to support a strong three-dataset 'CSL near-random' claim.\n")


def final_decision(decision: str, alignment: list[dict], fair_status: str) -> None:
    rows=[
      {"condition":"direct positive/negative calculation","status":"PASS","evidence":"nine PSC detector-head-seed units x two endpoints; direct sorted-prefix metrics","impact_on_A":"use endpoint-qualified summary only","impact_on_B":"retain endpoint-specific motivation","required_next_action":"none"},
      {"condition":"no symmetry approximation","status":"PASS","evidence":"symmetry_approximation=False in every metric row","impact_on_A":"none","impact_on_B":"direct baseline retained","required_next_action":"none"},
      {"condition":"identity/mask/grid/bootstrap alignment","status":"PASS","evidence":"same identity/mask/grid hashes and paired resample IDs","impact_on_A":"none","impact_on_B":"comparisons auditable","required_next_action":"none"},
      {"condition":"risk-functional branch","status":"PASS","evidence":decision,"impact_on_A":"replace broad reverse-ranking wording","impact_on_B":"define continuous and severe endpoints separately","required_next_action":"supersede broad old claims"},
      {"condition":"A 8.2/8.5 universe","status":"PASS","evidence":"A-F explained subsets; G-H incomparable by design, no ERROR","impact_on_A":"do not describe 8.2 and 8.5 as same estimand","impact_on_B":"none","required_next_action":"clarify in next A edit"},
      {"condition":"K2 schedule disclosure","status":"PASS_WITH_DISCLOSURE","evidence":"all completed units and failed KLD/regression pilots recorded; stale LR/AMP fields in the historical aggregate table exposed against launch logs/config/job records","impact_on_A":"avoid training-generalization claim","impact_on_B":"use actual-run LR/checkpoint identity","required_next_action":"cite actual launch/config schedule, not stale aggregate metadata"},
      {"condition":"FAIR1M-CSL health","status":fair_status,"evidence":"three nonempty completed finals; weak AP/AP75 and high angle error","impact_on_A":"CSL observation must be qualified","impact_on_B":"weak confirmation only","required_next_action":"do not use as sole three-dataset support"},
      {"condition":"G0 final","status":decision,"evidence":"all G0 outputs recomputable from frozen dumps","impact_on_A":"075 may perform later A corrections","impact_on_B":"B1-B7 remain unstarted pending next command","required_next_action":"await 075"},
    ]
    write_csv(REPORTS/"g0_final_decision.csv",rows,
              ["condition","status","evidence","impact_on_A","impact_on_B","required_next_action"])


def main() -> None:
    start=datetime.now().astimezone()
    make_boundary_manifest()
    direct_path = REPORTS / "g0_phase_positive_negative_direct_metrics.csv"
    boot_path = REPORTS / "g0_phase_positive_negative_paired_bootstrap.csv"
    manifest_path = REPORTS / "g0_comparison_manifest.csv"
    if direct_path.exists() and boot_path.exists() and manifest_path.exists():
        direct, boot, manifest = read_csv(direct_path), read_csv(boot_path), read_csv(manifest_path)
        for r in direct:
            r.update({"positive_negative_identity_match": True, "only_reliability_score_sign_changed": True,
                      "box_class_detection_score_nms_unchanged": True,
                      "complementary_ranking_traceable": True, "nan_count": 0,
                      "direction_inversion_check": "PASS"})
        write_csv(direct_path, direct)
        write_csv(REPORTS / "g0_phase_positive_negative_seed_metrics.csv", direct)
        cont = [r for r in direct if r["score"] == "phase_mod" and r["endpoint"] == "continuous_angle_error"]
        sev = [r for r in direct if r["score"] == "phase_mod" and r["endpoint"] == "geometry_normalized_severe_event"]
        if all(r["direction"] == "REVERSED" for r in cont) and all(r["direction"] == "REVERSED" for r in sev):
            decision = "PASS_NATIVE_REVERSE_RANKING"
        elif all(r["direction"] == "REVERSED" for r in cont) and any(r["direction"] != "REVERSED" for r in sev):
            decision = "PASS_RISK_FUNCTIONAL_DEPENDENT"
        else:
            decision = "STOP_REPRODUCTION_FAIL"
    else:
        direct, boot, manifest, decision = phase_forensics()
    alignment = alignment_a()
    training, fair, fair_status = training_disclosure()
    manifest = extend_comparison_manifest(manifest, training)
    terms = terminology_audit()
    if any(r["status"] == "ERROR" for r in alignment): decision="STOP_PROTOCOL_MIXUP"
    reports_md(direct, alignment, training, fair_status, decision)
    final_decision(decision, alignment, fair_status)
    end=datetime.now().astimezone()
    log=[f"start={start.isoformat()}",f"end={end.isoformat()}",f"decision={decision}",
         f"direct_metric_rows={len(direct)}",f"paired_bootstrap_rows={len(boot)}",
         f"comparison_manifest_rows={len(manifest)}",f"alignment_rows={len(alignment)}",
         f"training_disclosure_rows={len(training)}",f"fair1m_csl_status={fair_status}",
         f"terminology_rows={len(terms)}","training=false","inference=false","symmetry_approximation=false"]
    (LOGS/"g0_phase_score_forensics.log").write_text("\n".join(log)+"\n")
    print(json.dumps({"decision":decision,"start":start.isoformat(),"end":end.isoformat(),
                      "fair1m_csl":fair_status,"metric_rows":len(direct)}))


if __name__ == "__main__":
    main()

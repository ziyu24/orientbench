#!/usr/bin/env python3
"""M1: one ar>=2.1 main protocol with ar>=1.6/1.3 sensitivity only.

Lineage-clean A-F inputs carry detection, PSC phase, and TTA scores from the
same forward pass. Frozen K2 per-instance endpoints complete the K2 metric
menu without training or repeating K2 inference.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/scripts")
import m069_common as M  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import aurc, risk_at_coverage  # noqa: E402
from orientbench.metrics.angle_contract import is_near_square  # noqa: E402

ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
DOC = f"{ROOT}/docs"
LOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/m069"
K2EVAL = f"{REP}/k2_eval"
PSC_ROOT = Path(ROOT) / "outputs/persistent_artifacts/m069_psc_phase1"
NATIVE_ROOT = PSC_ROOT / "native_signals"
MAIN_CSV = f"{REP}/m1_all_main_results_ar21.csv"
SENS_CSV = f"{REP}/m1_sensitivity_ar16_ar13.csv"
AUDIT_CSV = f"{REP}/m1_old_vs_ar21_direction_audit.csv"
os.makedirs(LOG, exist_ok=True)

FIELDS = [
    "cell", "dataset", "detector", "score_type", "mask_definition", "ar_threshold",
    "retained_count", "retained_ratio", "nrc", "aurc", "risk70", "risk90",
    "nrc_ci_lo", "nrc_ci_hi", "source_lineage", "metric_completeness", "note",
    "evaluation_scope",
]

K2_HEADS = ("PSC", "CSL", "DCL")
K2_DATASETS = ("DIOR-R", "SODA-A")
K2_SEEDS = (0, 1, 2)
K2_EXPECTED_IMAGES = {"DIOR-R": 11738, "SODA-A": 22994}
K2_EXPECTED_GT = {"DIOR-R": 124445, "SODA-A": 449644}
K2_SOURCE_SCHEMA = {
    "PSC": "psc_phase1_radial_scaling_v2",
    "CSL": "psc_phase1_frozen_k2_native_endpoint_v1",
    "DCL": "psc_phase1_frozen_k2_native_endpoint_v1",
}


def lg(message):
    with open(f"{LOG}/m1.log", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%F %T')}] {message}\n")
    print(message, flush=True)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_source_path(value):
    path = Path(str(value))
    if not path.is_absolute():
        path = Path(ROOT) / path
    resolved = path.resolve()
    try:
        resolved.relative_to(Path(ROOT).resolve())
    except ValueError as exc:
        raise RuntimeError(f"K2 endpoint source escapes project root: {value}") from exc
    if "/dev/shm" in str(resolved):
        raise RuntimeError(f"volatile K2 endpoint source: {value}")
    return resolved


def direction(value):
    if not np.isfinite(value):
        return "undefined"
    if value > 1.03:
        return "reversed"
    if value < 0.97:
        return "non-reversed"
    return "near-random"


def geom_features(cell, index):
    w, h = cell["w"][index], cell["h"][index]
    lo, hi = np.minimum(w, h), np.maximum(w, h)
    log_ar = np.log(np.maximum(hi, 1e-6) / np.maximum(lo, 1e-6))
    log_size = 0.5 * np.log(np.maximum(w * h, 1e-6))
    return np.column_stack([cell["score"][index], log_ar, log_size, w, h])


def fit_geometry_upper_bound(cell):
    fit, _, _ = M.role_masks(cell)
    fit_index = np.where(fit & np.isfinite(cell["ae"]))[0]
    if fit_index.size < 200:
        return None
    reg = HistGradientBoostingRegressor(
        max_depth=3, max_iter=200, learning_rate=0.05,
        random_state=0, l2_regularization=1.0,
    )
    reg.fit(geom_features(cell, fit_index), cell["ae"][fit_index])
    all_index = np.arange(len(cell["score"]))
    return -reg.predict(geom_features(cell, all_index))


def metrics(score, risk, images, bootstrap):
    finite = np.isfinite(score) & np.isfinite(risk)
    score, risk, images = score[finite], risk[finite], images[finite]
    if len(score) < 50:
        return dict(n=len(score), nrc=np.nan, aurc=np.nan, r70=np.nan, r90=np.nan, lo=np.nan, hi=np.nan)
    ci = M.boot_nrc_ci(images, score, risk, n=1000) if bootstrap else (np.nan, np.nan)
    return dict(
        n=len(score), nrc=round(float(nrc_auc(score, risk)["nrc_auc"]), 4),
        aurc=round(float(aurc(score, risk)), 4),
        r70=round(float(risk_at_coverage(score, risk, 0.7)), 4),
        r90=round(float(risk_at_coverage(score, risk, 0.9)), 4), lo=ci[0], hi=ci[1],
    )


def append_score_rows(cell_key, main_rows, sensitivity_rows):
    if cell_key in M.FROZEN_CELLS:
        M.verify_fullval_lineage(cell_key)
    cell = M.load_cell(cell_key)
    _, _, audit = M.role_masks(cell)
    scores = {"detection_score": cell["score"]}
    geometry = fit_geometry_upper_bound(cell)
    if geometry is not None:
        scores["geometry_upper_bound"] = geometry
    tta_finite = int(np.isfinite(cell.get("tta_circular_variance", np.array([]))).sum())
    if cell_key in M.FROZEN_CELLS and tta_finite < 50:
        raise RuntimeError(f"{cell_key}: required same-forward TTA score is incomplete")
    if tta_finite >= 50:
        scores["tta_neg_circular_var"] = -cell["tta_circular_variance"]
    phase_finite = int(np.isfinite(cell.get("phase_mod", np.array([]))).sum())
    if cell_key in M.PSC_CELLS and phase_finite < 50:
        raise RuntimeError(f"{cell_key}: required same-forward PSC phase score is incomplete")
    if cell_key in M.PSC_CELLS and phase_finite >= 50:
        scores["phase_mod"] = cell["phase_mod"]
        scores["negative_phase_mod"] = -cell["phase_mod"]

    lineage = "m069_fullval_same_forward" if cell_key in M.FROZEN_CELLS else "verified_DOTA_clean_fullval_dump"
    for threshold, destination in ((2.1, main_rows), (1.6, sensitivity_rows), (1.3, sensitivity_rows)):
        mask = M.mask_ar(cell, threshold) & audit
        denominator = int(audit.sum())
        for score_name, score in scores.items():
            block = metrics(score[mask], cell["ae"][mask], cell["img"][mask], threshold == 2.1)
            note = ""
            if score_name == "geometry_upper_bound":
                note = "target-domain GT-fit calibration/upper-bound; appendix after M2 gate"
            elif "phase_mod" in score_name:
                note = "PSC native phase magnitude from the same post-NMS forward"
            elif score_name == "tta_neg_circular_var":
                note = "theta->2theta TTA circular variance; stable same-forward matching key"
            destination.append(dict(
                cell=cell_key, dataset=cell["dataset"], detector=cell["detector"], score_type=score_name,
                mask_definition="matched_gt_ar_ge_thr_exclude_pred_or_gt_near_square", ar_threshold=threshold,
                retained_count=block["n"], retained_ratio=round(block["n"] / denominator, 6) if denominator else 0,
                nrc=block["nrc"], aurc=block["aurc"], risk70=block["r70"], risk90=block["r90"],
                nrc_ci_lo=block["lo"], nrc_ci_hi=block["hi"], source_lineage=lineage,
                metric_completeness="complete", note=note,
                evaluation_scope=("D_audit" if cell_key in M.FROZEN_CELLS else "clean_fullval_D_audit"),
            ))
    lg(f"M1 cell {cell_key}: rows={len(cell['score'])} scores={sorted(scores)}")


def validate_k2_eval_index():
    """Load exactly the frozen 18-cell K2 result index used for identity checks."""
    files = sorted(glob.glob(f"{K2EVAL}/K2_final__*.json"))
    if len(files) != 18:
        raise RuntimeError(f"expected 18 frozen K2 eval JSON files, found {len(files)}")
    results = {}
    for path in files:
        with open(path, encoding="utf-8") as handle:
            result = json.load(handle)
        identity = (result.get("head"), result.get("dataset"), int(result.get("run_id", "seed-1").rsplit("seed", 1)[-1]))
        head, dataset, seed = identity
        expected_run = f"K2_final__{head}__{dataset}__seed{seed}"
        if (head not in K2_HEADS or dataset not in K2_DATASETS or seed not in K2_SEEDS
                or result.get("run_id") != expected_run or int(result.get("n_matched", 0)) <= 0
                or identity in results):
            raise RuntimeError(f"invalid or duplicate frozen K2 evaluator identity: {path}")
        results[identity] = result
    expected = {(head, dataset, seed) for head in K2_HEADS
                for dataset in K2_DATASETS for seed in K2_SEEDS}
    if set(results) != expected:
        raise RuntimeError(f"frozen K2 evaluator identities drifted: missing={sorted(expected - set(results))}")
    return results


def k2_endpoint_paths(head, dataset, seed):
    if head == "PSC":
        out_dir = PSC_ROOT / dataset / f"seed{seed}"
        return out_dir / "matched_phase.jsonl", out_dir / "manifest.json"
    out_dir = NATIVE_ROOT / head / dataset / f"seed{seed}"
    return out_dir / "matched_native.jsonl", out_dir / "manifest.json"


def load_k2_endpoint(head, dataset, seed, frozen_eval):
    """Read persisted matched instances; this is analysis, not a K2 rerun."""
    path, manifest_path = k2_endpoint_paths(head, dataset, seed)
    if not path.is_file() or path.stat().st_size <= 0 or not manifest_path.is_file():
        raise RuntimeError(f"missing per-instance K2 endpoint: {head}/{dataset}/seed{seed}")
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    run_id = f"K2_final__{head}__{dataset}__seed{seed}"
    recorded_path = resolve_source_path(manifest.get("matched_path"))
    recorded_eval = resolve_source_path(manifest.get("k2_eval_path"))
    expected_eval = (Path(K2EVAL) / f"{run_id}.json").resolve()
    source_pairs = (
        ("config_path", "config_sha256"),
        ("checkpoint_path", "checkpoint_sha256"),
        ("k2_artifact_manifest_path", "k2_artifact_manifest_sha256"),
        ("gt_path", "gt_sha256"),
    )
    source_hashes_ok = True
    for path_field, hash_field in source_pairs:
        source = resolve_source_path(manifest.get(path_field))
        if (not source.is_file() or source.stat().st_size <= 0
                or manifest.get(hash_field) != sha256(source)):
            source_hashes_ok = False
    expected_rows = int(manifest.get("matched_rows" if head == "PSC" else "n_matched", -1))
    expected_native = {
        "DCL": "dcl_mean_sigmoid_bit_margin",
        "CSL": "csl_softmax_top1_top2_margin",
    }
    common_ok = (
        manifest.get("status") == "complete"
        and manifest.get("schema_version") == K2_SOURCE_SCHEMA[head]
        and manifest.get("run_id") == run_id
        and manifest.get("dataset") == dataset
        and int(manifest.get("seed", -1)) == seed
        and int(manifest.get("n_images", -1)) == K2_EXPECTED_IMAGES[dataset]
        and int(manifest.get("n_gt", -1)) == K2_EXPECTED_GT[dataset]
        and expected_rows == int(frozen_eval["n_matched"]) > 0
        and manifest.get("no_training") is True
        and recorded_path == path.resolve()
        and recorded_eval == expected_eval
        and manifest.get("k2_eval_sha256") == sha256(expected_eval)
        and int(manifest.get("matched_bytes", -1)) == path.stat().st_size
        and manifest.get("matched_sha256") == sha256(path)
        and source_hashes_ok
        and "/dev/shm" not in json.dumps(manifest)
    )
    if head != "PSC":
        common_ok = common_ok and (
            manifest.get("head") == head
            and manifest.get("native_signal") == expected_native[head]
            and manifest.get("identity_only") is True
            and manifest.get("post_nms_own_detector_matching") is True
            and manifest.get("no_ap_evaluation") is True
        )
    if not common_ok:
        raise RuntimeError(f"invalid per-instance K2 endpoint manifest: {manifest_path}")

    images, risk, gt_ar, near_square, native, detection = [], [], [], [], [], []
    identities = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            identity = (str(row.get("image_id")), int(row.get("pred_id", -1)))
            expected_signal = expected_native.get(head)
            identity_ok = (
                row.get("dataset") == dataset
                and int(row.get("seed", -1)) == seed
                and identity[0] not in {"", "None"}
                and identity[1] >= 0
                and (head == "PSC" or (
                    row.get("head") == head
                    and row.get("native_signal") == expected_signal
                    and row.get("post_nms") is True
                ))
            )
            if not identity_ok:
                raise RuntimeError(f"K2 endpoint identity drift at {path}:{line_number}: {identity}")
            if identity in identities:
                raise RuntimeError(f"duplicate K2 endpoint identity at {path}:{line_number}: {identity}")
            identities.add(identity)
            try:
                pred_box = [float(value) for value in row["pred_box"]]
                gt_box = [float(value) for value in row["gt_box"]]
                angle_error = float(row["angle_error"])
                score = float(row.get("detection_score", row.get("score")))
                native_score = float(row["phase_mod_primary"] if head == "PSC" else row["native_score"])
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(f"invalid K2 endpoint row at {path}:{line_number}") from exc
            if (len(pred_box) != 5 or len(gt_box) != 5
                    or not all(math.isfinite(value) for value in pred_box + gt_box)
                    or pred_box[2] <= 0 or pred_box[3] <= 0 or gt_box[2] <= 0 or gt_box[3] <= 0
                    or not all(math.isfinite(value) for value in (angle_error, score, native_score))
                    or not 0 <= angle_error <= 90 or not 0 <= score <= 1
                    or native_score < 0 or (head != "PSC" and native_score > 1)):
                raise RuntimeError(f"nonfinite K2 endpoint row at {path}:{line_number}")
            ar = max(gt_box[2], gt_box[3]) / max(min(gt_box[2], gt_box[3]), 1e-12)
            recorded_ar = float(row["aspect_ratio"])
            if not math.isfinite(recorded_ar) or not math.isclose(ar, recorded_ar, rel_tol=1e-6, abs_tol=1e-6):
                raise RuntimeError(f"GT aspect-ratio drift at {path}:{line_number}")
            images.append(identity[0])
            risk.append(angle_error)
            gt_ar.append(ar)
            near_square.append(
                is_near_square(pred_box[2], pred_box[3]) or is_near_square(gt_box[2], gt_box[3]))
            native.append(native_score)
            detection.append(score)
    if len(risk) != expected_rows:
        raise RuntimeError(f"K2 endpoint cardinality mismatch {run_id}: {len(risk)} != {expected_rows}")
    return {
        "image": np.asarray(images, dtype=object),
        "risk": np.asarray(risk, dtype=float),
        "gt_ar": np.asarray(gt_ar, dtype=float),
        "near_square": np.asarray(near_square, dtype=bool),
        "native": np.asarray(native, dtype=float),
        "detection": np.asarray(detection, dtype=float),
        "manifest_sha256": sha256(manifest_path),
    }


def append_k2_rows(main_rows, sensitivity_rows):
    """Complete all K2 score metrics from validated, persisted per-instance endpoints."""
    frozen = validate_k2_eval_index()
    for head in K2_HEADS:
        for dataset in K2_DATASETS:
            for seed in K2_SEEDS:
                result = frozen[(head, dataset, seed)]
                endpoint = load_k2_endpoint(head, dataset, seed, result)
                total = len(endpoint["risk"])
                scores = {
                    f"native_{head}": endpoint["native"],
                    f"score_{head}": endpoint["detection"],
                }
                for threshold, destination in (
                        (2.1, main_rows), (1.6, sensitivity_rows), (1.3, sensitivity_rows)):
                    mask = (
                        (endpoint["gt_ar"] >= threshold)
                        & (~endpoint["near_square"])
                        & np.isfinite(endpoint["risk"])
                    )
                    for score_name, score in scores.items():
                        block = metrics(
                            score[mask], endpoint["risk"][mask], endpoint["image"][mask],
                            threshold == 2.1)
                        note = (
                            "PSC primary phase_mod from frozen K2 per-instance Phase-1 base; "
                            "all metrics completed without K2 rerun"
                            if head == "PSC" and score_name == "native_PSC"
                            else "frozen K2 detection score on the same persisted matched endpoint"
                            if score_name.startswith("score_")
                            else f"{head} native signal from targeted frozen-K2 identity endpoint; all metrics complete"
                        )
                        destination.append(dict(
                            cell=f"K2:{result['run_id']}", dataset=dataset, detector=f"k2_{head}",
                            score_type=score_name,
                            mask_definition="matched_gt_ar_ge_thr_exclude_pred_or_gt_near_square",
                            ar_threshold=threshold, retained_count=block["n"],
                            retained_ratio=round(block["n"] / total, 6), nrc=block["nrc"],
                            aurc=block["aurc"], risk70=block["r70"], risk90=block["r90"],
                            nrc_ci_lo=block["lo"], nrc_ci_hi=block["hi"],
                            source_lineage=("m069_psc_phase1_frozen_k2_per_instance"
                                            if head == "PSC"
                                            else "m069_psc_phase1_targeted_native_frozen_k2"),
                            metric_completeness="complete",
                            note=f"{note}; source_manifest_sha256={endpoint['manifest_sha256']}",
                            evaluation_scope="frozen_full_validation_endpoint",
                        ))
                lg(f"M1 K2 endpoint {head}/{dataset}/seed{seed}: matched={total} complete_metrics=True")


def build_direction_audit(main_rows, sensitivity_rows):
    keyed = {(r["cell"], r["score_type"], float(r["ar_threshold"])): r for r in main_rows + sensitivity_rows}
    rows = []
    all_cells = sorted({row["cell"] for row in main_rows})
    for cell_key in all_cells:
        score_names = sorted({r["score_type"] for r in main_rows if r["cell"] == cell_key})
        for score_name in score_names:
            new = keyed.get((cell_key, score_name, 2.1))
            old = keyed.get((cell_key, score_name, 1.6))
            if not new or not old:
                continue
            for metric_name, column in (("NRC", "nrc"), ("AURC", "aurc"), ("Risk@70", "risk70"), ("Risk@90", "risk90")):
                try:
                    old_value, new_value = float(old[column]), float(new[column])
                except (TypeError, ValueError):
                    continue
                if metric_name == "NRC":
                    old_dir, new_dir = direction(old_value), direction(new_value)
                    changed = old_dir != new_dir
                else:
                    delta = new_value - old_value
                    old_dir, new_dir = "ar1.6_reference", "higher" if delta > 0 else "lower" if delta < 0 else "unchanged"
                    changed = abs(delta) > 1e-12
                rows.append(dict(
                    metric=metric_name, cell=cell_key, dataset=new["dataset"], detector=new["detector"],
                    score_type=score_name, old_ar16_value=old_value, new_ar21_value=new_value,
                    direction_old=old_dir, direction_new=new_dir, conclusion_changed=changed,
                    interpretation=("NRC direction changed; old claim superseded" if metric_name == "NRC" and changed
                                    else "ar2.1 value is authoritative; ar1.6 sensitivity only"),
                ))
    return rows


def write_csv(path, rows, fields):
    temporary = f"{path}.tmp"
    with open(temporary, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def main():
    main_rows, sensitivity_rows = [], []
    cells = M.FROZEN_CELLS + [c for c in M.DOTA_CELLS if os.path.isfile(M.CELLS[c][2])]
    for cell_key in cells:
        append_score_rows(cell_key, main_rows, sensitivity_rows)
    append_k2_rows(main_rows, sensitivity_rows)
    write_csv(MAIN_CSV, main_rows, FIELDS)
    write_csv(SENS_CSV, sensitivity_rows, FIELDS)
    audit = build_direction_audit(main_rows, sensitivity_rows)
    audit_fields = [
        "metric", "cell", "dataset", "detector", "score_type", "old_ar16_value", "new_ar21_value",
        "direction_old", "direction_new", "conclusion_changed", "interpretation",
    ]
    write_csv(AUDIT_CSV, audit, audit_fields)
    nrc_changes = [r for r in audit if r["metric"] == "NRC" and r["conclusion_changed"]]
    verdict = "PASS"
    write_csv(f"{REP}/m1_decision.csv", [dict(
        decision=verdict, changed_nrc_directions=len(nrc_changes), main_rows=len(main_rows),
        sensitivity_rows=len(sensitivity_rows), main_mask="ar>=2.1", legacy_masks="sensitivity_only",
    )], ["decision", "changed_nrc_directions", "main_rows", "sensitivity_rows", "main_mask", "legacy_masks"])

    doc = [
        "# M1: ar>=2.1 protocol unification", "",
        "- The only main-table mask is `ar>=2.1`; `ar>=1.6` and `ar>=1.3` are sensitivity only.",
        "- The evaluation mask uses matched-GT aspect ratio; selector geometry uses prediction-box w/h only. `near_square` excludes instability in either matched box.",
        "- A-F use lineage-clean full-validation dumps. Phase and TTA fields come from the same forward and stable detection match, not a local `pred_id` join.",
        "- Every score row records mask, threshold, retained count, retained ratio, source lineage, and metric completeness.",
        "- K2 training and its evaluator matrix are not rerun. Complete PSC phase-modulus metrics use the persisted Phase-1 matched base; complete DCL/CSL native metrics use the preregistered targeted identity-only frozen-checkpoint endpoint dumps (no AP evaluation).",
        "- All K2 endpoint masks are recomputed under the unified matched-GT aspect-ratio definition and exclude near-square prediction or GT geometry; old prediction-AR K2 summary masks are superseded for M1.",
        "- Image-level LTT is authoritative in `m3_image_level_ltt.csv`; GT-noise proxy remains separately authoritative in `k3_gt_angle_noise_by_dataset.csv` and is not called human noise.",
        "- DOTA clean cells remain the two K4b full-val cells; DOTA#20 is excluded.",
        f"- NRC direction changes from ar1.6 to ar2.1: {len(nrc_changes)}. New ar2.1 values supersede the old narrative.",
        f"- **M1 decision: {verdict}.**", "", "## NRC direction changes",
        "| cell | score | ar1.6 | ar2.1 | old | new |", "|---|---|---:|---:|---|---|",
    ]
    for row in nrc_changes:
        doc.append(f"| {row['cell']} | {row['score_type']} | {row['old_ar16_value']} | {row['new_ar21_value']} | {row['direction_old']} | {row['direction_new']} |")
    if not nrc_changes:
        doc.append("| none | | | | | |")
    doc_path = f"{DOC}/m1_ar21_protocol_unification.md"
    with open(f"{doc_path}.tmp", "w", encoding="utf-8") as f:
        f.write("\n".join(doc) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(f"{doc_path}.tmp", doc_path)
    lg(f"M1 DONE verdict={verdict} main={len(main_rows)} sensitivity={len(sensitivity_rows)} NRC_changes={len(nrc_changes)}")


if __name__ == "__main__":
    main()

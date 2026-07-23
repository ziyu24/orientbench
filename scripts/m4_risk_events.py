"""Compute M4 risk events under the frozen ar>=2.1 protocol.

Primary risk is ``angle_error > delta_theta_0.75(aspect_ratio)`` under the
le90, concentric, same-scale rectangle model. Fixed 5/10/15-degree events are
sensitivity endpoints. Inputs with the known DIOR 052 wrong-split lineage fail
before any formal M4 table is replaced.
"""

import csv
import hashlib
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/scripts")
import m069_common as M
from derive_delta_theta_075 import (
    ANGLE_CONVENTION,
    FROZEN_AT,
    GEOMETRY_MODEL,
    HIGH_AR_POLICY,
    SOLVE_TOL_DEG,
    THRESHOLD_SEMANTICS,
)


ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
DOC = f"{ROOT}/docs"

LINEAGE_CSV = f"{REP}/m4_input_lineage_audit.csv"
STABILITY_CSV = f"{REP}/m4_observed_ar_numerical_stability.csv"
DIRECT_STABILITY_CSV = f"{REP}/m4_delta_theta_direct_solve_stability.csv"

# K3 corner-jitter proxy, used only to flag interpretation sensitivity. It is
# neither a human annotation estimate nor sigma_gt and never defines a threshold.
NOISE_FLOOR_AR21 = {
    "DIOR-R": 3.0,
    "FAIR1M-v1.0": 4.5,
    "SODA-A": 5.9,
    "DOTA-v1.0": None,
}
DIOR_TEST_ID_MIN = 11726
DIOR_TEST_ID_MAX = 23463


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fp:
        for block in iter(lambda: fp.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _numeric_image_ids(values):
    parsed = []
    for value in np.unique(values):
        text = str(value)
        if not text.isdigit():
            return None
        parsed.append(int(text))
    return np.asarray(parsed, dtype=int)


def _lineage_record(cell, C):
    source_path = os.path.abspath(M.CELLS[cell][2])
    exists = os.path.isfile(source_path)
    reasons = []
    if not exists:
        reasons.append("source_missing")
    if source_path.startswith("/dev/shm/"):
        reasons.append("ephemeral_dev_shm_source")

    dataset = str(C["dataset"])
    image_ids = _numeric_image_ids(C["img"]) if dataset == "DIOR-R" else None
    image_id_min = int(image_ids.min()) if image_ids is not None and image_ids.size else ""
    image_id_max = int(image_ids.max()) if image_ids is not None and image_ids.size else ""
    if dataset == "DIOR-R":
        if "orientbench_real_052/matched_tables/DIOR-R" in source_path:
            reasons.append("known_052_partial_wrong_split")
        if image_ids is None or image_ids.size == 0:
            reasons.append("dior_image_ids_not_numeric_or_empty")
        elif np.any((image_ids < DIOR_TEST_ID_MIN) | (image_ids > DIOR_TEST_ID_MAX)):
            reasons.append("dior_ids_outside_frozen_test_range")

    status = "PASS_FULLVAL_LINEAGE" if not reasons else "FAIL_PARTIAL_OR_EPHEMERAL_LINEAGE"
    return {
        "cell": cell,
        "dataset": dataset,
        "detector": C["detector"],
        "source_path": source_path,
        "source_sha256": _sha256(source_path) if exists else "",
        "n_matched_rows": int(len(C["ae"])),
        "n_matched_images": int(len(np.unique(C["img"]))),
        "image_id_min": image_id_min,
        "image_id_max": image_id_max,
        "lineage_status": status,
        "reason": "|".join(reasons),
        "can_recompute_cpu": bool(exists and not reasons),
    }


def _preflight_cells(cells):
    loaded = []
    lineage = []
    for cell in cells:
        if cell in M.FROZEN_CELLS:
            M.verify_fullval_lineage(cell)
        C = M.load_cell(cell)
        record = _lineage_record(cell, C)
        loaded.append((cell, C, record))
        lineage.append(record)
    _wr(LINEAGE_CSV, lineage)
    failed = [r for r in lineage if not r["lineage_status"].startswith("PASS")]
    if failed:
        detail = "; ".join(f"{r['cell']}:{r['reason']}" for r in failed)
        raise RuntimeError(
            "M4 input-lineage preflight failed before formal-table write: " + detail
        )
    return loaded


def _validate_frozen_geometry(frozen):
    expected = {
        "schema_version": "m4_delta_theta_075_v2",
        "frozen_at": FROZEN_AT,
        "definition_changed": False,
        "tau_main": 0.75,
        "angle_convention": ANGLE_CONVENTION,
        "geometry_model": GEOMETRY_MODEL,
    }
    problems = []
    for key, value in expected.items():
        # Legacy JSON did not record the two textual fields. It remains usable
        # only for lookup; a formal 069 run must regenerate the v2 metadata.
        if frozen.get(key) != value:
            problems.append(f"{key}={frozen.get(key)!r}, expected {value!r}")
    if float(frozen.get("solve_tolerance_deg", float("nan"))) != SOLVE_TOL_DEG:
        problems.append(
            f"solve_tolerance_deg={frozen.get('solve_tolerance_deg')!r}, "
            f"expected {SOLVE_TOL_DEG}"
        )
    if frozen.get("high_ar_policy") != HIGH_AR_POLICY:
        problems.append(
            f"high_ar_policy={frozen.get('high_ar_policy')!r}, "
            f"expected {HIGH_AR_POLICY!r}"
        )
    if frozen.get("threshold_semantics") != THRESHOLD_SEMANTICS:
        problems.append(
            f"threshold_semantics={frozen.get('threshold_semantics')!r}, "
            f"expected {THRESHOLD_SEMANTICS!r}"
        )
    if not frozen.get("stability_all_pass", False):
        problems.append("direct-solve stability audit is not PASS")
    if problems:
        raise RuntimeError(
            "M4 frozen geometry metadata is legacy/incomplete; run the approved "
            "derive_delta_theta_075.py regeneration first: " + "; ".join(problems)
        )
    if not os.path.isfile(DIRECT_STABILITY_CSV):
        raise RuntimeError(f"missing direct-solve stability audit: {DIRECT_STABILITY_CSV}")
    direct_rows = list(csv.DictReader(open(DIRECT_STABILITY_CSV, encoding="utf-8")))
    if not direct_rows or any(r.get("stability_pass") != "True" for r in direct_rows):
        raise RuntimeError("M4 direct-solve stability audit is empty or contains failures")


def _main_mask(C):
    ar = np.asarray(C["ar"], dtype=float)
    ae = np.asarray(C["ae"], dtype=float)
    return (ar >= M.AR_MAIN) & (~np.asarray(C["near_square"], dtype=bool)) & np.isfinite(ar) & np.isfinite(ae)


def run():
    frozen_path = f"{REP}/m4_delta_theta_075_frozen.json"
    with open(frozen_path, encoding="utf-8") as fp:
        frozen = json.load(fp)
    frozen_sha256 = _sha256(frozen_path)

    cells = M.FROZEN_CELLS + [
        c for c in M.DOTA_CELLS if os.path.isfile(M.CELLS[c][2])
    ]
    # Audit source lineage first so a known partial/wrong split is recorded and
    # rejected even when the frozen numerical metadata also needs regeneration.
    loaded = _preflight_cells(cells)
    _validate_frozen_geometry(frozen)
    grid_max = float(frozen["ar_grid_max"])

    geo_rows = []
    sens_rows = []
    stability_rows = []
    delta_at_ar21 = float(M.delta_theta_075(M.AR_MAIN))

    for cell, C, lineage in loaded:
        mask = _main_mask(C)
        if not np.any(mask):
            raise RuntimeError(f"M4 {cell} has no finite ar>={M.AR_MAIN} observations")
        ae = np.asarray(C["ae"], dtype=float)[mask]
        ar = np.asarray(C["ar"], dtype=float)[mask]
        dtheta = np.asarray([M.delta_theta_075(value) for value in ar], dtype=float)
        if np.any(~np.isfinite(dtheta)) or np.any(dtheta < 0.0):
            raise RuntimeError(f"M4 {cell} produced invalid delta-theta values")
        severe = ae > dtheta
        floor = NOISE_FLOOR_AR21.get(C["dataset"])
        eligible = int(np.isfinite(np.asarray(C["ae"], dtype=float)).sum())
        retained_ratio = float(mask.sum() / eligible) if eligible else float("nan")
        above_legacy = ar > 8.0
        above_grid = ar > grid_max

        stability_rows.append({
            "cell": cell,
            "dataset": C["dataset"],
            "ar_threshold": M.AR_MAIN,
            "n_main": int(mask.sum()),
            "ar_min": float(np.min(ar)),
            "ar_median": float(np.median(ar)),
            "ar_p99": float(np.percentile(ar, 99)),
            "ar_max": float(np.max(ar)),
            "n_ar_gt_legacy8": int(above_legacy.sum()),
            "ratio_ar_gt_legacy8": round(float(above_legacy.mean()), 6),
            "n_ar_gt_grid_max": int(above_grid.sum()),
            "ratio_ar_gt_grid_max": round(float(above_grid.mean()), 6),
            "delta_theta_min_deg": float(np.min(dtheta)),
            "delta_theta_max_deg": float(np.max(dtheta)),
            "solve_tolerance_deg": SOLVE_TOL_DEG,
            "delta_theta_curve_sha256": frozen_sha256,
            "grid_max_ar": grid_max,
            "high_ar_policy": HIGH_AR_POLICY,
            "legacy_ar8_clamp_used": False,
            "nonfinite_delta_count": int((~np.isfinite(dtheta)).sum()),
            "stability_pass": True,
        })

        common = {
            "cell": cell,
            "dataset": C["dataset"],
            "detector": C["detector"],
            "mask_definition": "matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square",
            "aspect_ratio_source": "matched_GT_box",
            "ar_threshold": M.AR_MAIN,
            "retained_count": int(mask.sum()),
            "retained_ratio": round(retained_ratio, 4),
            "angle_convention": ANGLE_CONVENTION,
            "geometry_model": GEOMETRY_MODEL,
            "solve_tolerance_deg": SOLVE_TOL_DEG,
            "delta_theta_curve_sha256": frozen_sha256,
            "threshold_semantics": THRESHOLD_SEMANTICS,
            "high_ar_policy": HIGH_AR_POLICY,
            "input_lineage_status": lineage["lineage_status"],
        }
        geo_rows.append({
            **common,
            "severe_event_rate": round(float(severe.mean()), 4),
            "mean_angle_err": round(float(ae.mean()), 3),
            "median_angle_err": round(float(np.median(ae)), 3),
            "p90_angle_err": round(float(np.percentile(ae, 90)), 3),
            "delta_theta_075_at_ar21": round(delta_at_ar21, 3),
            "observed_delta_theta_min": round(float(np.min(dtheta)), 6),
            "observed_delta_theta_max": round(float(np.max(dtheta)), 6),
            "n_ar_gt_legacy8": int(above_legacy.sum()),
            "n_ar_gt_grid_max": int(above_grid.sum()),
            "event_def": "angle_error_le90 > delta_theta_0.75(matched_GT_aspect_ratio)",
            "interpretation": (
                "Angle error reaches the rotation that makes concentric, "
                "same-scale rectangle IoU fall below 0.75; this is not a claim "
                "that the observed detection pair itself has IoU below 0.75."
            ),
        })
        for threshold in (5, 10, 15):
            rate = float((ae > threshold).mean())
            dataset_noise_sensitive = C["dataset"] in ("FAIR1M-v1.0", "SODA-A")
            threshold_near_proxy_floor = bool(
                floor is not None
                and threshold <= floor + 0.5
                and dataset_noise_sensitive
            )
            sens_rows.append({
                **common,
                "angle_threshold_deg": threshold,
                "event_rate": round(rate, 4),
                "interp": "fine-risk" if threshold == 5 else "interpretive sensitivity",
                "noise_sensitive": dataset_noise_sensitive,
                "threshold_near_proxy_floor": threshold_near_proxy_floor,
                "proxy_role": "corner-jitter proxy only; not sigma_gt or human disagreement",
                "note": (
                    "5deg is close to/below the dataset proxy floor; noise-sensitive"
                    if threshold_near_proxy_floor
                    else "dataset-level label-noise-sensitive interpretation"
                    if dataset_noise_sensitive
                    else ""
                ),
            })

    # All validation happens before replacing formal outputs.
    _wr(f"{REP}/m4_geometry_normalized_risk.csv", geo_rows)
    _wr(f"{REP}/m4_fixed_angle_sensitivity.csv", sens_rows)
    _wr(STABILITY_CSV, stability_rows)
    _write_doc(frozen, geo_rows, sens_rows, stability_rows)
    print(
        f"M4_DONE geo_rows={len(geo_rows)} sens_rows={len(sens_rows)} "
        f"stability_rows={len(stability_rows)}"
    )


def _write_doc(frozen, geo_rows, sens_rows, stability_rows):
    n_above8 = sum(int(r["n_ar_gt_legacy8"]) for r in stability_rows)
    n_extrap = sum(int(r["n_ar_gt_grid_max"]) for r in stability_rows)
    doc = [
        "# M4：风险事件定义\n",
        (
            "- 冻结主事件：`angle_error_le90 > delta_theta_0.75(aspect_ratio)`；"
            "角度采用 le90 长边朝向、pi 周期，几何模型为共中心、同尺度、全等矩形。"
        ),
        (
            f"- 数值求解为确定性多边形 IoU 二分，角度容差 {SOLVE_TOL_DEG} 度；"
            f"冻结定义未变（frozen_at={frozen['frozen_at']}，"
            f"derived_ar@15deg={frozen['derived_ar_at_15deg']}）。"
        ),
        (
            f"- 查找表扩展至 ar={frozen['ar_grid_max']}；ar>8 不再钳制到 ar=8；"
            f"超表范围采用 `{HIGH_AR_POLICY}`。本次主区 ar>8 共 {n_above8} 条，"
            f"超表范围 {n_extrap} 条。"
        ),
        (
            "- direct-solve 稳定性见 `m4_delta_theta_direct_solve_stability.csv`；"
            "观测 AR 支持域见 `m4_observed_ar_numerical_stability.csv`；"
            "输入 lineage 见 `m4_input_lineage_audit.csv`，partial/wrong-split 输入会在正式表写入前失败。"
        ),
        (
            "- 主口径唯一为 ar>=2.1；固定角度 >5 度（fine-risk）、>10 度、>15 度仅作敏感性。"
        ),
        "- 主掩码与几何归一化事件中的 aspect ratio 均来自 matched GT box；选择器侧预测几何与此评估几何分开记录。",
        (
            "- FAIR1M/SODA-A 的固定角度结果均作 dataset-level noise-sensitive 标记，其中 5 度阈值接近 proxy floor。corner-jitter 仅为 proxy，"
            "不是 sigma_gt、不是人工双标，不进入风险阈值定义。\n"
        ),
        "## Geometry-normalized 主风险（ar>=2.1）",
        "| cell | dataset | n | severe rate | mean error | p90 | delta@ar2.1 | n(ar>8) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in geo_rows:
        doc.append(
            f"| {row['cell']} | {row['dataset']} | {row['retained_count']} | "
            f"{row['severe_event_rate']} | {row['mean_angle_err']} | "
            f"{row['p90_angle_err']} | {row['delta_theta_075_at_ar21']} | "
            f"{row['n_ar_gt_legacy8']} |"
        )
    doc += [
        "\n## 固定角度敏感性（ar>=2.1）",
        "| cell | dataset | >5deg | >10deg | >15deg | 5deg noise-sensitive |",
        "|---|---|---:|---:|---:|---|",
    ]
    by_cell = {}
    for row in sens_rows:
        by_cell.setdefault(row["cell"], {})[row["angle_threshold_deg"]] = row
    for cell, values in by_cell.items():
        doc.append(
            f"| {cell} | {values[5]['dataset']} | {values[5]['event_rate']} | "
            f"{values[10]['event_rate']} | {values[15]['event_rate']} | "
            f"{values[5]['noise_sensitive']} |"
        )
    with open(f"{DOC}/m4_risk_event_definition.md", "w", encoding="utf-8") as fp:
        fp.write("\n".join(doc))


def _wr(path, rows):
    if not rows:
        raise ValueError(f"refusing to write empty M4 artifact: {path}")
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    run()

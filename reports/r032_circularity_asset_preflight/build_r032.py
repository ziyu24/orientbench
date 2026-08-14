#!/usr/bin/env python3
"""Build the r032 read-only asset preflight. No scientific contrast is computed."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import tarfile
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
OUT = ROOT / "reports/r032_circularity_asset_preflight"
R014 = SOURCE_ROOT / "outputs/persistent_artifacts/orientbench_r014"
R019 = SOURCE_ROOT / "outputs/persistent_artifacts/orientbench_r019"
M069 = SOURCE_ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
DATA = Path("/home/rspip/cqc/data/dataset")
PLAN = ROOT / "dis/plans/C/c-r032-circularity-asset-preflight-retry-20260814/sug.md"
STARTED = ROOT / "dis/server_reports/orientbench-c-r032-circularity-asset-preflight-retry-20260814/STARTED.json"

UNITS = {
    "A": ("DIOR-R", "Rotated RetinaNet PSC"),
    "B": ("DIOR-R", "Oriented R-CNN"),
    "C": ("DIOR-R", "Rotated RTMDet-S"),
    "D": ("FAIR1M-v1.0", "Rotated RetinaNet PSC"),
    "E": ("SODA-A", "Rotated RetinaNet PSC"),
    "F": ("SODA-A", "Oriented R-CNN"),
    "G": ("DOTA-v1.0 val", "Oriented R-CNN"),
    "H": ("DOTA-v1.0 val", "Rotated RTMDet-M"),
}
FIELDS = [
    "predicted_ar", "gt_ar", "class_id", "confidence", "predicted_width",
    "predicted_height", "canonical_angle_error", "row_key", "image_id",
    "mother_scene_id", "split_role", "official_annotation_id",
]
QUARANTINE = [
    "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations/",
    "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_final/",
    "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_v2/",
    "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/r026_raw_revalidation/error.json",
    "top_journal_v3_reaudit_055/measurement_validity_r022_20260813/",
    "top_journal_v3_reaudit_055/measurement_validity_r023_20260813/",
]
HASH_CACHE: dict[str, str] = {}


def sha(path: Path) -> str:
    key = str(path)
    if key in HASH_CACHE:
        return HASH_CACHE[key]
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    HASH_CACHE[key] = h.hexdigest()
    return HASH_CACHE[key]


def set_sha(values) -> str:
    payload = "\n".join(sorted(str(v) for v in values)) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    HASH_CACHE.pop(str(path), None)
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    HASH_CACHE.pop(str(path), None)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def parquet_schema(path: Path) -> tuple[str, int]:
    meta = pq.read_metadata(path)
    return "|".join(meta.schema.names), meta.num_rows


def jsonl_schema_count(path: Path) -> tuple[str, int]:
    count = 0
    keys = None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            count += 1
            if keys is None:
                keys = sorted(json.loads(line))
    return "|".join(keys or []), count


def csv_schema_count(path: Path) -> tuple[str, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        count = sum(1 for _ in reader)
    return "|".join(header), count


def quarantine_rows() -> list[dict]:
    rows = []
    for rel_root in QUARANTINE:
        path = ROOT / rel_root
        if path.is_file():
            paths = [path]
        elif path.is_dir():
            paths = sorted(p for p in path.rglob("*") if p.is_file())
        else:
            paths = []
        for item in paths:
            rows.append({"relative_path": item.relative_to(ROOT).as_posix(), "bytes": item.stat().st_size, "sha256": sha(item)})
    return rows


def official_manifest(name: str, paths: list[Path], logical_root: Path) -> tuple[Path, int, int, str]:
    rows = []
    for path in sorted(paths, key=lambda p: p.name):
        rows.append({"relative_path": path.relative_to(logical_root).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    dest = OUT / "official_manifests" / f"{name}.csv"
    write_csv(dest, rows, ["relative_path", "bytes", "sha256"])
    return dest, len(rows), sum(int(r["bytes"]) for r in rows), sha(dest)


def source_spec(unit: str) -> dict[str, Path]:
    if unit in "ABCDEF":
        return {
            "cohort": ROOT / "audit_bundles/r028/dior/rows.parquet",
            "features": R014 / f"features/{unit}.parquet",
            "scores": R014 / f"scores/{unit}.parquet",
            "matched_geometry": M069 / f"{unit}/matched_fullval.jsonl",
            "cluster_map": (R014 / "soda_tile_to_mother_r014.csv") if unit in "EF" else (M069 / f"{unit}/image_universe.csv"),
        }
    slug = "orcnn" if unit == "G" else "rtmdet"
    return {
        "cohort": ROOT / f"audit_bundles/r028/dota/matched_{slug}.parquet",
        "features": R019 / f"prelabel/target_features/{slug}.parquet",
        "scores": R019 / f"prelabel/target_scores/{slug}.parquet",
        "matched_geometry": SOURCE_ROOT / f"top_journal_v3_reaudit_055/reports/m_dota_clean_perinstance/DOTA_{slug}.jsonl",
        "cluster_map": ROOT / "audit_bundles/r028/dota/tile_to_mother.csv",
    }


def cohort_frame(unit: str) -> pd.DataFrame:
    spec = source_spec(unit)
    frame = pd.read_parquet(spec["cohort"])
    if unit in "ABCDEF":
        frame = frame.loc[frame["unit"].astype(str) == unit].copy()
    return frame


def tokens(frame: pd.DataFrame) -> list[str]:
    return (frame["image_id"].astype(str) + "\x1f" + frame["pred_id"].astype(str)).tolist()


def jsonl_tokens(path: Path) -> tuple[list[str], int, int, str, int, int]:
    values = []
    schema = None
    missing = 0
    finite = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            schema = schema or sorted(row)
            values.append(f"{row['image_id']}\x1f{row['pred_id']}")
            value = row.get("angle_error")
            if value is None:
                missing += 1
            elif isinstance(value, (int, float)) and math.isfinite(value):
                finite += 1
            else:
                missing += 1
    return values, len(values), len(values) - len(set(values)), "|".join(schema or []), finite, missing


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    started = json.loads(STARTED.read_text())
    before = quarantine_rows()
    write_csv(OUT / "legacy_quarantine_before.csv", before, ["relative_path", "bytes", "sha256"])

    # Official immutable inventories. FAIR split membership is read from its archived split manifest;
    # no extraction, conversion, or repair is performed.
    dior_root = DATA / "DIOR/annfiles/obb"
    dior_ids = {x.strip() for x in (DATA / "DIOR/splits/test.txt").read_text().splitlines() if x.strip()}
    dior_paths = [dior_root / f"{x}.xml" for x in sorted(dior_ids)]
    if not all(p.is_file() for p in dior_paths):
        raise RuntimeError("DIOR official test XML set incomplete")
    dior_manifest = official_manifest("dior_test", dior_paths, dior_root)

    fair_tar = DATA / "fair1m1.0/tools/_split_workspace.tar.gz"
    with tarfile.open(fair_tar, "r:gz") as archive:
        text = archive.extractfile("_split_workspace/split_manifest.txt").read().decode()
    section = None
    fair_val = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            section = line.strip("[]")
        elif section == "val" and line.endswith(".tif"):
            fair_val.append(Path(line).stem)
    fair_root = DATA / "fair1m1.0/raw/train/labelXml"
    fair_paths = [fair_root / f"{x}.xml" for x in sorted(fair_val)]
    if len(fair_paths) != 3298 or not all(p.is_file() for p in fair_paths):
        raise RuntimeError(f"FAIR official val XML set incomplete: {len(fair_paths)}")
    fair_manifest = official_manifest("fair1m_val", fair_paths, fair_root)

    soda_root = DATA / "SODA-A/Annotations/val"
    soda_paths = sorted(soda_root.glob("*.json"))
    soda_manifest = official_manifest("soda_val", soda_paths, soda_root)
    dota_root = DATA / "dota/dota1.0/val/annfiles"
    dota_paths = sorted(dota_root.glob("*.txt"))
    dota_manifest = official_manifest("dota_val", dota_paths, dota_root)

    official_rows = []
    for dataset, split, root, archive, result in [
        ("DIOR-R", "test", dior_root, "", dior_manifest),
        ("FAIR1M-v1.0", "val(seed=20260503,ratio=0.2)", fair_root, str(fair_tar), fair_manifest),
        ("SODA-A", "val", soda_root, "", soda_manifest),
        ("DOTA-v1.0", "val", dota_root, "", dota_manifest),
    ]:
        child, count, total, digest = result
        official_rows.append({"dataset": dataset, "split": split, "official_root": str(root), "split_authority": archive or str(root), "file_count": count, "bytes": total, "manifest_path": str(child), "manifest_sha256": digest, "status": "PASS_INVENTORIED"})
    write_csv(OUT / "official_annotation_inventory.csv", official_rows)

    converted_gt = ROOT / "audit_bundles/r028/dota/dota_gt_fresh.pkl"
    tile_map = ROOT / "audit_bundles/r028/dota/tile_to_mother.csv"
    gt_integrity = ROOT / "audit_bundles/r028/dota/gt_integrity.json"
    write_json(OUT / "dota_gt_provenance.json", {
        "status": "PASS_PROVENANCE_ONLY_NO_EQUIVALENCE_CLAIM",
        "official_raw": {"path": str(dota_root), "file_count": len(dota_paths), "manifest_path": str(dota_manifest[0]), "manifest_sha256": dota_manifest[3]},
        "persistent_converted_gt": {"path": str(converted_gt), "bytes": converted_gt.stat().st_size, "sha256": sha(converted_gt)},
        "tile_to_mother": {"path": str(tile_map), "bytes": tile_map.stat().st_size, "sha256": sha(tile_map)},
        "integrity_witness": {"path": str(gt_integrity), "bytes": gt_integrity.stat().st_size, "sha256": sha(gt_integrity)},
        "source_code": {"path": str(ROOT / "p3_selector/deployable_proxy_r019/scripts/label_attach_results_r019.py"), "lines": "84-114"},
        "known_counts": {"tiles": 5297, "mothers": 458, "gt_objects": 55804},
        "semantic_equality_claimed": False,
    })

    # Source and join inventories.
    source_rows = []
    join_rows = []
    cohorts: dict[str, pd.DataFrame] = {}
    for unit, (dataset, detector) in UNITS.items():
        cohort = cohort_frame(unit)
        cohorts[unit] = cohort
        cohort_keys = tokens(cohort)
        cohort_set = set(cohort_keys)
        if len(cohort_keys) != len(cohort_set):
            raise RuntimeError(f"cohort duplicate: {unit}")
        spec = source_spec(unit)
        for role, path in spec.items():
            if path.suffix == ".parquet":
                schema, count = parquet_schema(path)
            elif path.suffix == ".jsonl":
                schema, count = jsonl_schema_count(path)
            else:
                schema, count = csv_schema_count(path)
            source_rows.append({"unit": unit, "dataset": dataset, "detector": detector, "semantic_role": role, "absolute_path": str(path), "exists": True, "bytes": path.stat().st_size, "sha256": sha(path), "format": path.suffix.lstrip("."), "schema": schema, "row_count": count, "read_only": True, "witness_source": "frozen existing asset; r032 read-only"})

        role_values: dict[str, tuple[list[str], int, int, str, int, int, str]] = {}
        role_values["cohort"] = (cohort_keys, len(cohort), 0, "|".join(cohort.columns), len(cohort), 0, "row_key")
        for role in ("features", "scores"):
            p = spec[role]
            frame = pd.read_parquet(p, columns=["image_id", "pred_id"])
            vals = tokens(frame)
            role_values[role] = (vals, len(vals), len(vals) - len(set(vals)), "image_id|pred_id", len(vals), 0, "row_key")
        vals, count, dup, schema, finite, missing = jsonl_tokens(spec["matched_geometry"])
        role_values["matched_geometry"] = (vals, count, dup, schema, finite, missing, "row_key")

        cluster = pd.read_csv(spec["cluster_map"], dtype=str)
        image_col = "tile_id" if "tile_id" in cluster.columns else ("stem" if "stem" in cluster.columns else "image_id")
        cvals = cluster[image_col].astype(str).tolist()
        role_values["cluster_map"] = (cvals, len(cvals), len(cvals) - len(set(cvals)), "|".join(cluster.columns), len(cvals), 0, "image_id")
        # Class labels are carried by features for A-F and by the frozen cohort for G-H.
        if unit in "ABCDEF":
            p = spec["features"]
            frame = pd.read_parquet(p, columns=["image_id", "pred_id", "class_id"])
            vals = tokens(frame)
            missing_class = int(frame["class_id"].isna().sum())
            role_values["class_labels"] = (vals, len(vals), len(vals) - len(set(vals)), "image_id|pred_id|class_id", len(vals) - missing_class, missing_class, "row_key")
        else:
            vals = cohort_keys
            missing_class = int(cohort["class_id"].isna().sum())
            role_values["class_labels"] = (vals, len(vals), 0, "image_id|pred_id|class_id", len(vals) - missing_class, missing_class, "row_key")

        for role, (vals, count, dup, schema, finite, missing, key_type) in role_values.items():
            source_set = set(vals)
            if key_type == "row_key":
                absent = cohort_set - source_set
                extras = source_set - cohort_set
            else:
                cohort_images = set(cohort["image_id"].astype(str))
                absent = cohort_images - source_set
                extras = source_set - cohort_images
            join_rows.append({
                "unit": unit, "source_role": role, "source_path": str(spec.get(role, spec["features"] if role == "class_labels" and unit in "ABCDEF" else spec["cohort"])),
                "key_type": key_type, "schema": schema, "row_count": count, "unique_key_count": len(source_set), "duplicate_count": dup,
                "finite_count": finite, "missing_count": missing, "cohort_key_count": len(cohort_set) if key_type == "row_key" else len(set(cohort["image_id"].astype(str))),
                "cohort_missing_count": len(absent), "cohort_drop_count": len(absent), "extra_count": len(extras),
                "extras_sorted_key_sha256": set_sha(extras), "status": "PASS" if dup == 0 and not absent else "FAIL",
            })
    write_csv(OUT / "source_inventory.csv", source_rows)
    write_csv(OUT / "join_feasibility.csv", join_rows)

    # Complete 8 x 12 field matrix. The local gt_id is an ordinal in processed/tiled
    # annotations; no frozen witness maps it back to a stable official raw-object ID.
    field_rows = []
    for unit in UNITS:
        spec = source_spec(unit)
        matched = str(spec["matched_geometry"])
        cohort = str(spec["cohort"])
        features = str(spec["features"])
        scores = str(spec["scores"])
        matrix = {
            "predicted_ar": ("DERIVABLE", matched, "pred_obb.obb_w|pred_obb.obb_h", "long-side ratio", str(ROOT / "scripts/m069_common.py"), "55-78", "frozen geometry transform"),
            "gt_ar": ("DIRECT", matched if unit in "ABCDEF" else cohort, "aspect_ratio" if unit in "ABCDEF" else "ar", "", "", "", "frozen matched label"),
            "class_id": ("DIRECT", features if unit in "ABCDEF" else cohort, "class_id", "", "", "", "frozen class label"),
            "confidence": ("DIRECT", scores, "detection_score", "", "", "", "frozen detector confidence"),
            "predicted_width": ("DIRECT", matched, "pred_obb.obb_w", "", "", "", "frozen matched geometry"),
            "predicted_height": ("DIRECT", matched, "pred_obb.obb_h", "", "", "", "frozen matched geometry"),
            "canonical_angle_error": ("DIRECT", matched if unit in "ABCDEF" else cohort, "angle_error" if unit in "ABCDEF" else "angle_error", "", "", "", "canonical long-side error persisted"),
            "row_key": ("DERIVABLE", matched, "image_id|pred_id", "tuple(image_id,pred_id)", str(ROOT / "p3_selector/deployable_proxy_r014/scripts/evaluate_eqs_r014.py"), "112-118", "existing uniqueness contract"),
            "image_id": ("DIRECT", matched, "image_id", "", "", "", "frozen identifier"),
            "mother_scene_id": (("DIRECT", str(spec["cluster_map"]), "mother_scene_id" if unit in "EF" else "mother", "", "", "", "frozen tile mapping") if unit in "EFGH" else ("DERIVABLE", matched, "image_id", "identity(image_id)", str(ROOT / "p3_selector/deployable_proxy_r014/scripts/evaluate_eqs_r014.py"), "104-106", "non-tiled image is its cluster")),
            "split_role": ("DIRECT", matched, "d_cal_daudit_split_flag", "", "", "", "frozen split flag"),
            "official_annotation_id": ("MISSING", "", "", "not available", "", "", "gt_id is only a processed/tiled per-image ordinal; no frozen raw-object back-map"),
        }
        for field in FIELDS:
            status, source_path, source_column, transform, transform_path, line, witness = matrix[field]
            field_rows.append({"unit": unit, "field": field, "status": status, "source_path": source_path, "source_column": source_column, "transform_needed": transform, "transform_source_path": transform_path, "transform_line": line, "witness": witness})
    write_csv(OUT / "field_availability.csv", field_rows)

    table1 = ROOT / "top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv"
    dota_ap = SOURCE_ROOT / "outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/dota_ap_parity.csv"
    support_rows = []
    for unit in UNITS:
        manifest = (M069 / f"{unit}/manifest.json") if unit in "ABCDEF" else (R019 / "prelabel/image_only_registry.json")
        for item, path, location, status in [
            ("public_unit_name", PLAN, "fixed-unit table", "DIRECT"),
            ("config_checkpoint_identity", manifest, "config/checkpoint path and SHA", "DIRECT"),
            ("AP50_AP75", table1 if unit in "ABCDEF" else dota_ap, "unit row", "DIRECT"),
            ("matching_threshold_and_classwise_one_to_one", ROOT / "scripts/m069_fullval_reliability_dump.py" if unit in "ABCDEF" else ROOT / "p3_selector/deployable_proxy_r019/scripts/label_attach_results_r019.py", "399-403" if unit in "ABCDEF" else "152-166", "DIRECT"),
            ("D_cal_D_audit_role", ROOT / "scripts/m069_common.py", "261-274", "DIRECT"),
            ("risk_constant", ROOT / "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json", "frozen delta-theta table", "DIRECT"),
        ]:
            support_rows.append({"unit": unit, "evidence_item": item, "status": status if path.exists() else "MISSING", "source_path": str(path), "source_location": location, "witness": "existing evidence only"})
    write_csv(OUT / "manuscript_support_inventory.csv", support_rows)

    gaps = [{"unit": u, "field": "official_annotation_id", "path": "official raw annotation -> processed/tiled object back-map", "minimum_nonexecuted_recovery_action": "create and separately audit an immutable raw-object-to-evaluation-object mapping without changing frozen cohorts"} for u in UNITS]
    write_json(OUT / "r033_readiness.json", {
        "status": "ASSET_GAP_R032", "ready_for_r033": False, "fixed_units": list(UNITS),
        "gaps": gaps, "join_failures": [r for r in join_rows if r["status"] != "PASS"],
        "decision": "Do not execute r033 circularity/attribution audit until a separately authorized object-lineage asset closes these gaps.",
    })

    write_json(OUT / "preflight.json", {
        "schema": "r032_preflight_v1", "dispatch_id": "orientbench-c-r032-circularity-asset-preflight-retry-20260814",
        "dispatch_commit_sha": "a9e1b7f278628962db0ecb82de1fda1a93509a73", "started_commit": git("rev-parse", "239fb3e994890226aab55c696d3724270d973d72"),
        "plan_path": str(PLAN.relative_to(ROOT)), "plan_sha256": sha(PLAN), "worker": git("config", "--local", "paper.worker-id"),
        "scientific_computation_performed": False, "training_or_inference_performed": False, "quarantine_content_used": False,
        "fixed_units": list(UNITS), "field_cartesian_rows": len(field_rows), "readiness": "ASSET_GAP_R032",
    })
    ledger = [
        {"step": "T0", "status": "PASS", "action": "identity closure and STARTED committed/pushed before asset reads", "scientific_output": False},
        {"step": "T1", "status": "PASS", "action": "read-only source inventory", "scientific_output": False},
        {"step": "T2", "status": "PASS_WITH_GAPS", "action": "8x12 field matrix; official raw-object ID gap recorded", "scientific_output": False},
        {"step": "T3", "status": "PASS", "action": "schema/key coverage inventory only", "scientific_output": False},
        {"step": "T4", "status": "PASS", "action": "four official annotation manifests and DOTA provenance", "scientific_output": False},
        {"step": "T5", "status": "PASS", "action": "manuscript support locations", "scientific_output": False},
        {"step": "T6", "status": "ASSET_GAP_R032", "action": "r033 not authorized by readiness", "scientific_output": False},
    ]
    write_csv(OUT / "execution_ledger.csv", ledger)

    after = quarantine_rows()
    write_csv(OUT / "legacy_quarantine_after.csv", after, ["relative_path", "bytes", "sha256"])
    if before != after:
        raise RuntimeError("quarantine changed")

    # Provisional manifest lets the same validator run on four temp-copy mutations;
    # targeted structural checks precede manifest verification.
    def make_manifest() -> None:
        rows = []
        for path in sorted(p for p in OUT.rglob("*") if p.is_file() and p.name not in {"artifact_manifest.json", "validation_r032.json"}):
            rows.append({"relative_path": path.relative_to(OUT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
        write_json(OUT / "artifact_manifest.json", {"schema": "r032_artifact_manifest_v1", "files": rows})

    make_manifest()
    mutations = []
    validator = OUT / "validate_r032.py"
    with tempfile.TemporaryDirectory(prefix="r032_mutations_") as temporary:
        for name in ("delete_unit_field", "change_source_sha", "cohort_duplicate", "missing_to_direct"):
            target = Path(temporary) / name
            shutil.copytree(OUT, target)
            if name == "delete_unit_field":
                frame = pd.read_csv(target / "field_availability.csv", dtype=str).iloc[1:]
                frame.to_csv(target / "field_availability.csv", index=False, lineterminator="\n")
            elif name == "change_source_sha":
                frame = pd.read_csv(target / "source_inventory.csv", dtype=str)
                frame.loc[0, "sha256"] = "0" * 64
                frame.to_csv(target / "source_inventory.csv", index=False, lineterminator="\n")
            elif name == "cohort_duplicate":
                frame = pd.read_csv(target / "join_feasibility.csv", dtype=str)
                frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
                frame.to_csv(target / "join_feasibility.csv", index=False, lineterminator="\n")
            else:
                frame = pd.read_csv(target / "field_availability.csv", dtype=str)
                idx = frame.index[frame["status"] == "MISSING"][0]
                frame.loc[idx, "status"] = "DIRECT"
                frame.to_csv(target / "field_availability.csv", index=False, lineterminator="\n")
            proc = subprocess.run(["python", str(validator), "--bundle-dir", str(target), "--quiet"], cwd=ROOT, text=True, capture_output=True)
            mutations.append({"mutation": name, "exit_code": proc.returncode, "rejected": proc.returncode != 0, "diagnostic": (proc.stderr or proc.stdout).strip().splitlines()[-1:]})
            if proc.returncode == 0:
                raise RuntimeError(f"mutation was not rejected: {name}")
    write_json(OUT / "mutation_results.json", {"status": "PASS", "mutations": mutations})
    make_manifest()
    proc = subprocess.run(["python", str(validator), "--bundle-dir", str(OUT), "--output", str(OUT / "validation_r032.json")], cwd=ROOT)
    if proc.returncode:
        raise SystemExit(proc.returncode)
    print("PASS_R032_ASSET_GAP")


if __name__ == "__main__":
    main()

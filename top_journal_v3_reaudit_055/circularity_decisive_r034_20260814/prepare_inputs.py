#!/usr/bin/env python3
"""Prepare immutable derived inputs for r034 from frozen r028/r014/r019 assets."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
OUT = ROOT / "outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814"
INPUT = OUT / "inputs"
R014 = SOURCE_ROOT / "outputs/persistent_artifacts/orientbench_r014"
R019 = SOURCE_ROOT / "outputs/persistent_artifacts/orientbench_r019"
M069 = SOURCE_ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
R032 = ROOT / "reports/r032_circularity_asset_preflight"
UNITS = {
    "A": ("DIOR-R", "PSC"), "B": ("DIOR-R", "Oriented R-CNN"), "C": ("DIOR-R", "RTMDet"),
    "D": ("FAIR1M", "PSC"), "E": ("SODA-A", "PSC"), "F": ("SODA-A", "Oriented R-CNN"),
    "G": ("DOTA-v1.0", "Oriented R-CNN"), "H": ("DOTA-v1.0", "RTMDet-M"),
}
CLASS_COUNTS = {"DIOR-R": 20, "FAIR1M": 37, "SODA-A": 9, "DOTA-v1.0": 15}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def set_sha(values) -> str:
    return hashlib.sha256(("\n".join(sorted(str(x) for x in values)) + "\n").encode()).hexdigest()


def source_paths(unit: str) -> tuple[Path, Path]:
    if unit in "ABCDEF":
        return R014 / f"features/{unit}.parquet", M069 / f"{unit}/manifest.json"
    slug = "orcnn" if unit == "G" else "rtmdet"
    return R019 / f"prelabel/target_features/{slug}.parquet", R019 / "prelabel/image_only_registry.json"


def base_frame(unit: str) -> pd.DataFrame:
    if unit in "ABCDEF":
        frame = pd.read_parquet(ROOT / "audit_bundles/r028/dior/rows.parquet")
        return frame.loc[frame.unit.astype(str).eq(unit)].copy()
    slug = "orcnn" if unit == "G" else "rtmdet"
    return pd.read_parquet(ROOT / f"audit_bundles/r028/dota/matched_{slug}.parquet")


def model_config(unit: str, manifest: Path) -> tuple[str, str, str, str]:
    doc = json.loads(manifest.read_text())
    if unit in "ABCDEF":
        cfg = str(doc.get("config_path", "")); ckpt = str(doc.get("checkpoint_path", "")); cksha = str(doc.get("checkpoint_sha256", ""))
    else:
        slug = "orcnn" if unit == "G" else "rtmdet"
        spec = doc["units"][slug]; cfg = str(spec["config"]); ckpt = str(spec["checkpoint"]); cksha = sha(Path(ckpt))
    cfg_path = Path(cfg)
    return cfg, sha(cfg_path) if cfg_path.is_file() else "", ckpt, cksha


def main() -> None:
    INPUT.mkdir(parents=True, exist_ok=True)
    all_rows = []
    joins = []
    sources = []
    nms_rows = []
    diagnostic_rows = []
    lineage_rows = []
    unit_cluster_universes: dict[str, list[str]] = {}
    official = pd.read_csv(R032 / "official_annotation_inventory.csv", dtype=str)
    official_by = {str(r.dataset): r for r in official.itertuples(index=False)}
    official_key = {"DIOR-R": "DIOR-R", "FAIR1M": "FAIR1M-v1.0", "SODA-A": "SODA-A", "DOTA-v1.0": "DOTA-v1.0"}
    for unit, (dataset, detector) in UNITS.items():
        base = base_frame(unit)
        feature_path, model_manifest = source_paths(unit)
        feat = pd.read_parquet(feature_path, columns=["image_id", "pred_id", "class_id", "detection_score", "log_pred_ar"])
        for frame, label in ((base, "cohort"), (feat, "features")):
            if frame.duplicated(["image_id", "pred_id"]).any():
                raise RuntimeError(f"duplicate {label} key {unit}")
        keys = pd.MultiIndex.from_frame(base[["image_id", "pred_id"]].astype({"image_id": str, "pred_id": int}))
        f = feat.copy(); f["image_id"] = f.image_id.astype(str); f["pred_id"] = f.pred_id.astype(int)
        f = f.set_index(["image_id", "pred_id"], verify_integrity=True)
        selected = f.reindex(keys)
        if selected.isna().any().any():
            raise RuntimeError(f"feature join missing {unit}: {selected.isna().any(axis=1).sum()}")
        if unit in "ABCDEF":
            expected_score = base.raw_confidence.to_numpy(float)
            gt_ar = base.ar.to_numpy(float); e_can = base.e_can.to_numpy(float); risk_norm = base.risk_main.to_numpy(float)
            cluster = base.cluster.astype(str).to_numpy(); gt_id = np.full(len(base), -1, dtype=np.int64)
        else:
            expected_score = base.raw_confidence.to_numpy(float)
            gt_ar = base.ar.to_numpy(float); e_can = base.angle_error.to_numpy(float); risk_norm = base.risk.to_numpy(float)
            cluster = base.mother.astype(str).to_numpy(); gt_id = base.gt_id.to_numpy(np.int64)
        if not np.array_equal(selected.detection_score.to_numpy(float), expected_score):
            raise RuntimeError(f"confidence mismatch {unit}")
        out = pd.DataFrame({
            "unit": unit, "dataset": dataset, "detector": detector,
            "image_id": base.image_id.astype(str).to_numpy(), "pred_id": base.pred_id.to_numpy(np.int64), "gt_id": gt_id,
            "class_id": selected.class_id.to_numpy(np.int64), "cluster": cluster,
            "gt_ar": gt_ar, "log_pred_ar": selected.log_pred_ar.to_numpy(float), "e_can": e_can,
            "risk_norm": risk_norm, "risk_raw": np.clip(e_can / 90.0, 0.0, 1.0),
            "conf": expected_score, "ARonly": -selected.log_pred_ar.to_numpy(float),
            "oracleAR": -np.log(np.maximum(gt_ar, 1.0)), "probe": base.linear_source_frozen.to_numpy(float),
        })
        expected_classes = set(range(CLASS_COUNTS[dataset])); found_classes = set(out.class_id.unique())
        if not found_classes <= expected_classes:
            raise RuntimeError(f"class range {unit}: {sorted(found_classes - expected_classes)}")
        if not np.isfinite(out[["gt_ar", "log_pred_ar", "e_can", "risk_norm", "risk_raw", "conf", "ARonly", "oracleAR", "probe"]]).all().all():
            raise RuntimeError(f"nonfinite derived row {unit}")
        if not out.risk_norm.between(0, 1).all() or not out.risk_raw.between(0, 1).all():
            raise RuntimeError(f"risk range {unit}")
        all_rows.append(out)
        if unit in "ABCDEF":
            universe = pd.read_csv(M069 / f"{unit}/image_universe.csv", dtype=str)
            audit_images = universe.loc[universe.d_cal_daudit_split_flag.eq("D_audit"), "image_id"].astype(str)
            if unit in "EF":
                soda_map = pd.read_csv(R014 / "soda_tile_to_mother_r014.csv", dtype=str).set_index("tile_id").mother_scene_id
                mapped = audit_images.map(soda_map)
                if mapped.isna().any():
                    raise RuntimeError(f"SODA audit cluster mapping missing {unit}")
                unit_cluster_universes[unit] = sorted(set(mapped.astype(str)), key=lambda x: x.encode())
            else:
                unit_cluster_universes[unit] = sorted(set(audit_images), key=lambda x: x.encode())
        else:
            tile_map_frame = pd.read_csv(ROOT / "audit_bundles/r028/dota/tile_to_mother.csv", dtype=str)
            unit_cluster_universes[unit] = sorted(set(tile_map_frame.mother.astype(str)), key=lambda x: x.encode())
        cohort_path = (ROOT / "audit_bundles/r028/dior/rows.parquet") if unit in "ABCDEF" else (ROOT / f"audit_bundles/r028/dota/matched_{'orcnn' if unit == 'G' else 'rtmdet'}.parquet")
        joins.append({
            "unit": unit, "cohort_rows": len(base), "feature_rows": len(feat), "cohort_missing": 0,
            "feature_extras": len(f.index.difference(keys)), "duplicate_cohort_keys": 0, "duplicate_feature_keys": 0,
            "cohort_key_sha256": set_sha(f"{a}\x1f{b}" for a, b in keys), "status": "PASS",
        })
        for role, path in (("cohort", cohort_path), ("features", feature_path), ("model_manifest", model_manifest)):
            sources.append({"unit": unit, "role": role, "absolute_path": str(path), "bytes": path.stat().st_size, "sha256": sha(path), "read_only": True})
        cfg, cfg_sha, ckpt, ckpt_sha = model_config(unit, model_manifest)
        config_text = Path(cfg).read_text(errors="replace") if Path(cfg).is_file() else ""
        nms_lines = [line.strip() for line in config_text.splitlines() if re.search(r"nms|score_thr|max_per_img", line, re.I)]
        nms_rows.append({"unit": unit, "config_path": cfg, "config_sha256": cfg_sha, "checkpoint_path": ckpt, "checkpoint_sha256": ckpt_sha, "nms_excerpt": " || ".join(nms_lines[:30])})
        for eligibility, chosen in (("all-AR", out), ("AR>=2.1", out.loc[out.gt_ar.ge(2.1)])):
            diagnostic_rows.append({
                "unit": unit, "dataset": dataset, "eligibility": eligibility, "rows": len(chosen),
                "clusters": chosen.cluster.nunique(), "classes_present": chosen.class_id.nunique(), "official_class_count": CLASS_COUNTS[dataset],
                "near_square_fraction": float(chosen.gt_ar.lt(2.1).mean()), "gt_ar_q05": float(chosen.gt_ar.quantile(.05)),
                "gt_ar_q50": float(chosen.gt_ar.quantile(.5)), "gt_ar_q95": float(chosen.gt_ar.quantile(.95)),
                "conf_q05": float(chosen.conf.quantile(.05)), "conf_q50": float(chosen.conf.quantile(.5)), "conf_q95": float(chosen.conf.quantile(.95)),
                "conf_hist_entropy_50bin": float(-(lambda p: p[p > 0].dot(np.log(p[p > 0])))(np.histogram(chosen.conf, bins=50, range=(0, 1))[0] / max(len(chosen), 1))),
            })
        inv = official_by[official_key[dataset]]
        lineage_rows.append({
            "unit": unit, "dataset": dataset, "evaluation_rows": len(out), "evaluation_gt_id_available": int((out.gt_id.ge(0)).sum()),
            "official_root": inv.official_root, "official_file_count": int(inv.file_count), "official_manifest_path": inv.manifest_path,
            "official_manifest_sha256": inv.manifest_sha256, "raw_object_id_linked_rows": 0, "coverage": 0.0,
            "status": f"LINEAGE_GAP({unit})", "contradiction": False,
            "reason": "No frozen raw-object-to-processed/tiled-object identifier map; evaluation gt_id is a local post-conversion ordinal and is not promoted to an official object ID.",
            "minimum_recovery": "Separately audit an immutable raw-object-to-evaluation-object map; no recovery executed in r034.",
        })
    rows = pd.concat(all_rows, ignore_index=True)
    if rows.duplicated(["unit", "image_id", "pred_id"]).any():
        raise RuntimeError("derived row-key duplicate")
    rows.to_parquet(INPUT / "matched_rows_enriched.parquet", index=False, compression="zstd")
    if not (unit_cluster_universes["A"] == unit_cluster_universes["B"] == unit_cluster_universes["C"]):
        raise RuntimeError("DIOR D_audit cluster universes differ")
    if unit_cluster_universes["E"] != unit_cluster_universes["F"]:
        raise RuntimeError("SODA D_audit mother universes differ")
    if unit_cluster_universes["G"] != unit_cluster_universes["H"]:
        raise RuntimeError("DOTA mother universes differ")
    dataset_reference = {"DIOR-R": "A", "FAIR1M": "D", "SODA-A": "E", "DOTA-v1.0": "G"}
    cluster_rows = [{"dataset": dataset, "cluster_index": i, "cluster": cluster} for dataset, unit in dataset_reference.items() for i, cluster in enumerate(unit_cluster_universes[unit])]
    pd.DataFrame(cluster_rows).to_csv(INPUT / "cluster_universe.csv", index=False)
    pd.DataFrame(joins).to_csv(INPUT / "join_audit.csv", index=False)
    pd.DataFrame(sources).to_csv(INPUT / "source_inventory.csv", index=False)
    pd.DataFrame(lineage_rows).to_csv(OUT / "lineage_status.csv", index=False)
    pd.DataFrame(diagnostic_rows).to_csv(OUT / "mechanism_diagnostics.csv", index=False)
    pd.DataFrame(nms_rows).to_csv(OUT / "nms_config_inventory.csv", index=False)
    class_rows = []
    for (unit, eligibility, class_id), group in pd.concat([rows.assign(eligibility="all-AR"), rows.loc[rows.gt_ar.ge(2.1)].assign(eligibility="AR>=2.1")]).groupby(["unit", "eligibility", "class_id"]):
        class_rows.append({"unit": unit, "eligibility": eligibility, "class_id": class_id, "rows": len(group), "fraction": len(group) / len(rows.loc[rows.unit.eq(unit) & ((rows.gt_ar.ge(2.1)) if eligibility == "AR>=2.1" else np.ones(len(rows), bool))])})
    pd.DataFrame(class_rows).to_csv(OUT / "class_composition.csv", index=False)
    match_rows = []
    for unit, (dataset, _) in UNITS.items():
        fpath, _ = source_paths(unit); total = len(pd.read_parquet(fpath, columns=["image_id"]))
        matched = len(rows.loc[rows.unit.eq(unit)])
        match_rows.append({"unit": unit, "dataset": dataset, "prediction_rows": total, "frozen_D_audit_matched_rows": matched, "D_audit_matched_fraction_of_predictions": matched / total, "unmatched_handling": "excluded by the frozen classwise IoU>=0.5 one-to-one matched cohort; no rematching in r034"})
    pd.DataFrame(match_rows).to_csv(OUT / "matching_diagnostics.csv", index=False)
    output_files = [INPUT / "matched_rows_enriched.parquet", INPUT / "cluster_universe.csv", INPUT / "join_audit.csv", INPUT / "source_inventory.csv", OUT / "lineage_status.csv", OUT / "mechanism_diagnostics.csv", OUT / "nms_config_inventory.csv", OUT / "class_composition.csv", OUT / "matching_diagnostics.csv"]
    manifest = [{"path": str(p.relative_to(OUT)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in output_files]
    pd.DataFrame(manifest).to_csv(INPUT / "derived_input_manifest.csv", index=False)
    print(json.dumps({"status": "PASS", "rows": len(rows), "units": rows.unit.nunique(), "lineage_gaps": len(lineage_rows)}, sort_keys=True))


if __name__ == "__main__":
    main()

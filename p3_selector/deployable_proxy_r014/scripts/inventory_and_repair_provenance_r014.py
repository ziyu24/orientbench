#!/usr/bin/env python3
"""Exhaustive r014 provenance inventory and official-evaluator parity."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import pickle
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from mmengine.config import Config
from mmrotate.evaluation.functional import eval_rbbox_map


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r014"
REPORTS = ROOT / "p3_selector/deployable_proxy_r014/reports"
M069 = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
OLD = ROOT / "outputs/persistent_artifacts/orientbench_v2_047/tta_preds"
SODA4_ID = ROOT / "outputs/persistent_artifacts/orientbench_v2/SODA-A/4/raw/result_b4.pkl"
GT = {
    "DIOR-R": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl",
    "FAIR1M-v1.0": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl",
    "SODA-A": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl",
}
UNITS = {
    "A": ("DIOR-R/22", "DIOR-R", "rotated_retinanet_psc", RUNTIME / "raw/dior22"),
    "B": ("DIOR-R/3", "DIOR-R", "oriented_rcnn", RUNTIME / "raw/dior3"),
    "C": ("DIOR-R/61", "DIOR-R", "rotated_rtmdet_s", RUNTIME / "raw/dior61"),
    "D": ("FAIR1M-v1.0/24", "FAIR1M-v1.0", "rotated_retinanet_psc", RUNTIME / "raw/fair24"),
    "E": ("SODA-A/23", "SODA-A", "rotated_retinanet_psc", OLD / "SODA-A_23"),
    "F": ("SODA-A/4", "SODA-A", "oriented_rcnn", OLD / "SODA-A_4"),
}
EXPECTED = {"A": 11738, "B": 11738, "C": 11738, "D": 4362, "E": 22994, "F": 22994}
AUTHORITY = {
    "A": (0.5368, 0.3503), "B": (0.6448, 0.4275), "C": (0.6462, 0.4515),
    "D": (0.3462, 0.2422), "E": (0.5991, 0.2735), "F": (0.7295, 0.3805),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def set_sha(values) -> str:
    return hashlib.sha256(("\n".join(sorted(map(str, values))) + "\n").encode()).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def raw_path(unit: str, view: str) -> Path:
    if unit == "F" and view == "identity":
        return SODA4_ID
    return UNITS[unit][3] / f"{view}.pkl"


def load_raw(path: Path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def inventory_raw(unit: str, view: str) -> tuple[dict, list]:
    path = raw_path(unit, view)
    records = load_raw(path)
    ids = [str(row["img_id"]) for row in records]
    predictions = sum(len(row["pred_instances"]["scores"]) for row in records)
    result = {
        "unit": UNITS[unit][0], "unit_key": unit, "dataset": UNITS[unit][1], "view": view,
        "path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path),
        "image_records": len(ids), "unique_images": len(set(ids)), "image_set_sha256": set_sha(ids),
        "prediction_count": predictions, "zero_prediction_images": sum(len(row["pred_instances"]["scores"]) == 0 for row in records),
        "expected_images": EXPECTED[unit],
        "status": "READY" if len(ids) == len(set(ids)) == EXPECTED[unit] else "FAIL_UNIVERSE",
    }
    return result, records


def official(unit: str, records: list) -> dict:
    manifest = json.loads((M069 / unit / "manifest.json").read_text())
    cfg = Config.fromfile(manifest["config_path"])
    metainfo = cfg.get("metainfo")
    if metainfo is None:
        metainfo = cfg.test_dataloader.dataset.get("metainfo")
    if metainfo is None:
        metainfo = cfg.val_dataloader.dataset.get("metainfo")
    if metainfo is None or "classes" not in metainfo:
        raise RuntimeError(f"class metainfo unavailable for {unit}")
    classes = tuple(metainfo["classes"])
    gt_rows = [json.loads(line) for line in GT[UNITS[unit][1]].open() if line.strip()]
    image_ids = sorted({str(row["img_id"]) for row in records} | {str(row["image_id"]) for row in gt_rows})
    image_index = {value: index for index, value in enumerate(image_ids)}
    dets = [[[] for _ in classes] for _ in image_ids]
    for record in records:
        pred = record["pred_instances"]
        boxes = pred["bboxes"].tensor if hasattr(pred["bboxes"], "tensor") else pred["bboxes"]
        boxes = boxes.detach().cpu().numpy(); scores = pred["scores"].detach().cpu().numpy(); labels = pred["labels"].detach().cpu().numpy()
        image = image_index[str(record["img_id"])]
        for box, score, label in zip(boxes, scores, labels):
            dets[image][int(label)].append([*map(float, box), float(score)])
    det_results = [[np.asarray(value, np.float32).reshape(-1, 6) for value in image] for image in dets]
    gt_boxes = [[] for _ in image_ids]; gt_labels = [[] for _ in image_ids]
    class_index = {name: index for index, name in enumerate(classes)}
    for row in gt_rows:
        image = image_index[str(row["image_id"])]
        gt_boxes[image].append([row["obb_cx"], row["obb_cy"], row["obb_w"], row["obb_h"], row["obb_theta"]])
        gt_labels[image].append(class_index[row["class_name"]])
    annotations = [{
        "bboxes": np.asarray(boxes, np.float32).reshape(-1, 5),
        "labels": np.asarray(labels, np.int64),
        "bboxes_ignore": np.empty((0, 5), np.float32), "labels_ignore": np.empty((0,), np.int64),
    } for boxes, labels in zip(gt_boxes, gt_labels)]
    result = {}
    for threshold in (0.5, 0.75):
        mean_ap, _ = eval_rbbox_map(det_results, annotations, iou_thr=threshold, use_07_metric=True,
                                    box_type="rbox", dataset=classes, logger="silent", nproc=38)
        result[f"official_AP{int(threshold * 100)}"] = float(mean_ap)
    result["authority_AP50"] = AUTHORITY[unit][0]; result["authority_AP75"] = AUTHORITY[unit][1]
    result["AP50_abs_diff"] = abs(result["official_AP50"] - AUTHORITY[unit][0])
    result["AP75_abs_diff"] = abs(result["official_AP75"] - AUTHORITY[unit][1])
    result["official_parity"] = "PASS" if max(result["AP50_abs_diff"], result["AP75_abs_diff"]) <= 0.002 else "FAIL"
    return result


def fair_audit(new_views: dict[str, list]) -> list[dict]:
    split = {path.stem for path in (ROOT / "top_journal_v3_reaudit_055/data_prep/FAIR1M_val20/annfiles_dotaformat").glob("*.txt")}
    gt_count = Counter()
    with GT["FAIR1M-v1.0"].open() as handle:
        for line in handle:
            row = json.loads(line); gt_count[str(row["image_id"])] += 1
    old = load_raw(OLD / "FAIR1M-v1.0_24/identity.pkl")
    old_count = {str(row["img_id"]): len(row["pred_instances"]["scores"]) for row in old}
    m069_rows = list(csv.DictReader((M069 / "D/image_universe.csv").open()))
    m069_count = {row["image_id"]: int(row["n_predictions"]) for row in m069_rows}
    new_counts = {}
    for view, records in new_views.items():
        new_counts[view] = {str(row["img_id"]): len(row["pred_instances"]["scores"]) for row in records}
    rows = []
    for image_id in sorted(split):
        rows.append({
            "image_id": image_id, "gt_count": gt_count.get(image_id, 0), "old_r011_n_pred": old_count.get(image_id, "MISSING"),
            "m069_n_pred": m069_count.get(image_id, "MISSING"),
            "r014_identity_n_pred": new_counts["identity"].get(image_id, "MISSING"),
            "r014_hflip_n_pred": new_counts["hflip"].get(image_id, "MISSING"),
            "r014_vflip_n_pred": new_counts["vflip"].get(image_id, "MISSING"),
        })
    return rows


def exhaustive_search() -> list[dict]:
    rows = []
    roots = [ROOT / "outputs/persistent_artifacts", ROOT / "work_dirs", ROOT / "top_journal_v3_reaudit_055"]
    for base in roots:
        for path in base.rglob("*.pkl"):
            lower = str(path).lower()
            if "fair" not in lower or not any(token in lower for token in ("24", "tta", "raw", "result")):
                continue
            try:
                records = load_raw(path)
                if not isinstance(records, list) or not records or "img_id" not in records[0]:
                    continue
                ids = [str(row["img_id"]) for row in records]
                rows.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path),
                             "image_records": len(ids), "unique_images": len(set(ids)), "status": "CANDIDATE"})
            except Exception as error:
                rows.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
                             "sha256": "UNREADABLE", "image_records": "", "unique_images": "", "status": f"UNREADABLE:{type(error).__name__}"})
    return rows


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    inventory, provenance = [], []
    records_by_unit = {}
    for unit in UNITS:
        view_records = {}
        for view in ("identity", "hflip", "vflip"):
            row, records = inventory_raw(unit, view); inventory.append(row); view_records[view] = records
        if len({row["image_set_sha256"] for row in inventory if row["unit_key"] == unit}) != 1:
            raise RuntimeError(f"view universe differs for {unit}")
        parity = official(unit, view_records["identity"])
        manifest = json.loads((M069 / unit / "manifest.json").read_text())
        provenance.append({
            "unit": UNITS[unit][0], "unit_key": unit, "dataset": UNITS[unit][1], "detector": UNITS[unit][2],
            "split": "full-validation", "images": EXPECTED[unit], "identity_predictions": inventory[-3]["prediction_count"],
            "config": manifest["config_path"], "config_sha256": manifest["config_sha256"],
            "checkpoint": manifest["checkpoint_path"], "checkpoint_sha256": manifest["checkpoint_sha256"],
            "gt": str(GT[UNITS[unit][1]].relative_to(ROOT)), "gt_sha256": sha256(GT[UNITS[unit][1]]),
            "threshold_nms": "frozen config", "class_map": "frozen config metainfo", "D_cal_D_audit": "frozen m069 image split",
            **parity, "can_recompute": True,
            "status": "PASS_PROVENANCE_R014" if parity["official_parity"] == "PASS" else "FAIL_PROVENANCE_R014",
        })
        records_by_unit[unit] = view_records
    fair_rows = fair_audit(records_by_unit["D"])
    if len(fair_rows) != 4362 or sum(int(row["gt_count"]) for row in fair_rows) != 78644:
        raise RuntimeError("FAIR frozen universe failed")
    if any(row["r014_identity_n_pred"] == "MISSING" for row in fair_rows):
        raise RuntimeError("FAIR repaired raw still misses image rows")
    if sum(int(row["r014_identity_n_pred"]) for row in fair_rows) != 488194:
        raise RuntimeError("FAIR repaired raw prediction total differs from m069")
    soda_dir = Path("/home/rspip/cqc/data/dataset/SODA-A/dota_format_tiled_ss/val_tiled/images")
    tiles = sorted(path.stem for path in soda_dir.iterdir() if path.is_file())
    mapping = [{"dataset": "SODA-A", "tile_id": tile, "mother_scene_id": tile.split("__", 1)[0],
                "mapping_source": "frozen tile filename", "verified": True} for tile in tiles]
    if len(mapping) != 22994 or any(not row["mother_scene_id"] for row in mapping) or len({row["tile_id"] for row in mapping}) != 22994:
        raise RuntimeError("SODA mother-scene map failed")
    write_csv(REPORTS / "provenance_r014.csv", provenance)
    write_csv(REPORTS / "tta_inventory_r014.csv", inventory)
    write_csv(REPORTS / "fair_universe_join_r014.csv", fair_rows)
    write_csv(RUNTIME / "soda_tile_to_mother_r014.csv", mapping)
    search = exhaustive_search()
    write_csv(RUNTIME / "fair_raw_exhaustive_search_r014.csv", search)
    summary = {
        "status": "PASS_A_R014" if all(row["status"] == "PASS_PROVENANCE_R014" for row in provenance) else "FAIL_PROVENANCE_R014",
        "core_units": len(provenance), "core_pass": sum(row["status"] == "PASS_PROVENANCE_R014" for row in provenance),
        "fair_images": len(fair_rows), "fair_gt": sum(int(row["gt_count"]) for row in fair_rows),
        "fair_predictions": sum(int(row["r014_identity_n_pred"]) for row in fair_rows),
        "soda_tiles": len(mapping), "soda_mothers": len({row["mother_scene_id"] for row in mapping}),
        "exhaustive_candidates": len(search),
    }
    (RUNTIME / "provenance_summary_r014.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

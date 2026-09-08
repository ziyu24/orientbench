"""Bounded r028 evaluation-trace, replay, and blind-material production."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pickle
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch
from mmcv.ops import box_iou_rotated
from mmdet.evaluation.functional import average_precision
from mmrotate.evaluation import eval_rbbox_map


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def array(value) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    return np.asarray(value, dtype=float)


def box_iou(dets: np.ndarray, gts: np.ndarray) -> np.ndarray:
    if not len(dets) or not len(gts):
        return np.zeros((len(dets), len(gts)), dtype=float)
    return box_iou_rotated(torch.from_numpy(dets[:, :5]).float(), torch.from_numpy(gts[:, :5]).float()).numpy()


def trace_image(detections: np.ndarray, ground_truth: np.ndarray, ignored: np.ndarray, threshold: float, image_id: str):
    """Literal single-image trace of MMRotate's tpfp_default semantics."""
    detections = np.asarray(detections, dtype=float).reshape(-1, 6)
    ground_truth = np.asarray(ground_truth, dtype=float).reshape(-1, 5)
    ignored = np.asarray(ignored, dtype=float).reshape(-1, 5)
    all_gt = np.vstack((ground_truth, ignored))
    ignore_flags = np.array([False] * len(ground_truth) + [True] * len(ignored))
    ious = box_iou(detections, all_gt)
    covered = np.zeros(len(all_gt), dtype=bool)
    rows = []
    order = np.argsort(-detections[:, 5])
    for local_rank, pred_index in enumerate(order.tolist()):
        if len(all_gt):
            best = int(ious[pred_index].argmax())
            best_iou = float(ious[pred_index, best])
        else:
            best, best_iou = None, 0.0
        before = bool(covered[best]) if best is not None else False
        if best is not None and best_iou >= threshold and ignore_flags[best]:
            state, tp, fp = "ignored", 0, 0
        elif best is not None and best_iou >= threshold and not before:
            state, tp, fp = "tp", 1, 0
            covered[best] = True
        else:
            state, tp, fp = "fp_duplicate" if best is not None and best_iou >= threshold else "fp_below_threshold", 0, 1
        rows.append({
            "image_id": image_id, "prediction_index": int(pred_index), "local_rank": local_rank,
            "score": float(detections[pred_index, 5]), "best_gt_index": best,
            "best_gt_ignored": bool(ignore_flags[best]) if best is not None else False,
            "best_iou": best_iou, "occupied_before": before, "state": state, "tp": tp, "fp": fp,
            "over_threshold_gt_indices": [int(x) for x in np.flatnonzero(ious[pred_index] >= threshold)],
        })
    return rows, ious


def ap11(tp: np.ndarray, fp: np.ndarray, num_gt: int) -> float:
    """VOC-2007 interpolation, with the evaluator's float32 arithmetic."""
    if num_gt <= 0:
        return 0.0
    tp = np.asarray(tp, dtype=np.float32)
    fp = np.asarray(fp, dtype=np.float32)
    recall = np.cumsum(tp) / num_gt
    precision = np.cumsum(tp) / np.maximum(np.cumsum(tp) + np.cumsum(fp), np.finfo(np.float32).eps)
    return float(average_precision(recall, precision, mode="11points"))


def replay(traces: dict[str, list[dict]], effective_gt: dict[str, int], image_order: list[str]):
    rows = [row for image_id in image_order for row in traces[image_id]]
    scores = np.array([row["score"] for row in rows], dtype=float)
    order = np.argsort(-scores)
    ordered = []
    total_tp = total_fp = 0
    for rank, index in enumerate(order.tolist()):
        row = dict(rows[index])
        total_tp += row["tp"]
        total_fp += row["fp"]
        row.update({"global_rank": rank, "cumulative_tp": total_tp, "cumulative_fp": total_fp})
        ordered.append(row)
    tp = np.array([row["tp"] for row in ordered], dtype=float)
    fp = np.array([row["fp"] for row in ordered], dtype=float)
    return ordered, {"num_gt": int(sum(effective_gt.values())), "num_dets": len(ordered), "tp": int(tp.sum()),
                     "fp": int(fp.sum()), "ignored": int(sum(row["state"] == "ignored" for row in ordered)),
                     "ap11": ap11(tp, fp, int(sum(effective_gt.values())))}


def xml_record(path: Path):
    root = ET.parse(path).getroot()
    width, height = int(root.findtext("Img_SizeWidth")), int(root.findtext("Img_SizeHeight"))
    objects = root.findall("./HRSC_Objects/HRSC_Object")
    difficult = sum(int(item.findtext("difficult", "0")) != 0 for item in objects)
    return {"image_id": path.stem, "width": width, "height": height, "objects_all": len(objects),
            "objects_difficult": difficult, "density": len(objects) / (width * height), "xml_sha256": sha256(path)}


def select_images(dataset: Path, cfg: dict, output: Path):
    test_ids = [line.strip() for line in (dataset / "splits/test.txt").read_text().splitlines() if line.strip()]
    rows = [xml_record(dataset / "annfiles" / f"{image_id}.xml") for image_id in test_ids]
    if len({row["image_id"] for row in rows}) != len(rows):
        raise RuntimeError("duplicate test image ID")
    ordered = sorted(rows, key=lambda row: (-row["density"], int(row["image_id"])))
    high_count = math.ceil(len(ordered) / 4)
    rng = np.random.Generator(np.random.PCG64(cfg["selection"]["seed"]))
    high_indices = rng.choice(high_count, size=cfg["selection"]["per_stratum"], replace=False)
    low_indices = rng.choice(len(ordered) - high_count, size=cfg["selection"]["per_stratum"], replace=False) + high_count
    chosen = set(high_indices.tolist() + low_indices.tolist())
    for rank, row in enumerate(ordered):
        row["density_rank"] = rank
        row["stratum"] = "high_density" if rank < high_count else "other_density"
        row["selected"] = rank in chosen
    selected = [row for row in ordered if row["selected"]]
    if len(selected) != 24 or sum(row["stratum"] == "high_density" for row in selected) != 12:
        raise RuntimeError("fixed stratified selection failed")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ordered[0]))
        writer.writeheader(); writer.writerows(ordered)
    return selected, ordered


def standard_ap(records: list[dict], threshold: float):
    dets, annotations = [], []
    for record in records:
        boxes = array(record["pred_instances"]["bboxes"])
        scores = array(record["pred_instances"]["scores"]).reshape(-1, 1)
        dets.append([np.concatenate((boxes, scores), axis=1)])
        gt = array(record["gt_instances"]["bboxes"]).reshape(-1, 5)
        ignored = array(record["ignored_instances"]["bboxes"]).reshape(-1, 5)
        annotations.append({"bboxes": gt, "labels": np.zeros(len(gt), dtype=np.int64),
                            "bboxes_ignore": ignored, "labels_ignore": np.zeros(len(ignored), dtype=np.int64)})
    result, details = eval_rbbox_map(dets, annotations, iou_thr=threshold, use_07_metric=True,
                                     box_type="rbox", logger="silent", nproc=1)
    return float(result), {"num_gts": int(details[0]["num_gts"]), "num_dets": int(details[0]["num_dets"]),
                           "ap11": float(details[0]["ap"])}


def fixture_trace(name, predictions, regular, ignored, threshold):
    trace, matrix = trace_image(np.asarray(predictions, float), np.asarray(regular, float), np.asarray(ignored, float), threshold, name)
    global_rows, summary = replay({name: trace}, {name: len(regular)}, [name])
    standard, details = standard_ap([{"pred_instances": {"bboxes": np.asarray(predictions, float)[:, :5], "scores": np.asarray(predictions, float)[:, 5]},
                                      "gt_instances": {"bboxes": np.asarray(regular, float)}, "ignored_instances": {"bboxes": np.asarray(ignored, float)}}], threshold)
    return {"iou": matrix.tolist(), "trace": trace, "global_trace": global_rows, "replay": summary,
            "standard_ap11": standard, "standard_details": details, "ap_abs_delta": abs(summary["ap11"] - standard)}


def make_box(center, score=None):
    data = [float(center), 0.0, 10.0, 2.0, 0.0]
    return data if score is None else data + [float(score)]


def counterexamples(output: Path):
    threshold = 0.5
    # Frozen specification from r028: each detection overlaps each GT above threshold in both versions.
    start = fixture_trace("two_target_start", [make_box(1, .9), make_box(0, .8)], [make_box(-.01), make_box(2)], [], threshold)
    moved = fixture_trace("two_target_moved", [make_box(1, .9), make_box(0, .8)], [make_box(.01), make_box(2)], [], threshold)
    start_edges = [[x >= threshold for x in row] for row in start["iou"]]
    moved_edges = [[x >= threshold for x in row] for row in moved["iou"]]
    rotation = math.radians(17)
    def rot(box):
        # Image coordinates are y-down while MMRotate's rbox angle is
        # counter-clockwise in the corresponding y-up convention.
        x, y = box[:2]; out = list(box)
        out[0] = x * math.cos(rotation) + y * math.sin(rotation)
        out[1] = -x * math.sin(rotation) + y * math.cos(rotation)
        out[4] -= rotation
        return out
    rotated = fixture_trace("two_target_rotated", [rot(make_box(1, .9)), rot(make_box(0, .8))], [rot(make_box(-.01)), rot(make_box(2))], [], threshold)
    single = fixture_trace("single", [make_box(.01, .9)], [make_box(0)], [], threshold)
    # A deterministic equal-IoU tie changes the selected physical ID when GT order is exchanged, but TP/FP stays unchanged.
    tie_a = fixture_trace("tie_a", [make_box(0, .9)], [make_box(-1), make_box(1)], [], threshold)
    tie_b = fixture_trace("tie_b", [make_box(0, .9)], [make_box(1), make_box(-1)], [], threshold)
    empty = fixture_trace("empty", [make_box(0, .9)], [], [], threshold)
    duplicate = fixture_trace("duplicate", [make_box(0, .9), make_box(0, .8)], [make_box(0)], [], threshold)
    ignored = fixture_trace("ignored", [make_box(0, .9)], [], [make_box(0)], threshold)
    axial = fixture_trace("axial", [make_box(0, .9)], [[0, 0, 10, 2, math.pi]], [], threshold)
    payload = {"threshold": threshold, "single": single, "two_target_start": start, "two_target_moved": moved,
               "two_target_rotated": rotated, "tie_a": tie_a, "tie_b": tie_b, "empty": empty,
               "duplicate": duplicate, "ignored": ignored, "axial": axial,
               "checks": {
                   "all_threshold_edges_unchanged": start_edges == moved_edges,
                   "two_target_tp_fp_changed": [x["state"] for x in start["trace"]] != [x["state"] for x in moved["trace"]],
                   "two_target_ap_changed": start["replay"]["ap11"] != moved["replay"]["ap11"],
                   "rotation_equivalent": np.allclose(start["iou"], rotated["iou"], atol=1e-6) and [x["state"] for x in start["trace"]] == [x["state"] for x in rotated["trace"]],
                   # Both argmax indices are zero: exchanging the GT input
                   # order changes its physical identity from left to right.
                   "tie_id_changed_ap_unchanged": tie_a["trace"][0]["best_gt_index"] == 0 and tie_b["trace"][0]["best_gt_index"] == 0 and tie_a["replay"] == tie_b["replay"],
                   "all_fixture_replays_match_standard": all(item["ap_abs_delta"] <= 1e-8 for item in [single, start, moved, rotated, tie_a, tie_b, empty, duplicate, ignored, axial]),
               }}
    output.write_text(json.dumps(payload, indent=2) + "\n")
    if not all(payload["checks"].values()):
        raise RuntimeError("counterexample semantic check failed")


def blind_materials(dataset: Path, selected: list[dict], output: Path):
    rng = np.random.Generator(np.random.PCG64(28028))
    identifiers = [f"HRSC-BLIND-{number:03d}" for number in rng.permutation(np.arange(1, 25)).tolist()]
    mapping = [{"display_id": display_id, "image_id": row["image_id"], "image_sha256": sha256(dataset / "images" / f"{row['image_id']}.bmp")}
               for display_id, row in zip(identifiers, selected)]
    output.mkdir(parents=True, exist_ok=False)
    instructions = """# HRSC ship OBB independent blind annotation\n\nIndependently inspect the entire image and annotate every visible ship. Do not use any model output, reference boxes, object counts, or other annotators. Record one OBB per row as center-x, center-y, width, height, and le90 angle in radians; use `difficult` for severely occluded, truncated, or indeterminate ships and explain uncertainty in `note`. Record elapsed seconds for the full image.\n"""
    template = "display_id,cx,cy,width,height,theta_le90_rad,difficult,uncertain,note,elapsed_seconds\n"
    for annotator in ("annotator_1", "annotator_2", "annotator_3"):
        package = output / annotator
        images = package / "images"
        images.mkdir(parents=True)
        (package / "INSTRUCTIONS.md").write_text(instructions)
        (package / "annotations_template.csv").write_text(template)
        for item in mapping:
            (images / f"{item['display_id']}.bmp").symlink_to(dataset / "images" / f"{item['image_id']}.bmp")
    check = {"packages": [], "forbidden_terms": ["official", "prediction", "density", "gt_instances", "score", "oriented_rcnn", "rtmdet"]}
    for package in sorted(output.iterdir()):
        files = sorted(path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file() or path.is_symlink())
        image_files = sorted(path.name for path in (package / "images").iterdir())
        text = (package / "INSTRUCTIONS.md").read_text().lower() + "\n" + (package / "annotations_template.csv").read_text().lower()
        check["packages"].append({"package": package.name, "image_count": len(image_files), "files": files,
                                  "forbidden_term_hits": [term for term in check["forbidden_terms"] if term in text]})
    (output.parent / "blind_materials_check.json").write_text(json.dumps(check, indent=2) + "\n")
    (output.parent / "internal_display_mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")
    if any(row["image_count"] != 24 or row["forbidden_term_hits"] for row in check["packages"]):
        raise RuntimeError("blind-material check failed")


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); root, out = args.root.resolve(), args.out.resolve()
    cfg = json.loads((root / "configs/r028/protocol.json").read_text()); dataset = Path(cfg["dataset_root"])
    prediction_root = Path(cfg["prediction_root"])
    if not prediction_root.is_absolute():
        prediction_root = root / prediction_root
    out.mkdir(parents=True, exist_ok=False)
    selected, population = select_images(dataset, cfg, out / "selection_population.csv")
    (out / "selection_manifest.json").write_text(json.dumps({"protocol": cfg["selection"], "selected": selected}, indent=2) + "\n")
    counterexamples(out / "counterexamples.json")
    selected_ids = [row["image_id"] for row in selected]
    all_summaries, raw = {}, {}
    for model in cfg["models"]:
        path = prediction_root / model / cfg["prediction_label"] / "predictions.pkl"
        records = {str(record["img_id"]): record for record in pickle.load(path.open("rb"))}
        if set(selected_ids) - set(records):
            raise RuntimeError(f"missing selected raw predictions for {model}")
        chosen = [records[image_id] for image_id in selected_ids]
        raw[model] = {image_id: {"pred_boxes": array(records[image_id]["pred_instances"]["bboxes"]).tolist(),
                                 "scores": array(records[image_id]["pred_instances"]["scores"]).tolist(),
                                 "gt_boxes": array(records[image_id]["gt_instances"]["bboxes"]).tolist(),
                                 "ignore_boxes": array(records[image_id]["ignored_instances"]["bboxes"]).tolist()}
                      for image_id in selected_ids}
        all_summaries[model] = {"prediction_path": str(path), "prediction_sha256": sha256(path), "per_threshold": {}}
        for label, spec in (("ap50", cfg["evaluation"]["primary"]), ("ap75", cfg["evaluation"]["auxiliary"])):
            threshold = spec["iou_threshold"]
            traces, effective = {}, {}
            for image_id, record in zip(selected_ids, chosen):
                gt, ignored = array(record["gt_instances"]["bboxes"]), array(record["ignored_instances"]["bboxes"])
                expected = next(row for row in selected if row["image_id"] == image_id)["objects_all"]
                if len(gt) + len(ignored) != expected:
                    raise RuntimeError(f"XML/prediction GT count mismatch: {image_id}")
                predictions = np.concatenate((array(record["pred_instances"]["bboxes"]), array(record["pred_instances"]["scores"]).reshape(-1, 1)), axis=1)
                traces[image_id], _ = trace_image(predictions, gt, ignored, threshold, image_id)
                effective[image_id] = len(gt)
            global_rows, replay_summary = replay(traces, effective, selected_ids)
            standard, standard_details = standard_ap(chosen, threshold)
            all_summaries[model]["per_threshold"][label] = {"threshold": threshold, "replay": replay_summary,
                "standard": {"ap11": standard, **standard_details}, "ap_abs_delta": abs(replay_summary["ap11"] - standard),
                "prefix_rows": len(global_rows), "traces": traces, "global_prefixes": global_rows}
    (out / "raw_selected_predictions.json").write_text(json.dumps(raw) + "\n")
    (out / "ap_replay.json").write_text(json.dumps(all_summaries, indent=2) + "\n")
    blind_materials(dataset, selected, out / "blind_packages")
    average_counterexample = fixture_trace("image_1", [make_box(0, .9)], [make_box(0)], [], .5)
    average_counterexample_b = fixture_trace("image_2", [make_box(0, .8)], [], [], .5)
    global_ap = ap11(np.array([1., 0.]), np.array([0., 1.]), 1)
    mean_image_ap = (average_counterexample["replay"]["ap11"] + average_counterexample_b["replay"]["ap11"]) / 2
    summary = {"status": "TECHNICAL_VALIDATION_COMPLETE_HUMAN_RELABEL_NOT_EXECUTED", "selected_images": len(selected),
               "selection_population": len(population),
               "models": {model: {label: {"replay_ap11": data["replay"]["ap11"],
                                             "standard_ap11": data["standard"]["ap11"],
                                             "ap_abs_delta": data["ap_abs_delta"]}
                                  for label, data in item["per_threshold"].items()}
                          for model, item in all_summaries.items()},
               "counterexample": json.loads((out / "counterexamples.json").read_text())["checks"],
               "average_image_ap_counterexample": {"mean_image_ap": mean_image_ap, "global_ap": global_ap, "different": mean_image_ap != global_ap},
               "limitations": ["No human relabeling or natural-label-disagreement effect was measured.", "Fixed-24 unweighted results are not population inference or a model-winner certificate.", "Prefix vectors replay fixed-label AP exactly but do not establish unbiased AP, AP-difference, confidence interval, optional-stopping, or active-selection guarantees."]}
    if not all(value <= 1e-8 for model in all_summaries.values() for value in [entry["ap_abs_delta"] for entry in model["per_threshold"].values()]):
        raise RuntimeError("AP replay disagrees with unmodified standard evaluator")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()

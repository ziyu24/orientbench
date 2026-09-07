"""Re-evaluate the two existing r017 fits; no downloads, optimizer, or training."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orientbench.r017.measurement import weighted_log_loss
from orientbench.r017.run_pilot import _local, _normalise
from orientbench.r018.metrics import invert_rotated_prediction, measure, rasterize_direct, summarise


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 << 20):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    root, out = args.project_root.resolve(), args.out.resolve()
    if not out.is_relative_to(root / "runs" / "r018"):
        raise ValueError("new artifacts must stay within this project's runs/r018")
    out.mkdir(parents=True, exist_ok=True)
    protocol = read(root / "configs/r018/protocol.json")
    manifest_path = root / "configs/r017/data_manifest.json"
    if digest(manifest_path) != protocol["data_manifest_sha256"]:
        raise ValueError("frozen r017 cohort changed")
    manifest = read(manifest_path)
    prior = root / "runs/r017/artifacts"
    pi = read(prior / "training_loss_definition.json")["foreground_fraction"]
    if abs(pi - protocol["foreground_fraction"]) > 1e-14:
        raise ValueError("actual training weights changed")
    if digest(prior / "evaluation_rows.json") != protocol["original_rows_sha256"]:
        raise ValueError("original r017 result table changed")
    checkpoints = {s: prior / "checkpoints" / f"seed{s}_epoch30.pt" for s in protocol["existing_seeds"]}
    bindings = {"manifest": digest(manifest_path), "original_rows": digest(prior / "evaluation_rows.json"),
                "checkpoints": {}, "cache": {}, "labels": {}}
    for seed, path in checkpoints.items():
        bindings["checkpoints"][seed] = digest(path)
        if bindings["checkpoints"][seed] != protocol["checkpoint_sha256"][str(seed)]:
            raise ValueError("existing final checkpoint changed")

    # Establish actual map identity and quantify the already-observed rasterization deviation.
    import rasterio
    labels = {entry["tile"]: entry for entry in manifest["labels"]}
    images = {}
    for entry in manifest["images"]:
        images.setdefault(entry["tile"], []).append(entry)
    direct, label_rows = {}, []
    for split, tiles in (("train", manifest["training_tiles"]), ("calibration", manifest["calibration_tiles"])):
        for tile in tiles:
            x0, y0 = map(int, tile.split("_"))
            expected = (.5, 0, x0, 0, -.5, y0 + 450)
            for entry in images[tile]:
                with rasterio.open(_local(args.dataset_root, entry["key"])) as ds:
                    if ds.crs.to_epsg() != 32616 or (ds.width, ds.height, ds.count) != (900, 900, 4):
                        raise ValueError(f"unexpected raw grid for {tile}")
                    if not np.allclose(tuple(ds.transform)[:6], expected, rtol=0, atol=1e-8):
                        raise ValueError(f"raw image/ground identity mismatch for {tile}")
            path = _local(args.dataset_root, labels[tile]["key"])
            target = rasterize_direct(read(path), expected, "EPSG:32616")
            cache_path = prior / "cache" / split / f"{tile}.npz"
            bindings["labels"][tile] = digest(path)
            bindings["cache"][tile] = digest(cache_path)
            with np.load(cache_path) as cached:
                valid, old = cached["valid"], cached["label"]
                if old.shape != (448, 448) or valid.shape != old.shape or not valid.any():
                    raise ValueError("invalid existing target support")
                mismatch = int(((old != target) & valid).sum())
                label_rows.append({"split": split, "tile": tile, "valid_pixels": int(valid.sum()),
                                   "mismatch_pixels": mismatch, "mismatch_fraction": mismatch / int(valid.sum()),
                                   "cached_foreground": int((old & valid).sum()), "direct_foreground": int((target & valid).sum())})
            if split == "calibration":
                direct[tile] = target
    write(out / "label_grid_differences.json", label_rows)
    write(out / "input_bindings.json", bindings)

    import torch
    from torchvision.models.segmentation import fcn_resnet50
    old_rows = {(r["seed"], r["tile"]): r for r in read(prior / "evaluation_rows.json")}
    rows = {"actual_cached_labels": [], "direct448_label_sensitivity": []}
    replay = []
    started = time.monotonic()
    seconds_limit = protocol["gpu_hours_total"] * 3600
    saved_bytes = 0
    for seed, checkpoint_path in checkpoints.items():
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        if checkpoint["seed"] != seed or checkpoint["epoch"] != 30:
            raise ValueError("wrong checkpoint metadata")
        model = fcn_resnet50(weights=None, weights_backbone=None, num_classes=1, aux_loss=False)
        model.load_state_dict(checkpoint["model"], strict=True)
        model.to(args.device).eval()
        with torch.inference_mode():
            for tile in manifest["calibration_tiles"]:
                if time.monotonic() - started > seconds_limit:
                    raise RuntimeError("fixed evaluation time budget exhausted; keep partial artifacts")
                with np.load(prior / "cache/calibration" / f"{tile}.npz") as cached:
                    x = torch.from_numpy(cached["image"].astype(np.float32)).to(args.device)
                    target, valid = cached["label"], cached["valid"]
                p = torch.sigmoid(model(_normalise(x))["out"][:, 0]).cpu().numpy()
                aligned = []
                for view in (0, 1):
                    rotated_input = torch.rot90(x[view:view + 1], 1, (-2, -1))
                    q = torch.sigmoid(model(_normalise(rotated_input))["out"][:, 0]).cpu().numpy()
                    aligned.append(invert_rotated_prediction(q))
                aligned = np.stack(aligned)
                if p.shape != (4, 448, 448) or aligned.shape != (2, 448, 448):
                    raise ValueError("unexpected full-map prediction shape")
                prediction_path = out / "predictions" / f"seed{seed}_{tile}.npz"
                prediction_path.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(prediction_path, base=p, aligned_rotation=aligned)
                saved_bytes += prediction_path.stat().st_size
                if saved_bytes > protocol["prediction_bytes_limit"]:
                    raise RuntimeError("prediction artifact budget exceeded")
                measured = measure(p, aligned, target, valid, pi)
                rows["actual_cached_labels"].append({"seed": seed, "tile": tile, **measured})
                rows["direct448_label_sensitivity"].append({"seed": seed, "tile": tile,
                    **measure(p, aligned, direct[tile], valid, pi)})
                # Reproduce the old error only as a diagnostic, never as the corrected TTA.
                reference = old_rows[seed, tile]
                keys = ("primary", "delta_a", "delta_b", "loss_a", "loss_b", "loss_u", "loss_v", "loss_au", "loss_av", "loss_bv", "loss_bu")
                drift = max(abs(measured[k] - reference[k]) for k in keys)
                broken = [weighted_log_loss((p[i] + np.broadcast_to(aligned[i, 0], target.shape)) / 2,
                                            target, valid, pi) for i in (0, 1)]
                replay.append({"seed": seed, "tile": tile, "unaffected_loss_max_abs_difference": drift,
                               "legacy_tta_max_abs_difference": max(abs(broken[i] - reference[f"loss_{name}_tta"])
                                                                     for i, name in enumerate(("a", "b")))})
        del model, checkpoint
        if str(args.device).startswith("cuda"):
            torch.cuda.empty_cache()
    for name, values in rows.items():
        write(out / f"{name}_rows.json", values)
    summary = {name: summarise(values, manifest["calibration_tiles"]) for name, values in rows.items()}
    summary["replay"] = {"max_unaffected_difference": max(x["unaffected_loss_max_abs_difference"] for x in replay),
                         "max_legacy_tta_difference": max(x["legacy_tta_max_abs_difference"] for x in replay),
                         "tolerance": protocol["replay_tolerance"]}
    summary["replay"]["within_tolerance"] = max(summary["replay"]["max_unaffected_difference"],
                                                summary["replay"]["max_legacy_tta_difference"]) <= protocol["replay_tolerance"]
    summary["label_scope"] = "Same already-trained weights and fixed actual training class weights; direct448 is evaluation sensitivity, not recovery of the original training protocol."
    summary["elapsed_inference_seconds"] = time.monotonic() - started
    summary["saved_prediction_bytes"] = saved_bytes
    write(out / "replay_rows.json", replay)
    write(out / "summary.json", summary)
    print(json.dumps({name: value["metric_block_equal"] for name, value in summary.items()
                      if isinstance(value, dict) and "metric_block_equal" in value}), flush=True)


if __name__ == "__main__":
    main()

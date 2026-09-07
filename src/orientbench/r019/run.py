"""Fit four global translations on training tiles; evaluate once on existing maps."""
from datetime import datetime, timezone
import argparse
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orientbench.r017.measurement import weighted_log_loss
from orientbench.r017.run_pilot import _local, _normalise
from orientbench.r018.evaluate import digest, read, write
from orientbench.r018.metrics import measure, rasterize_direct, summarise
from orientbench.r019.registration import check_support, loss_surface, paired_change, select_shift, shifted_core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    root, out = args.project_root.resolve(), args.out.resolve()
    if not out.is_relative_to(root / "runs/r019"):
        raise ValueError("artifacts must stay in this project's runs/r019")
    out.mkdir(parents=True, exist_ok=False)
    protocol_path = root / "configs/r019/protocol.json"
    cfg = read(protocol_path)
    prior, evaluation = root / "runs/r017/artifacts", root / "runs/r018/artifacts"
    manifest_path = root / "configs/r017/data_manifest.json"
    if digest(manifest_path) != cfg["data_manifest_sha256"]:
        raise ValueError("frozen cohort changed")
    manifest = read(manifest_path)
    train, calibration = manifest["training_tiles"], manifest["calibration_tiles"]
    if len(train) != 256 or len(calibration) != 128 or set(train) & set(calibration):
        raise ValueError("frozen train/calibration split changed")
    review = read(root / "doc/R018_B_REVIEW_20260907.json")
    if digest(evaluation / "input_bindings.json") != review["source_hashes"]["input_bindings.json"]:
        raise ValueError("r018 input bindings changed")
    bindings = read(evaluation / "input_bindings.json")
    seed, margin, pi = cfg["existing_seed"], cfg["margin_pixels"], cfg["foreground_fraction"]
    checkpoint_path = prior / "checkpoints" / f"seed{seed}_epoch30.pt"
    if digest(checkpoint_path) != cfg["checkpoint_sha256"]:
        raise ValueError("existing checkpoint changed")
    if abs(read(prior / "training_loss_definition.json")["foreground_fraction"] - pi) > 1e-14:
        raise ValueError("actual training weights changed")
    evidence = {"protocol_sha256": digest(protocol_path), "manifest_sha256": digest(manifest_path),
                "checkpoint_sha256": digest(checkpoint_path), "train_cache": {},
                "train_predictions": {}, "calibration_predictions": {}, "calibration_cache": {}, "labels": {}}
    started = time.monotonic()

    def budget():
        if time.monotonic() - started > cfg["wall_hours_total"] * 3600:
            raise RuntimeError("fixed total budget exhausted; preserve partial artifacts")

    def cached(split, tile, load_image=True):
        path = prior / "cache" / split / f"{tile}.npz"
        if digest(path) != bindings["cache"][tile]:
            raise ValueError(f"existing cache changed: {tile}")
        evidence[f"{split}_cache"][tile] = bindings["cache"][tile]
        with np.load(path) as z:
            image, y, valid = z["image"] if load_image else None, z["label"], z["valid"]
        check_support(y, valid, 448)
        if load_image and image.shape != (4, 3, 448, 448):
            raise ValueError("existing four-view input changed")
        return image, y, valid

    # No calibration labels or probabilities are opened before shifts are saved.
    import torch
    from torchvision.models.segmentation import fcn_resnet50
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint["seed"] != seed or checkpoint["epoch"] != 30:
        raise ValueError("wrong checkpoint metadata")
    model = fcn_resnet50(weights=None, weights_backbone=None, num_classes=1, aux_loss=False)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.to(args.device).eval()
    prediction_dir = out / "train_predictions"
    prediction_dir.mkdir()
    write(out / "input_bindings.json", evidence)
    saved_bytes, inference_seconds = 0, 0.
    with torch.inference_mode():
        for index, tile in enumerate(train):
            budget()
            image, _, _ = cached("train", tile)
            tick = time.monotonic()
            x = torch.from_numpy(image.astype(np.float32)).to(args.device)
            p = torch.sigmoid(model(_normalise(x))["out"][:, 0]).cpu().numpy()
            inference_seconds += time.monotonic() - tick
            if p.shape != (4, 448, 448) or not np.isfinite(p).all():
                raise ValueError("unexpected training prediction")
            path = prediction_dir / f"{tile}.npz"
            np.savez_compressed(path, base=p)
            evidence["train_predictions"][tile] = digest(path)
            saved_bytes += path.stat().st_size
            if inference_seconds > cfg["gpu_hours_total"] * 3600 or saved_bytes > cfg["prediction_bytes_limit"]:
                raise RuntimeError("fixed inference/artifact budget exhausted")
            if (index + 1) % 32 == 0:
                print(f"Training prediction tiles: {index + 1}/256", flush=True)
    del model, checkpoint, x
    if str(args.device).startswith("cuda"):
        torch.cuda.empty_cache()

    surfaces = np.zeros((4, 2 * margin + 1, 2 * margin + 1), dtype=np.float64)
    for tile in train:
        budget()
        _, y, valid = cached("train", tile, load_image=False)
        with np.load(prediction_dir / f"{tile}.npz") as z:
            p = z["base"]
        for view in range(4):
            surfaces[view] += loss_surface(p[view], y, valid, pi, margin) / len(train)
    shifts = [select_shift(surface, margin) for surface in surfaces]
    # Direct BCE of all selected/zero shifts verifies the FFT on actual training data.
    direct = np.zeros((4, 2))
    for tile in train:
        budget()
        _, y, valid = cached("train", tile, load_image=False)
        yc, vc = shifted_core(y, 0, 0, margin), shifted_core(valid, 0, 0, margin)
        with np.load(prediction_dir / f"{tile}.npz") as z:
            p = z["base"]
            for view, shift in enumerate(shifts):
                for j, (dy, dx) in enumerate(((0, 0), (shift["dy"], shift["dx"]))):
                    direct[view, j] += weighted_log_loss(shifted_core(p[view], dy, dx, margin), yc, vc, pi) / len(train)
    expected = np.array([[s["train_loss_zero"], s["train_loss_selected"]] for s in shifts])
    fft_error = float(np.max(np.abs(direct - expected)))
    if fft_error > 1e-10:
        raise ValueError(f"actual training FFT/direct mismatch: {fft_error}")
    np.savez_compressed(out / "training_loss_surfaces.npz", surfaces=surfaces, direct_selected_and_zero=direct)
    write(out / "frozen_shifts.json", {"frozen_utc": datetime.now(timezone.utc).isoformat(),
        "fit_split": "train only", "views": cfg["view_order"], "shifts": shifts,
        "fft_direct_max_abs_difference": fft_error, "training_tiles": len(train),
        "convention": "q[y,x] = p[y+dy,x+dx]; targets fixed", "input_evidence": evidence})

    prediction_hashes = {entry["file"]: entry["sha256"] for entry in review["prediction_files"]}
    labels = {entry["tile"]: entry for entry in manifest["labels"]}
    analyses = {label: {arm: [] for arm in ("full448", "zero_core", "aligned_core", "paired_change")}
                for label in ("actual_cached_labels", "direct448_label_sensitivity")}
    previous_rows = {}
    for label in analyses:
        path = evaluation / f"{label}_rows.json"
        if digest(path) != review["source_hashes"][path.name]:
            raise ValueError("B-audited r018 row table changed")
        previous_rows[label] = {r["tile"]: r for r in read(path) if r["seed"] == seed}
    replay_error = 0.
    for tile in calibration:
        budget()
        _, y, valid = cached("calibration", tile, load_image=False)
        path = evaluation / "predictions" / f"seed{seed}_{tile}.npz"
        if digest(path) != prediction_hashes[path.name]:
            raise ValueError("B-audited calibration prediction changed")
        evidence["calibration_predictions"][tile] = prediction_hashes[path.name]
        with np.load(path) as z:
            p, rotations = z["base"], z["aligned_rotation"]
        if p.shape != (4, 448, 448) or rotations.shape != (2, 448, 448):
            raise ValueError("full map shapes changed")
        label_path = _local(args.dataset_root, labels[tile]["key"])
        if digest(label_path) != bindings["labels"][tile]:
            raise ValueError("original calibration label changed")
        evidence["labels"][tile] = bindings["labels"][tile]
        x0, y0 = map(int, tile.split("_"))
        direct_y = rasterize_direct(read(label_path), (.5, 0, x0, 0, -.5, y0 + 450), "EPSG:32616")
        shifted_p = np.stack([shifted_core(p[i], s["dy"], s["dx"], margin) for i, s in enumerate(shifts)])
        shifted_tta = np.stack([shifted_core(rotations[i], s["dy"], s["dx"], margin)
                                for i, s in enumerate(shifts[:2])])
        for label, target in (("actual_cached_labels", y), ("direct448_label_sensitivity", direct_y)):
            core_y, core_v = shifted_core(target, 0, 0, margin), shifted_core(valid, 0, 0, margin)
            full = measure(p, rotations, target, valid, pi)
            reference = previous_rows[label][tile]
            replay_error = max(replay_error, max(abs(value - reference[key]) for key, value in full.items()))
            if replay_error > 1e-10:
                raise ValueError("full448 replay differs from B-audited r018 metrics")
            zero = measure(shifted_core(p, 0, 0, margin), shifted_core(rotations, 0, 0, margin), core_y, core_v, pi)
            aligned = measure(shifted_p, shifted_tta, core_y, core_v, pi)
            for arm, values in (("full448", full), ("zero_core", zero), ("aligned_core", aligned),
                                ("paired_change", paired_change(zero, aligned))):
                analyses[label][arm].append({"seed": seed, "tile": tile, **values})
    summary = {}
    for label, arms in analyses.items():
        summary[label] = {}
        for arm, rows in arms.items():
            write(out / f"{label}_{arm}_rows.json", rows)
            value = summarise(rows, calibration, seeds=(seed,))
            value["interval_scope"] = ("Post-hoc one-seed spatial sensitivity, no fresh confirmation. "
                "For paired_change primary is D=I_zero_core-I_aligned_core; other arms primary is I. "
                "D on actual labels is the r019 main contrast; all other intervals are descriptive.")
            summary[label][arm] = value
    summary["resources"] = {"inference_seconds": inference_seconds, "wall_seconds": time.monotonic() - started,
                            "prediction_bytes": saved_bytes, "neural_network_fits": 0, "new_forward_images": 1024}
    summary["shifts"] = shifts
    summary["full448_replay_max_abs_difference"] = replay_error
    summary["scope"] = "Global translation of frozen model probabilities; not physical registration identification, RPC correction, PSF or new information proof."
    write(out / "input_bindings.json", evidence)
    write(out / "summary.json", summary)
    print(summary["actual_cached_labels"]["paired_change"]["metric_block_equal"], flush=True)


if __name__ == "__main__":
    main()

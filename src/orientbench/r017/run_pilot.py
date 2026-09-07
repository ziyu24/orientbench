"""Bounded end-to-end r017 acquisition, fitting, and blinded evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orientbench.r017.measurement import crossed_comparison, weighted_log_loss


ROOT_URL = "https://spacenet-dataset.s3.amazonaws.com/"
VIEWS = ("1030010003472200", "103001000392F600", "10300100036D5200", "1030010003315300")


def _json(path: Path):
    return json.loads(path.read_text())


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True))


def _local(root: Path, key: str) -> Path:
    prefix = "spacenet/SN4_buildings/train/AOI_6_Atlanta/"
    if not key.startswith(prefix):
        raise ValueError(f"unexpected SpaceNet key: {key}")
    return root / "SpaceNet4" / "train" / key[len(prefix):]


def acquire(items: list[dict], root: Path, ledger: Path, limit: int) -> dict:
    """Fetch exactly manifest items, with content-length and total byte bounds."""
    records = _json(ledger) if ledger.exists() else []
    received = sum(r.get("received_bytes", 0) for r in records)
    by_key = {r["key"]: r for r in records if r.get("status") == "complete"}
    for item in items:
        key, expected = item["key"], int(item["bytes"])
        destination = _local(root, key)
        if destination.is_file() and destination.stat().st_size == expected:
            digest = hashlib.sha256(destination.read_bytes()).hexdigest()
            by_key.setdefault(key, {"key": key, "expected_bytes": expected, "received_bytes": 0,
                                    "status": "reused", "path": str(destination), "sha256": digest})
            continue
        if received + expected > limit:
            raise RuntimeError(f"download budget would be exceeded before {key}")
        partial = destination.with_suffix(destination.suffix + ".part")
        if partial.exists():
            partial.unlink()
        destination.parent.mkdir(parents=True, exist_ok=True)
        record = {"key": key, "expected_bytes": expected, "received_bytes": 0, "status": "started",
                  "path": str(destination)}
        records.append(record)
        _write(ledger, records)
        try:
            request = urllib.request.Request(ROOT_URL + urllib.parse.quote(key, safe="/"),
                                             headers={"User-Agent": "orientbench-r017/1"})
            with urllib.request.urlopen(request, timeout=90) as response, partial.open("wb") as out:
                header = response.headers.get("Content-Length")
                if header is not None and int(header) != expected:
                    raise RuntimeError(f"content-length mismatch for {key}")
                while chunk := response.read(1 << 20):
                    received += len(chunk)
                    record["received_bytes"] += len(chunk)
                    if received > limit or record["received_bytes"] > expected:
                        raise RuntimeError("download budget or expected size exceeded")
                    out.write(chunk)
            if record["received_bytes"] != expected:
                raise RuntimeError(f"short download for {key}")
            os.replace(partial, destination)
            record.update(status="complete", sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
        except Exception as exc:
            record.update(status="failed", error=str(exc))
            attempts = sum(r.get("key") == key and r.get("status") == "failed" for r in records)
            if attempts < 4:
                _write(ledger, records)
                time.sleep(2 ** attempts)
                return acquire(items, root, ledger, limit)
            raise
        finally:
            _write(ledger, records)
        by_key[key] = record
    return {"new_received_bytes": received, "records": records, "complete_items": len(by_key)}


def _read_tile(tile: str, image_keys: dict, label_key: str, root: Path):
    import rasterio
    from rasterio.features import rasterize
    from shapely.geometry import shape
    import torch
    import torch.nn.functional as F

    arrays, meta, valid = [], None, None
    for view in VIEWS:
        path = _local(root, image_keys[view])
        with rasterio.open(path) as ds:
            if ds.count < 3 or ds.width != 900 or ds.height != 900:
                raise ValueError(f"unexpected image shape: {path}")
            current = (str(ds.crs), tuple(ds.transform), ds.width, ds.height)
            if meta is None:
                meta = current
            elif current != meta:
                raise ValueError(f"view grid mismatch: {tile}, {view}")
            raw = ds.read((1, 2, 3)).astype(np.float32)
            supported = np.all(np.isfinite(raw), axis=0) & np.all(ds.read_masks((1, 2, 3)) > 0, axis=0)
            if ds.nodata is not None:
                supported &= ~np.any(raw == ds.nodata, axis=0)
            valid = supported if valid is None else valid & supported
            arrays.append(raw)
            transform, crs = ds.transform, ds.crs
    payload = json.loads(_local(root, label_key).read_text())
    shapes = [(shape(f["geometry"]), 1) for f in payload.get("features", []) if f.get("geometry")]
    label = rasterize(shapes, out_shape=(900, 900), transform=transform, fill=0, all_touched=False,
                      dtype=np.uint8).astype(bool)
    if not valid.any():
        raise ValueError(f"empty common valid support: {tile}")
    image = torch.from_numpy(np.stack(arrays))
    label_t = torch.from_numpy(label[None, None].astype(np.float32))
    valid_t = torch.from_numpy(valid[None, None].astype(np.float32))
    image = F.interpolate(image, size=(448, 448), mode="bilinear", align_corners=False)
    label_t = F.interpolate(label_t, size=(448, 448), mode="nearest")[0, 0] > 0.5
    valid_t = F.interpolate(valid_t, size=(448, 448), mode="nearest")[0, 0] > 0.5
    if not valid_t.any():
        raise ValueError(f"empty resized common valid support: {tile}")
    return image.numpy(), label_t.numpy(), valid_t.numpy(), {"crs": str(crs), "transform": tuple(transform),
        "raw_min": float(np.min(image.numpy())), "raw_max": float(np.max(image.numpy())), "valid_pixels": int(valid_t.sum()),
        "foreground_pixels": int((label_t & valid_t).sum())}


def make_cache(manifest: dict, split: str, root: Path, out: Path, inspect_only: bool = False) -> dict:
    images = defaultdict(dict)
    for item in manifest["images"]:
        if item["split"] == split:
            images[item["tile"]][item["catid"]] = item["key"]
    labels = {x["tile"]: x["key"] for x in manifest["labels"] if x["split"] == split}
    tiles = manifest[f"{split}ing_tiles"] if split == "train" else manifest["calibration_tiles"]
    summaries, cache_dir = {}, out / "cache" / split
    cache_dir.mkdir(parents=True, exist_ok=True)
    for index, tile in enumerate(tiles):
        if set(images[tile]) != set(VIEWS) or tile not in labels:
            raise ValueError(f"manifest incomplete for {tile}")
        image, label, valid, summary = _read_tile(tile, images[tile], labels[tile], root)
        summaries[tile] = summary
        if not inspect_only:
            np.savez_compressed(cache_dir / f"{tile}.npz", image=image.astype(np.float16), label=label, valid=valid)
        if inspect_only and index == 15:
            break
    _write(out / ("preflight_train.json" if inspect_only else f"cache_{split}.json"), summaries)
    return summaries


def _model(weights: Path):
    import torch
    from torchvision.models.segmentation import fcn_resnet50
    model = fcn_resnet50(weights=None, weights_backbone=None, num_classes=1, aux_loss=False)
    state = torch.load(weights, map_location="cpu", weights_only=True)
    state = {k: v for k, v in state.items() if not k.startswith("fc.")}
    model.backbone.load_state_dict(state, strict=True)
    return model


def _normalise(x):
    import torch
    mean = torch.tensor((0.485, 0.456, 0.406), device=x.device)[None, :, None, None]
    std = torch.tensor((0.229, 0.224, 0.225), device=x.device)[None, :, None, None]
    return (torch.clamp(x / 3000.0, 0, 1) - mean) / std


def train(manifest: dict, root: Path, out: Path, weights: Path, device: str) -> list[dict]:
    import torch
    import torch.nn.functional as F
    cache = out / "cache" / "train"
    tiles = manifest["training_tiles"]
    fractions = []
    for tile in tiles:
        x = np.load(cache / f"{tile}.npz")
        fractions.append(float((x["label"] & x["valid"]).sum() / x["valid"].sum()))
    pi = float(np.mean(fractions))
    if not 0 < pi < 1:
        raise ValueError("invalid fixed training foreground fraction")
    details = {"foreground_fraction": pi, "foreground_weight": 1 / (2 * pi), "background_weight": 1 / (2 * (1 - pi)),
               "samples_per_epoch": len(tiles) * 4}
    _write(out / "training_loss_definition.json", details)
    result = []
    for seed in (1701, 1702):
        checkpoint = out / "checkpoints" / f"seed{seed}_epoch30.pt"
        if checkpoint.exists():
            result.append({"seed": seed, "checkpoint": str(checkpoint), "reused": True})
            continue
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        model = _model(weights).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4, betas=(0.9, .999), eps=1e-8)
        history = []
        for epoch in range(30):
            model.train(); generator = np.random.default_rng(seed * 1000 + epoch); order = generator.permutation(len(tiles))
            samples = [(tiles[i], v) for i in order for v in generator.permutation(4)]
            optimizer.zero_grad(set_to_none=True); running = 0.0
            for start in range(0, len(samples), 4):
                batch = samples[start:start + 4]
                xs, ys, ms = [], [], []
                for tile, view in batch:
                    d = np.load(cache / f"{tile}.npz")
                    image, label, valid = d["image"][view].astype(np.float32), d["label"], d["valid"]
                    k = int(generator.integers(4)); flip = bool(generator.integers(2))
                    image = np.rot90(image, k, axes=(-2, -1)); label = np.rot90(label, k); valid = np.rot90(valid, k)
                    if flip: image = image[:, :, ::-1]; label = label[:, ::-1]; valid = valid[:, ::-1]
                    xs.append(np.ascontiguousarray(image)); ys.append(np.ascontiguousarray(label)); ms.append(np.ascontiguousarray(valid))
                x = torch.from_numpy(np.stack(xs)).to(device); y = torch.from_numpy(np.stack(ys)).to(device); m = torch.from_numpy(np.stack(ms)).to(device)
                logits = model(_normalise(x))["out"][:, 0]
                weights_px = torch.where(y > .5, 1 / (2 * pi), 1 / (2 * (1 - pi)))
                per = (F.binary_cross_entropy_with_logits(logits, y, reduction="none") * weights_px * m).sum((1, 2)) / m.sum((1, 2))
                loss = per.mean() / 2
                loss.backward(); running += float(per.detach().sum().cpu())
                if (start // 4 + 1) % 2 == 0:
                    optimizer.step(); optimizer.zero_grad(set_to_none=True)
            history.append({"epoch": epoch + 1, "image_mean_weighted_bce": running / len(samples)})
            _write(out / "training" / f"seed{seed}.json", history)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"seed": seed, "epoch": 30, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "training_loss": details}, checkpoint)
        result.append({"seed": seed, "checkpoint": str(checkpoint), "reused": False, "sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest()})
        del model; torch.cuda.empty_cache()
    _write(out / "training_manifest.json", result)
    return result


def evaluate(manifest: dict, out: Path, device: str) -> dict:
    import torch
    cache, pi = out / "cache" / "calibration", _json(out / "training_loss_definition.json")["foreground_fraction"]
    blocks = {t: tuple(map(int, t.split("_"))) for t in manifest["calibration_tiles"]}
    rows = []
    for seed in (1701, 1702):
        ckpt = torch.load(out / "checkpoints" / f"seed{seed}_epoch30.pt", map_location="cpu", weights_only=False)
        model = _model(Path("/home/rspip/cqc/study/pth_data/rareplanes_initialization/resnet50-11ad3fa6.pth")); model.load_state_dict(ckpt["model"], strict=True); model.to(device).eval()
        with torch.inference_mode():
            for tile in manifest["calibration_tiles"]:
                d = np.load(cache / f"{tile}.npz"); x = torch.from_numpy(d["image"].astype(np.float32)).to(device)
                p = torch.sigmoid(model(_normalise(x))["out"][:, 0]).cpu().numpy()
                tta = []
                for view in (0, 1):
                    z = torch.rot90(x[view:view+1], 1, (-2, -1)); q = torch.sigmoid(model(_normalise(z))["out"][:, 0]); tta.append(torch.rot90(q, -1, (-2, -1))[0, 0].cpu().numpy())
                cross = crossed_comparison(*p, d["label"], d["valid"], pi)
                single = {f"loss_{name}": weighted_log_loss(p[i], d["label"], d["valid"], pi) for i, name in enumerate(("a", "b", "u", "v"))}
                for name, prob in (("a_tta", (p[0] + tta[0]) / 2), ("b_tta", (p[1] + tta[1]) / 2)):
                    single[f"loss_{name}"] = weighted_log_loss(prob, d["label"], d["valid"], pi)
                iou = {}
                for name, prob in (("a", p[0]), ("b", p[1]), ("u", p[2]), ("v", p[3]), ("au", (p[0]+p[2])/2), ("av", (p[0]+p[3])/2), ("bv", (p[1]+p[3])/2), ("bu", (p[1]+p[2])/2)):
                    pred, truth, valid = prob >= .5, d["label"], d["valid"]
                    iou[f"iou_{name}_intersection"] = int((pred & truth & valid).sum()); iou[f"iou_{name}_union"] = int(((pred | truth) & valid).sum())
                single["loss_constant_half"] = weighted_log_loss(np.full_like(d["label"], .5, dtype=np.float64), d["label"], d["valid"], pi)
                single["loss_constant_prevalence"] = weighted_log_loss(np.full_like(d["label"], pi, dtype=np.float64), d["label"], d["valid"], pi)
                rows.append({"seed": seed, "tile": tile, "block": blocks[tile], **cross, **single, **iou})
        del model; torch.cuda.empty_cache()
    _write(out / "evaluation_rows.json", rows)
    per = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for key, value in row.items():
            if key.startswith(("loss_", "delta_", "primary")):
                per[row["block"]][key].append(value)
    block_values = {str(k): {metric: float(np.mean(vals)) for metric, vals in v.items()} for k, v in per.items()}
    primary = np.array([v["primary"] for v in block_values.values()])
    rng = np.random.Generator(np.random.PCG64(17017)); draws = primary[rng.integers(0, len(primary), (20000, len(primary)))].mean(1)
    summary = {"foreground_fraction": pi, "blocks": len(block_values), "block_equal_primary": float(primary.mean()),
               "primary_95_ci": [float(np.quantile(draws, .025)), float(np.quantile(draws, .975))],
               "bootstrap_seed": 17017, "bootstrap_draws": 20000, "block_values": block_values,
               "rows": len(rows), "constant_half_loss": float(np.log(2)),
               "constant_prevalence_loss": float(np.mean([r["loss_constant_prevalence"] for r in rows]))}
    _write(out / "evaluation_summary.json", summary)
    return summary


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--weights", type=Path, required=True); p.add_argument("--device", default="cuda:2")
    args = p.parse_args(); manifest = _json(args.manifest); args.out.mkdir(parents=True, exist_ok=True)
    train_items = [x for x in manifest["images"] if x["split"] == "train"] + [x for x in manifest["labels"] if x["split"] == "train"]
    ledger = args.out / "downloads.json"
    acquire(train_items, args.root, ledger, 12_000_000_000)
    make_cache(manifest, "train", args.root, args.out, inspect_only=True)
    make_cache(manifest, "train", args.root, args.out)
    train(manifest, args.root, args.out, args.weights, args.device)
    calibration_items = [x for x in manifest["images"] if x["split"] == "calibration"] + [x for x in manifest["labels"] if x["split"] == "calibration"]
    acquire(calibration_items, args.root, ledger, 12_000_000_000)
    make_cache(manifest, "calibration", args.root, args.out)
    evaluate(manifest, args.out, args.device)


if __name__ == "__main__":
    main()

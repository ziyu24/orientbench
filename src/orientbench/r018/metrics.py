"""Shape-safe TTA, direct label rasterization, and paired spatial summaries."""
import numpy as np

from orientbench.r017.measurement import crossed_comparison, weighted_log_loss


def invert_rotated_prediction(probability):
    p = np.asarray(probability)
    if p.ndim != 3 or p.shape[0] != 1:
        raise ValueError("expected one B,H,W probability map with no class axis")
    return np.rot90(p, -1, axes=(-2, -1))[0].copy()


def fuse_maps(first, second):
    a, b = np.asarray(first), np.asarray(second)
    if a.ndim != 2 or a.shape != b.shape:
        raise ValueError("fusion requires two identical H,W grids; broadcasting is forbidden")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("nonfinite predictions")
    if np.any((a < 0) | (a > 1) | (b < 0) | (b > 1)):
        raise ValueError("predictions must be probabilities")
    return (a + b) / 2


def rasterize_direct(payload, raw_transform, raw_crs, side=448):
    from affine import Affine
    from rasterio.crs import CRS
    from rasterio.features import rasterize
    declared = payload.get("crs", {}).get("properties", {}).get("name")
    if declared is None or CRS.from_user_input(declared) != CRS.from_user_input(raw_crs):
        raise ValueError("GeoJSON and image CRS must agree")
    if payload.get("type") != "FeatureCollection":
        raise ValueError("expected GeoJSON FeatureCollection")
    shapes = []
    for feature in payload["features"]:
        geometry = feature.get("geometry")
        if not geometry or geometry.get("type") not in ("Polygon", "MultiPolygon"):
            raise ValueError("invalid building geometry")
        shapes.append((geometry, 1))
    transform = Affine(*raw_transform[:6]) * Affine.scale(900 / side, 900 / side)
    if not shapes:
        return np.zeros((side, side), dtype=bool)
    return rasterize(shapes, out_shape=(side, side), transform=transform,
                     fill=0, all_touched=False, dtype="uint8").astype(bool)


def measure(p, rotations, target, valid, pi):
    if np.shape(p) != (4, *np.shape(target)) or np.shape(rotations) != (2, *np.shape(target)):
        raise ValueError("four base and two aligned rotated maps required")
    result = crossed_comparison(*p, target, valid, pi)
    maps = dict(zip(("a", "b", "u", "v"), p))
    maps.update(au=fuse_maps(p[0], p[2]), av=fuse_maps(p[0], p[3]),
                bv=fuse_maps(p[1], p[3]), bu=fuse_maps(p[1], p[2]),
                a_tta=fuse_maps(p[0], rotations[0]), b_tta=fuse_maps(p[1], rotations[1]))
    maps.update(constant_half=np.full(target.shape, .5), constant_prevalence=np.full(target.shape, pi))
    for name, prob in maps.items():
        result[f"loss_{name}"] = weighted_log_loss(prob, target, valid, pi)
        if not name.startswith("constant"):
            pred = prob >= .5
            result[f"iou_{name}_intersection"] = int((pred & target & valid).sum())
            result[f"iou_{name}_union"] = int(((pred | target) & valid).sum())
    result["tta_gain_a"] = result["loss_a_tta"] - result["loss_av"]
    result["tta_gain_b"] = result["loss_b_tta"] - result["loss_bu"]
    return result


def summarise(rows, tiles, seeds=(1701, 1702)):
    lookup = {(r["seed"], r["tile"]): r for r in rows}
    if len(lookup) != len(rows) or set(lookup) != {(s, t) for s in seeds for t in tiles}:
        raise ValueError("complete unique frozen tile-by-seed table required")
    block = lambda t: tuple(int(v) // 2700 for v in t.split("_"))
    # First occurrence in frozen tile order reproduces the original bootstrap ordering.
    blocks = list(dict.fromkeys(map(block, tiles)))
    groups = [[t for t in tiles if block(t) == b] for b in blocks]
    metrics = [k for k in rows[0] if k.startswith(("loss_", "delta_", "tta_gain_")) or k == "primary"]
    seed_blocks = {s: {k: [float(np.mean([lookup[s, t][k] for t in g])) for g in groups]
                       for k in metrics} for s in seeds}
    block_means = {k: np.mean([seed_blocks[s][k] for s in seeds], axis=0) for k in metrics}
    rng = np.random.Generator(np.random.PCG64(17017))
    index = rng.integers(0, len(blocks), (20000, len(blocks)))
    intervals = {k: np.quantile(v[index].mean(1), [.025, .975]).tolist() for k, v in block_means.items()}
    iou = {}
    for key in rows[0]:
        if not (key.startswith("iou_") and key.endswith("_intersection")):
            continue
        union_key = key.replace("_intersection", "_union")
        per_seed = []
        for s in seeds:
            values = []
            for g in groups:
                denominator = sum(lookup[s, t][union_key] for t in g)
                values.append(None if denominator == 0 else sum(lookup[s, t][key] for t in g) / denominator)
            per_seed.append(values)
        defined = all(v is not None for values in per_seed for v in values)
        iou[key[4:-13]] = {"seed_blocks": per_seed, "equal_mean": float(np.mean(per_seed)) if defined else None}
    return {"blocks": blocks, "rows": len(rows), "metric_block_equal": {k: float(v.mean()) for k, v in block_means.items()},
            "intervals_95": intervals, "interval_scope": "Only primary I is the original primary; other intervals are descriptive, conditional on this one pass.",
            "seed_block_equal": {str(s): {k: float(np.mean(v)) for k, v in seed_blocks[s].items()} for s in seeds},
            "seed_block_values": seed_blocks, "iou": iou}

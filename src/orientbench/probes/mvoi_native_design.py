"""Match native strip means at common training tiles; no pixels or model outcomes."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
import itertools
import json
import math
from pathlib import Path


def design(inventory_path: Path, out: Path) -> dict:
    from pyproj import Transformer
    from shapely.geometry import Polygon, box

    inventory = json.loads(inventory_path.read_text())
    grouped = defaultdict(list)
    transform = Transformer.from_crs(4326, 32616, always_xy=True)
    for record in inventory["native_records"]:
        corners = record["corners_lon_lat"]
        poly = Polygon([transform.transform(corners[p + "Lon"], corners[p + "Lat"])
                        for p in ("UL", "UR", "LR", "LL")])
        if not poly.is_valid:
            raise ValueError("invalid native footprint")
        grouped[record["catid"]].append((record, poly))
    catalogs = sorted(grouped)

    def angle(a, b, period=360):
        return abs((a - b + period / 2) % period - period / 2)

    def ray(a, b, az="meanSatAz", el="meanSatEl"):
        ea, eb = map(math.radians, (float(a[el]), float(b[el])))
        da = math.radians(angle(float(a[az]), float(b[az])))
        cosine = math.sin(ea) * math.sin(eb) + math.cos(ea) * math.cos(eb) * math.cos(da)
        return math.degrees(math.acos(max(-1, min(1, cosine))))

    @lru_cache(None)
    def pair(i, inds, j, jnds):
        items = [(grouped[i][u][0]["image_fields"], grouped[j][v][0]["image_fields"])
                 for u in inds for v in jnds]
        if not items:
            return None
        return {
            "azimuth_max": max(angle(float(a["meanSatAz"]), float(b["meanSatAz"])) for a, b in items),
            "azimuth_min": min(angle(float(a["meanSatAz"]), float(b["meanSatAz"])) for a, b in items),
            "axis_min": min(angle(float(a["meanSatAz"]), float(b["meanSatAz"]), 180) for a, b in items),
            "ray_max": max(ray(a, b) for a, b in items),
            "ray_min": min(ray(a, b) for a, b in items),
            "off_difference_max": max(abs(float(a["meanOffNadirViewAngle"]) - float(b["meanOffNadirViewAngle"])) for a, b in items),
            "gsd_ratio_max": max(max(float(a["meanCollectedGSD"]), float(b["meanCollectedGSD"])) /
                                 min(float(a["meanCollectedGSD"]), float(b["meanCollectedGSD"])) for a, b in items),
            "sun_ray_max": max(ray(a, b, "meanSunAz", "meanSunEl") for a, b in items),
        }

    @lru_cache(None)
    def candidates(signature):
        mapping = dict(zip(catalogs, signature))
        output = []
        for i, r, j in itertools.permutations(catalogs, 3):
            near, far, matched = pair(i, mapping[i], r, mapping[r]), pair(i, mapping[i], j, mapping[j]), pair(r, mapping[r], j, mapping[j])
            if not (near and far and matched):
                continue
            if not (near["azimuth_max"] <= 10 and near["ray_max"] <= 5 and far["azimuth_min"] >= 60
                    and far["ray_min"] >= 15 and matched["off_difference_max"] <= 2
                    and matched["gsd_ratio_max"] <= 1.05 and matched["sun_ray_max"] <= 3):
                continue
            selected = [grouped[c][k][0]["image_fields"] for c in (i, r, j) for k in mapping[c]]
            if {f["satId"] for f in selected} != {"WV02"}:
                raise ValueError("sensor mismatch")
            times = [datetime.fromisoformat(f["firstLineTime"].replace("Z", "+00:00")) for f in selected]
            if (max(times) - min(times)).total_seconds() > 600:
                continue
            output.append((i, r, j))
        return tuple(output)

    zero_byte_labels = set()
    for obj in inventory["label_file_names_only"]:
        if obj["bytes"] == 0:
            zero_byte_labels.add("_".join(Path(obj["key"]).stem.split("_")[-2:]))
    by_tile, counts, signatures, selected_strips = {}, Counter(), Counter(), {}
    for tile in inventory["common_training_tiles"]:
        x, y = map(int, tile.split("_"))
        # Confirmed processed GeoTIFF: 900 px at 0.5 m; filename is lower-left UTM.
        polygon = box(x, y, x + 450, y + 450)
        # Include every strip intersecting the tile, not just a favorable covering strip.
        intersecting = tuple(tuple(k for k, (_, p) in enumerate(grouped[c]) if p.intersects(polygon)) for c in catalogs)
        fully_covered = tuple(any(p.covers(polygon) for _, p in grouped[c]) for c in catalogs)
        signature = tuple(indices if covered else () for indices, covered in zip(intersecting, fully_covered))
        signatures[signature] += 1
        triples = candidates(signature) if tile not in zero_byte_labels else ()
        by_tile[tile] = triples
        counts.update(triples)
        if triples:
            used = set(itertools.chain.from_iterable(triples))
            selected_strips[tile] = {c: [grouped[c][k][0]["source_key"] for k in signature[catalogs.index(c)]]
                                    for c in sorted(used)}
    result = {
        "scope": "Training tile footprint coverage and all intersecting native strip means. Not exact per-pixel geometry, measured PSF, or task-benefit evidence.",
        "acquisitions": len(catalogs), "native_strips": len(inventory["native_records"]),
        "common_training_tiles": len(by_tile), "zero_byte_label_files_excluded": len(zero_byte_labels),
        "tiles_with_primary_support": sum(bool(v) for v in by_tile.values()),
        "primary_tile_triplets": sum(counts.values()), "primary_distinct_triplets": len(counts),
        "coverage_signatures": len(signatures),
        "triplets": [{"ids": list(t), "tiles": n} for t, n in sorted(counts.items(), key=lambda item: (-item[1], item[0]))],
        "by_tile": by_tile, "intersecting_native_strips": selected_strips,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("by_tile", "intersecting_native_strips")}, indent=2), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    design(args.inventory, args.out)

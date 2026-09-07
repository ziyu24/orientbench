"""Read existing non-test metadata and TIFF headers; never decode image pixels.

This is a B research feasibility check, not a SERVER experiment or an
acquisition-geometry calibration. No object angles, attributes, or predictions
are joined to acquisition metadata. Output goes only to stdout.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path


def inspect(root: Path, dataset: Path) -> dict:
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    meta_path = dataset / "real/metadata_annotations/RarePlanes_Public_Metadata.csv"
    pre_path = root / "runs/r015/artifacts/preflight.json"
    g0_path = root / "runs/r012/final_repair_artifacts/primary.json"
    meta_bytes = meta_path.read_bytes()
    metadata = list(csv.DictReader(meta_bytes.decode("utf-8-sig").splitlines()))
    pre = json.loads(pre_path.read_text())
    split = json.loads(g0_path.read_text())["split"]
    locations = {
        part: {int(loc) for key in groups for loc in key.split(":", 1)[1].split(",")}
        for part, groups in split.items()
    }
    numeric = (
        "off_nadir_max", "target_azimuth_maximum", "pan_resolution_minimum",
        "pan_resolution_maximum", "avg_sun_elevation_angle",
    )
    output = {
        "metadata_sha256": hashlib.sha256(meta_bytes).hexdigest(),
        "metadata_fields": list(metadata[0]),
        "metadata_total_rows": len(metadata),
        "partitions": {},
        "scope": "Existing train/calibration metadata and TIFF headers only. No pixel decode, "
                 "test image access, model forward, object-angle/attribute/outcome join, or writes.",
    }
    for part in ("train", "calibration"):
        selected = [r for r in metadata if int(r["loc_id"]) in locations[part]]
        assert all(int(r["loc_id"]) not in locations["test"] for r in selected)
        by_loc = defaultdict(list)
        for row in selected:
            by_loc[row["loc_id"]].append(row)
        stats = {}
        for field in numeric:
            values = []
            invalid = 0
            for row in selected:
                try:
                    value = float(row[field])
                    if not math.isfinite(value):
                        raise ValueError(field)
                    values.append(value)
                except (KeyError, ValueError):
                    invalid += 1
            stats[field] = {"valid": len(values), "invalid": invalid,
                            "min": min(values) if values else None,
                            "max": max(values) if values else None}
        sources = sorted({r["image_id"] for r in pre["records"][part]})
        selected_ids = {r["image_id"] for r in selected}
        used_by_loc = Counter(r["loc_id"] for r in selected if r["image_id"] in sources)
        headers = []
        for source in sources:
            assert source in selected_ids
            candidates = [dataset / "real/imagery" / p / "PS-RGB_cog" / (source + ".tif")
                          for p in ("train", "calibration")]
            found = [p for p in candidates if p.is_file()]
            assert len(found) == 1, (source, "source path not unique")
            with Image.open(found[0]) as image:
                # Reading tag_v2 and dimensions does not call load(), crop(), or np.asarray().
                tags = sorted(int(k) for k in image.tag_v2)
                headers.append({"source": source, "width": image.width,
                                "height": image.height, "tiff_tags": tags,
                                "rpc_tag_50844": 50844 in tags})
        repeated = [rows for rows in by_loc.values() if len(rows) > 1]
        output["partitions"][part] = {
            "metadata_rows": len(selected), "locations": len(by_loc),
            "components": len(split[part]),
            "r015_used_source_count": len(sources),
            "r015_used_location_count": len(used_by_loc),
            "r015_used_repeated_locations": sum(n > 1 for n in used_by_loc.values()),
            "r015_used_within_location_image_pairs": sum(n * (n - 1) // 2 for n in used_by_loc.values()),
            "repeated_locations": len(repeated),
            "within_location_image_pairs": sum(len(r) * (len(r) - 1) // 2 for r in repeated),
            "same_location_does_not_prove_same_aircraft": True,
            "location_observation_count_distribution": dict(Counter(map(len, by_loc.values()))),
            "sensors": dict(Counter(r["sensor"] for r in selected)),
            "scan_direction_values": dict(Counter(r["scan_direction"] for r in selected)),
            "numeric_metadata": stats,
            "source_headers": headers,
            "rpc_header_count": sum(r["rpc_tag_50844"] for r in headers),
        }
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.root, args.dataset), indent=2, sort_keys=True))

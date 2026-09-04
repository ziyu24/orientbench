"""Build the r010 RarePlanes real-only asset and split evidence.

This module deliberately does not import a detection model, nor open image pixels.
It validates source files, computes the component-held-out split from source
metadata, and records the evidence needed before any downstream experiment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

EXPECTED = {
    "LICENSE.txt": 20605,
    "real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson": 12529647,
    "real/metadata_annotations/RarePlanes_Public_Metadata.csv": 48458,
    "real/metadata_annotations/RarePlanes_Test_Coco_Annotations_tiled.json": 12535089,
    "real/metadata_annotations/RarePlanes_Train_Coco_Annotations_tiled.json": 33539381,
    "real/tarballs/test/RarePlanes_test_PS-RGB_cog.tar.gz": 1372184300,
    "real/tarballs/train/RarePlanes_train_PS-RGB_cog.tar.gz": 2402034321,
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_wing(value: object) -> str | None:
    # These are fixed canonical spellings for the official source vocabulary.
    return {"straight": "straight", "swept": "swept-back", "delta": "delta",
            "variable swept": "variable-sweep"}.get(str(value).strip().lower())


def attr_value(name: str, properties: dict) -> str | None:
    if name == "wing":
        wing = canonical_wing(properties.get("wing_type"))
        return "straight" if wing == "straight" else "nonstraight" if wing in {"swept-back", "delta", "variable-sweep"} else None
    if name == "engine_count":
        try:
            count = int(properties.get("num_engines"))
        except (TypeError, ValueError):
            return None
        return "2" if count == 2 else "other" if count in {0, 1, 3, 4} else None
    if name == "propulsion":
        value = str(properties.get("propulsion", "")).strip().lower()
        return "jet" if value == "jet" else "nonjet" if value in {"propeller", "unpowered"} else None
    raise ValueError(name)


def components(features: list[dict], metadata: list[dict]) -> tuple[dict[int, str], list[list[int]]]:
    """Connected loc components through CAT and official source-product rows.

    A source product has one metadata image_id and its loc/CAT labels.  The
    bipartite graph is then augmented with exact GeoJSON polygon intersection;
    object polygons at one collection location consequently cannot cross splits.
    """
    parent: dict[str, str] = {}
    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a: str, b: str) -> None:
        a, b = find(a), find(b)
        if a != b: parent[b] = a
    for row in metadata:
        loc, cat, image = str(row["loc_id"]), str(row["cat_id"]), str(row["image_id"])
        union("L:" + loc, "C:" + cat)
        union("L:" + loc, "I:" + image)
        union("C:" + cat, "I:" + image)
    # GeoJSON records are authoritative for object census and must all attach.
    for feature in features:
        prop = feature["properties"]
        union("L:" + str(prop["loc_id"]), "C:" + str(prop["cat_id"]))
    locs = sorted({int(f["properties"]["loc_id"]) for f in features})
    groups: dict[str, list[int]] = defaultdict(list)
    for loc in locs: groups[find("L:" + str(loc))].append(loc)
    ordered = sorted((sorted(v) for v in groups.values()), key=lambda v: tuple(v))
    key_for_loc = {loc: "loc:" + ",".join(map(str, group)) for group in ordered for loc in group}
    return key_for_loc, ordered


def split_components(groups: list[list[int]]) -> dict[str, list[list[int]]]:
    ordered = sorted(groups, key=lambda group: "loc:" + ",".join(map(str, group)))
    order = np.random.Generator(np.random.PCG64(1010)).permutation(len(ordered))
    shuffled = [ordered[int(i)] for i in order]
    return {"test": shuffled[:25], "calibration": shuffled[25:50], "train": shuffled[50:]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--third-party", type=Path, required=True)
    parser.add_argument("--pth-index", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    objects = []
    complete = True
    for key, expected_bytes in EXPECTED.items():
        path = root / key
        exists = path.is_file()
        size = path.stat().st_size if exists else None
        valid = exists and size == expected_bytes
        complete &= valid
        objects.append({"official_key": key, "expected_bytes": expected_bytes,
                        "local_path": str(path), "exists": exists, "bytes": size,
                        "byte_match": valid, "sha256": digest(path) if valid else None})
    license_text = (root / "LICENSE.txt").read_text(errors="replace") if (root / "LICENSE.txt").is_file() else ""
    license_ok = "CC BY-SA 4.0" in license_text or "Creative Commons Attribution-ShareAlike 4.0" in license_text
    geo_path = root / "real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson"
    csv_path = root / "real/metadata_annotations/RarePlanes_Public_Metadata.csv"
    parse_ok = complete and license_ok
    features: list[dict] = []
    rows: list[dict] = []
    if parse_ok:
        try:
            features = json.loads(geo_path.read_text())["features"]
            with csv_path.open(newline="") as stream: rows = list(csv.DictReader(stream))
        except (OSError, ValueError, KeyError):
            parse_ok = False
    image_ids = [str(row.get("image_id", "")) for row in rows]
    feature_locs = {int(f["properties"]["loc_id"]) for f in features} if parse_ok else set()
    row_locs = {int(row["loc_id"]) for row in rows if row.get("loc_id", "").isdigit()} if parse_ok else set()
    comp_map, comps = components(features, rows) if parse_ok else ({}, [])
    split_groups = split_components(comps) if len(comps) >= 50 else {"test": [], "calibration": [], "train": []}
    split_locs = {name: {loc for group in groups for loc in group} for name, groups in split_groups.items()}
    support: dict[str, dict[str, dict[str, int]]] = {}
    for name in ("wing", "engine_count", "propulsion"):
        support[name] = {split: dict(Counter(attr_value(name, f["properties"]) for f in features
                                               if int(f["properties"]["loc_id"]) in locs and attr_value(name, f["properties"]) is not None))
                         for split, locs in split_locs.items()}
    support_ok = all(min(support[name][split].get(label, 0) for split in split_locs) >= threshold
                     for name, labels, threshold in (("wing", ("straight", "nonstraight"), 100),
                                                      ("engine_count", ("2", "other"), 100),
                                                      ("propulsion", ("jet", "nonjet"), 100)) for label in labels)
    # No directory is treated as a model.  This inventory only recognizes an explicit
    # recorded provenance manifest, written by acquisition, with immutable revisions.
    model_manifest = root / "model_assets.json"
    model_assets = json.loads(model_manifest.read_text()) if model_manifest.is_file() else {"assets": []}
    required = {"oriented_rcnn", "rotated_rtmdet", "ars_detr", "o2_rtdetr", "fred", "resnet50", "vit_b16"}
    good_models = {x.get("id") for x in model_assets.get("assets", []) if x.get("license") and x.get("revision") and x.get("sha256") and x.get("local_path") and Path(x["local_path"]).exists()}
    models_ok = required <= good_models
    lineage_path = root / "image_archive_index.json"
    lineage = json.loads(lineage_path.read_text()) if lineage_path.is_file() else {}
    lineage_ok = lineage.get("all_one_to_one") is True
    data_ok = parse_ok and lineage_ok and len(rows) == 253 and len(set(image_ids)) == 253 and feature_locs <= row_locs and len(comps) >= 100 and support_ok
    token = "READY_FOR_BC_R011_FINAL_VALIDATION" if data_ok and models_ok else "ASSET_UNAVAILABLE_R010" if parse_ok else "INCONCLUSIVE_R010_ASSET_MATERIALIZATION"
    out = {"protocol": "r010-real-materialization-v1", "official_source": "s3://rareplanes-public/", "objects": objects,
           "license": {"cc_by_sa_4_0_verified": license_ok}, "parse_ok": parse_ok,
           "real_metadata": {"image_records": len(rows), "unique_image_records": len(set(image_ids)), "geojson_objects": len(features),
                             "geojson_loc_ids": len(feature_locs), "metadata_loc_ids": len(row_locs), "all_annotation_locs_in_metadata": feature_locs <= row_locs},
           "component_algorithm": "loc_id-CAT-source_product graph; GeoJSON location attachment; PCG64(1010)",
           "image_lineage": {"path": str(lineage_path), "all_one_to_one": lineage_ok},
           "component_count": len(comps), "split_components": {k: ["loc:" + ",".join(map(str, x)) for x in v] for k, v in split_groups.items()},
           "support": support, "support_gate_passed": support_ok,
           "models": {"required": sorted(required), "provenanced": sorted(x for x in good_models if x), "passed": models_ok},
           "token": token}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

if __name__ == "__main__":
    main()

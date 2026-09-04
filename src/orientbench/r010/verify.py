"""Independent r010 real-asset verifier.

It intentionally duplicates, rather than imports, the audit's component and
support logic.  It reads only the official materialised files and its own model
provenance registry; it never reads the primary audit outcome.
"""
from __future__ import annotations

import argparse
import csv
import json
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

SIZES = {"LICENSE.txt": 20605,
         "real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson": 12529647,
         "real/metadata_annotations/RarePlanes_Public_Metadata.csv": 48458,
         "real/metadata_annotations/RarePlanes_Test_Coco_Annotations_tiled.json": 12535089,
         "real/metadata_annotations/RarePlanes_Train_Coco_Annotations_tiled.json": 33539381,
         "real/tarballs/test/RarePlanes_test_PS-RGB_cog.tar.gz": 1372184300,
         "real/tarballs/train/RarePlanes_train_PS-RGB_cog.tar.gz": 2402034321}

def label(which, p):
    if which == "wing":
        x = str(p.get("wing_type", "")).strip().lower()
        return "straight" if x == "straight" else "nonstraight" if x in {"swept", "delta", "variable swept"} else None
    if which == "engine_count":
        try: x = int(p.get("num_engines"))
        except (ValueError, TypeError): return None
        return "2" if x == 2 else "other" if x in (0, 1, 3, 4) else None
    x = str(p.get("propulsion", "")).strip().lower()
    return "jet" if x == "jet" else "nonjet" if x in ("propeller", "unpowered") else None

def make_groups(feats, rows):
    p = {}
    def root(x):
        p.setdefault(x, x)
        if p[x] != x: p[x] = root(p[x])
        return p[x]
    def join(a, b):
        a, b = root(a), root(b)
        if a != b: p[b] = a
    for r in rows:
        a, b, c = "l" + r["loc_id"], "c" + r["cat_id"], "i" + r["image_id"]
        join(a, b); join(b, c)
    for f in feats: join("l" + str(f["properties"]["loc_id"]), "c" + str(f["properties"]["cat_id"]))
    result = defaultdict(list)
    for loc in sorted({int(f["properties"]["loc_id"]) for f in feats}): result[root("l" + str(loc))].append(loc)
    return sorted((sorted(v) for v in result.values()), key=lambda x: tuple(x))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, required=True); ap.add_argument("--out", type=Path, required=True); a = ap.parse_args()
    source_ok = all((a.root / k).is_file() and (a.root / k).stat().st_size == n for k, n in SIZES.items())
    text = (a.root / "LICENSE.txt").read_text(errors="replace") if (a.root / "LICENSE.txt").is_file() else ""
    license_ok = "CC BY-SA 4.0" in text or "Creative Commons Attribution-ShareAlike 4.0" in text
    feats = []; rows = []; parsed = False
    if source_ok and license_ok:
        try:
            feats = json.loads((a.root / "real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson").read_text())["features"]
            with (a.root / "real/metadata_annotations/RarePlanes_Public_Metadata.csv").open(newline="") as h: rows = list(csv.DictReader(h))
            parsed = True
        except (OSError, ValueError, KeyError): pass
    groups = make_groups(feats, rows) if parsed else []
    ordered = sorted(groups, key=lambda z: "loc:" + ",".join(map(str, z)))
    shuffled = [ordered[int(i)] for i in np.random.Generator(np.random.PCG64(1010)).permutation(len(ordered))] if len(ordered) >= 50 else []
    splits = {"test": {x for g in shuffled[:25] for x in g}, "calibration": {x for g in shuffled[25:50] for x in g}, "train": {x for g in shuffled[50:] for x in g}}
    counts = {kind: {part: dict(Counter(label(kind, f["properties"]) for f in feats if int(f["properties"]["loc_id"]) in locs and label(kind, f["properties"]) is not None)) for part, locs in splits.items()} for kind in ("wing", "engine_count", "propulsion")}
    member_names = []
    if source_ok:
        try:
            for arc in (a.root / "real/tarballs/test/RarePlanes_test_PS-RGB_cog.tar.gz", a.root / "real/tarballs/train/RarePlanes_train_PS-RGB_cog.tar.gz"):
                with tarfile.open(arc, "r:gz") as archive: member_names += [m.name.lower() for m in archive.getmembers() if m.isfile() and m.name.lower().endswith((".tif", ".tiff"))]
        except (OSError, tarfile.TarError): member_names = []
    imagery_ok = len(rows) == 253 and all(sum(r["image_id"].lower() in Path(m).stem for m in member_names) == 1 for r in rows)
    gate = parsed and imagery_ok and len(rows) == len(set(r["image_id"] for r in rows)) == 253 and len(groups) >= 100
    for kind, pair in (("wing", ("straight", "nonstraight")), ("engine_count", ("2", "other")), ("propulsion", ("jet", "nonjet"))):
        gate &= all(counts[kind][part].get(v, 0) >= 100 for part in splits for v in pair)
    models = json.loads((a.root / "model_assets.json").read_text()) if (a.root / "model_assets.json").is_file() else {"assets": []}
    need = {"oriented_rcnn", "rotated_rtmdet", "ars_detr", "o2_rtdetr", "fred", "resnet50", "vit_b16"}
    have = {m.get("id") for m in models.get("assets", []) if m.get("license") and m.get("revision") and m.get("sha256") and m.get("local_path") and Path(m["local_path"]).exists()}
    token = "READY_FOR_BC_R011_FINAL_VALIDATION" if gate and need <= have else "ASSET_UNAVAILABLE_R010" if parsed else "INCONCLUSIVE_R010_ASSET_MATERIALIZATION"
    out = {"protocol": "r010-independent-v1", "source_bytes_ok": source_ok, "license_ok": license_ok, "parsed": parsed, "rows": len(rows), "objects": len(feats), "imagery_one_to_one": imagery_ok, "components": len(groups), "split_keys": {k: ["loc:" + ",".join(map(str, g)) for g in (shuffled[:25] if k == "test" else shuffled[25:50] if k == "calibration" else shuffled[50:])] for k in splits}, "support": counts, "data_gate": gate, "model_ids": sorted(x for x in have if x), "token": token}
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
if __name__ == '__main__': main()

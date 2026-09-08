"""Read-only native DOTA v1/v2 image and annotation audit for r025."""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image
from shapely.geometry import Polygon
from shapely.strtree import STRtree


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_quad(points, tol):
    """Cyclic/reversed representation invariant integer key (not an IoU match)."""
    q = [(round(x / tol), round(y / tol)) for x, y in points]
    return min(tuple(v[i:] + v[:i]) for v in (q, q[::-1]) for i in range(4))


def quad_text(points):
    return json.dumps([[x, y] for x, y in points], separators=(",", ":"))


def parse_native(path, version, image_id, tol):
    records = []
    for line_no, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        fields = raw.split()
        if not fields or raw.strip().lower().startswith(("imagesource:", "gsd:", "acquisition date:")):
            continue
        if len(fields) != 10:
            records.append({"version": version, "image_id": image_id, "line": line_no,
                            "raw": raw, "class": fields[8] if len(fields) >= 9 else "",
                            "valid": False, "error": "missing_difficult" if len(fields) == 9 else "invalid_field_count"})
            continue
        try:
            points = [(float(fields[i]), float(fields[i + 1])) for i in range(0, 8, 2)]
            if not all(math.isfinite(v) for point in points for v in point):
                raise ValueError("non-finite coordinate")
            poly = Polygon(points)
        except (ValueError, IndexError):
            records.append({"version": version, "image_id": image_id, "line": line_no,
                            "raw": raw, "valid": False, "error": "non_numeric_quad"})
            continue
        error = None
        if not all(math.isfinite(v) for point in points for v in point):
            error = "non_finite_quad"
        elif not poly.is_valid:
            error = "self_intersection"
        elif poly.area <= 0:
            error = "zero_area"
        if fields[9] not in {"0", "1", "2"}:
            error = "invalid_difficult"
        if error:
            records.append({"version": version, "image_id": image_id, "line": line_no,
                            "raw": raw, "class": fields[8], "difficult": fields[9],
                            "quad": quad_text(points), "valid": False, "error": error})
            continue
        records.append({"version": version, "image_id": image_id, "line": line_no,
                        "raw": raw, "class": fields[8], "difficult": fields[9],
                        "points": points, "quad": quad_text(points),
                        "canonical_quad": json.dumps(canonical_quad(points, tol)),
                        "poly": poly, "area": poly.area, "cx": poly.centroid.x,
                        "cy": poly.centroid.y, "valid": error is None, "error": error or ""})
    return records


def image_record(name, old, new):
    r = {"image_id": name, "v1_path": str(old) if old else "", "v2_path": str(new) if new else ""}
    if not old or not new:
        r["status"] = "missing_version_image"
        return r
    r["v1_sha256"], r["v2_sha256"] = sha(old), sha(new)
    try:
        with Image.open(old) as a, Image.open(new) as b:
            a.load(); b.load()
            r["v1_size"], r["v2_size"] = f"{a.width}x{a.height}", f"{b.width}x{b.height}"
            if a.size != b.size or a.mode != b.mode:
                r["status"] = "decoded_shape_or_mode_diff"
            elif r["v1_sha256"] == r["v2_sha256"]:
                r["status"] = "byte_identical"
            elif a.tobytes() == b.tobytes():
                r["status"] = "pixel_identical_encoding_diff"
            else:
                r["status"] = "pixel_diff"
    except Exception as exc:
        r["status"], r["error"] = "decode_error", type(exc).__name__
    return r


def pair_labels(image_id, old_path, new_path, cfg):
    old = parse_native(old_path, "v1", image_id, cfg["polygon_tolerance"])
    new = parse_native(new_path, "v2", image_id, cfg["polygon_tolerance"])
    valid_old, valid_new = [x for x in old if x["valid"]], [x for x in new if x["valid"]]
    by_old, by_new = defaultdict(list), defaultdict(list)
    for x in valid_old: by_old[x["canonical_quad"]].append(x)
    for x in valid_new: by_new[x["canonical_quad"]].append(x)
    used_old, used_new, rows, edges = set(), set(), [], []

    def row(status, a=None, b=None, iou="", literal=""):
        d = {"image_id": image_id, "status": status, "old_line": a["line"] if a else "",
             "new_line": b["line"] if b else "", "iou": iou, "literal_quad_equal": literal,
             "old_class": a.get("class", "") if a else "", "new_class": b.get("class", "") if b else "",
             "old_difficult": a.get("difficult", "") if a else "", "new_difficult": b.get("difficult", "") if b else "",
             "old_quad": a.get("quad", "") if a else "", "new_quad": b.get("quad", "") if b else "",
             "old_area": a.get("area", "") if a else "", "new_area": b.get("area", "") if b else "",
             "centroid_shift": "", "area_ratio": ""}
        if a and b:
            d["centroid_shift"] = ((a["cx"]-b["cx"])**2 + (a["cy"]-b["cy"])**2)**.5
            d["area_ratio"] = b["area"] / a["area"] if a["area"] else ""
        rows.append(d)

    for key in sorted(set(by_old) | set(by_new)):
        a, b = by_old[key], by_new[key]
        if len(a) == len(b) == 1:
            x, y = a[0], b[0]; used_old.add(x["line"]); used_new.add(y["line"])
            same_meta = (x["class"], x["difficult"]) == (y["class"], y["difficult"])
            row("geometry_unchanged" if same_meta else "class_or_difficult_only", x, y, 1.0, x["quad"] == y["quad"])
        elif len(a) > 1 or len(b) > 1:
            for x in a: used_old.add(x["line"]); row("exact_duplicate_ambiguous", x, None)
            for y in b: used_new.add(y["line"]); row("exact_duplicate_ambiguous", None, y)

    rem_old = [x for x in valid_old if x["line"] not in used_old]
    rem_new = [x for x in valid_new if x["line"] not in used_new]
    graph = defaultdict(list)
    # Spatial lookup only prunes disjoint bounds; the frozen polygon IoU rule is unchanged.
    tree = STRtree([y["poly"] for y in rem_new])
    for x in rem_old:
        for index in sorted(tree.query(x["poly"])):
            y = rem_new[int(index)]
            union = x["poly"].union(y["poly"]).area
            iou = x["poly"].intersection(y["poly"]).area / union if union else 0.0
            if iou >= cfg["iou_threshold"]:
                graph[("old", x["line"])].append((y, iou)); graph[("new", y["line"])].append((x, iou))
                edges.append({"image_id": image_id, "old_line": x["line"], "new_line": y["line"], "iou": iou})
    paired_new = set()
    for x in rem_old:
        c = graph[("old", x["line"])]
        if len(c) == 1 and len(graph[("new", c[0][0]["line"])]) == 1:
            y, iou = c[0]; paired_new.add(y["line"])
            same_meta = (x["class"], x["difficult"]) == (y["class"], y["difficult"])
            row("geometry_revised" if same_meta else "geometry_revised_and_metadata_changed", x, y, iou, False)
        else:
            row("old_iou_ambiguous" if c else "old_no_candidate", x, None)
    for y in rem_new:
        if y["line"] not in paired_new:
            row("new_iou_ambiguous" if graph[("new", y["line"])] else "new_no_candidate", None, y)
    for x in old + new:
        if not x["valid"]:
            row("invalid_geometry_" + x["error"], x if x["version"] == "v1" else None,
                x if x["version"] == "v2" else None)
    counts = {"image_id": image_id, "old_total": len(old), "new_total": len(new),
              "old_invalid": sum(not x["valid"] for x in old), "new_invalid": sum(not x["valid"] for x in new)}
    return old + new, rows, edges, counts


def write_csv(path, rows):
    fields = sorted({key for row in rows for key in row}) or ["empty"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--run-id", choices=["r025", "r026"], default="r025"); args = ap.parse_args()
    root = args.root.resolve(); cfg = json.loads((root / f"configs/{args.run_id}/protocol.json").read_text())
    data, out = Path(cfg["dataset_root"]), root / f"runs/{args.run_id}/artifacts"
    out.mkdir(parents=True, exist_ok=False)
    dirs = {key: data / rel for key, rel in (("i1", cfg["v1_images"]), ("i2", cfg["v2_images"]), ("l1", cfg["v1_labels"]), ("l2", cfg["v2_labels"]))}
    maps = {key: {p.stem: p for p in value.glob("*") if p.is_file()} for key, value in dirs.items()}
    names = sorted(set().union(*[set(x) for x in maps.values()]))
    images = [image_record(name, maps["i1"].get(name), maps["i2"].get(name)) for name in names]
    pairable = {x["image_id"] for x in images if x["status"] in {"byte_identical", "pixel_identical_encoding_diff"}}
    objects, correspondence, edges, counts = [], [], [], []
    for name in sorted(pairable & set(maps["l1"]) & set(maps["l2"])):
        obj, cor, edge, count = pair_labels(name, maps["l1"][name], maps["l2"][name], cfg)
        objects.extend(obj); correspondence.extend(cor); edges.extend(edge); counts.append(count)
    write_csv(out / "image_pairs.csv", images); write_csv(out / "objects.csv", objects)
    write_csv(out / "label_correspondence.csv", correspondence); write_csv(out / "candidate_edges.csv", edges); write_csv(out / "image_object_counts.csv", counts)
    source_rows = []
    for rel in cfg["prediction_paths"]:
        path = root / rel
        source_rows.append({"registered_path": rel, "exists": path.is_file(), "sha256": sha(path) if path.is_file() else None,
                            "purpose": "complete raw prediction or tile-to-mother mapping"})
    metadata = [root.parent / "pth_data/readme.md", root.parent / "pth_data/merge_sources/pth_data_32/readme.md"]
    training = []
    for path in metadata:
        if path.is_file():
            for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                low = line.lower()
                if "dota" in low and ("orcnn" in low or "rtmdet" in low):
                    training.append({"index": str(path), "line": number, "entry": line})
    provenance = {"lookup_scope": [str(root / p) for p in cfg["prediction_paths"]] + [str(p) for p in metadata],
                  "prediction_files": source_rows, "training_index_entries": training,
                  "conclusion": "No AP or label-conditioned prediction claim is permitted unless all complete prediction and mapping inputs are present."}
    (out / "prediction_sources.json").write_text(json.dumps(provenance, indent=2) + "\n")
    focus = [r for r in correspondence if r.get("old_class") in cfg["classes"] or r.get("new_class") in cfg["classes"]]
    literal = sum(r.get("literal_quad_equal") is False and r["status"] in {"geometry_unchanged", "class_or_difficult_only"} for r in correspondence)
    summary = {"all_image_records": len(images), "same_pixel_images": len(pairable), "label_pairs": len(counts),
               "image_status": dict(sorted(Counter(r["status"] for r in images).items())),
               "all_correspondence_status": dict(sorted(Counter(r["status"] for r in correspondence).items())),
               "aircraft_ship_status": dict(sorted(Counter(r["status"] for r in focus).items())),
               "literal_vertex_difference_but_canonical_same": literal,
               "candidate_iou_edges": len(edges), "registered_prediction_files_present": all(x["exists"] for x in source_rows),
               "prediction_complete": None,
               "scope": cfg["scope"]}
    (out / "label_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()

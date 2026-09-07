"""Fetch official MVOI PAN sidecars and training filenames, never imagery pixels."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

BUCKET = "https://spacenet-dataset.s3.amazonaws.com/"
NATIVE = "AOIs/AOI_6_Atlanta/metadata/"
TRAIN = "spacenet/SN4_buildings/train/AOI_6_Atlanta/"


def parse_imd(text: str) -> dict:
    image = re.search(r"BEGIN_GROUP\s*=\s*IMAGE_1\s+(.*?)END_GROUP\s*=\s*IMAGE_1", text, re.S)
    if image is None:
        raise ValueError("missing IMAGE_1")
    fields = {}
    for key, value in re.findall(r"^\s*(\w+)\s*=\s*([^;\n]+);", image.group(1), re.M):
        if key in fields:
            raise ValueError(f"duplicate image field {key}")
        fields[key] = value.strip().strip('"')
    required = ["CatId", "satId", "firstLineTime", "meanCollectedGSD", "meanProductGSD",
                "meanOffNadirViewAngle", "meanSatAz", "meanSatEl", "meanSunAz", "meanSunEl"]
    if not all(k in fields for k in required):
        raise ValueError("missing required native fields")
    corners = {}
    for key, value in re.findall(r"^\s*((?:UL|UR|LR|LL)(?:Lon|Lat))\s*=\s*([^;]+);", text, re.M):
        corners[key] = float(value)
    return {"image_fields": fields, "corners_lon_lat": corners}


def collect(dataset_root: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    asset_root = dataset_root / "SpaceNet4" / "native_metadata"
    asset_root.mkdir(parents=True, exist_ok=True)
    index_path = out / "http_records.json"
    records = json.loads(index_path.read_text()) if index_path.exists() else []
    total = sum(x.get("received_bytes", 0) for x in records)

    def save_records():
        index_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def fetch(url: str, path: Path, limit: int = 1_500_000) -> bytes:
        nonlocal total
        if path.exists():
            data = path.read_bytes()
            binding = next((r for r in reversed(records) if r.get("path") == str(path)
                            and r.get("status") == "saved"), None)
            if binding is None or hashlib.sha256(data).hexdigest() != binding["sha256"]:
                raise ValueError(f"unbound existing file: {path}")
            return data
        record = {"url": url, "path": str(path), "received_bytes": 0, "status": "started"}
        records.append(record)
        save_records()
        parts = []
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                record["http_status"] = response.status
                record["content_length"] = response.headers.get("Content-Length")
                while True:
                    allowance = min(limit - record["received_bytes"], 50_000_000 - total)
                    if allowance <= 0:
                        raise ValueError("bounded metadata budget exhausted")
                    part = response.read(min(65536, allowance))
                    if not part:
                        break
                    parts.append(part)
                    total += len(part)
                    record["received_bytes"] += len(part)
            data = b"".join(parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            record.update(status="saved", sha256=hashlib.sha256(data).hexdigest())
            return data
        except Exception as exc:
            record.update(status="failed", error=str(exc))
            raise
        finally:
            save_records()

    def listing(prefix: str, delimiter: str | None = None):
        page, objects, folders, token = 0, [], [], None
        while True:
            query = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
            if delimiter:
                query["delimiter"] = delimiter
            if token:
                query["continuation-token"] = token
            url = BUCKET + "?" + urllib.parse.urlencode(query)
            key = hashlib.sha256(url.encode()).hexdigest()[:16]
            raw = fetch(url, out / "listings" / f"{key}.xml")
            root = ET.fromstring(raw)
            objects.extend({"key": n.findtext("{*}Key"), "bytes": int(n.findtext("{*}Size"))}
                           for n in root.findall("{*}Contents"))
            folders.extend(n.text for n in root.findall("{*}CommonPrefixes/{*}Prefix"))
            if root.findtext("{*}IsTruncated") == "false":
                return objects, folders
            token = root.findtext("{*}NextContinuationToken")
            page += 1
            if not token or page > 10:
                raise ValueError("unexpected listing pagination")

    _, folders = listing(NATIVE, "/")
    native_folders = {p.rstrip("/").split("/")[-1]: p for p in folders
                      if re.fullmatch(r"103[0-9A-F]{13}", p.rstrip("/").split("/")[-1])}
    _, train_folders = listing(TRAIN, "/")
    train_folders = {p.rstrip("/").rsplit("catid_", 1)[-1]: p for p in train_folders if "catid_" in p}
    native_records, members = [], {}
    for catid in sorted(train_folders):
        if catid not in native_folders:
            raise ValueError(f"no native folder for training source {catid}")
        items, _ = listing(native_folders[catid])
        sidecars = [x for x in items if "_PAN/" in x["key"] and x["key"].endswith((".IMD", ".RPB"))]
        for item in sidecars:
            if item["bytes"] > 200000:
                raise ValueError("unexpected sidecar size")
            key = item["key"]
            path = asset_root / catid / Path(key).name
            raw = fetch(BUCKET + urllib.parse.quote(key, safe="/"), path, 200000)
            if len(raw) != item["bytes"]:
                raise ValueError("sidecar size mismatch")
            if key.endswith(".IMD"):
                parsed = parse_imd(raw.decode("utf-8"))
                if parsed["image_fields"]["CatId"] != catid:
                    raise ValueError("native catalog ID mismatch")
                native_records.append({"catid": catid, "source_key": key, "local_path": str(path),
                                       "sha256": hashlib.sha256(raw).hexdigest(), **parsed})
        images, _ = listing(train_folders[catid] + "PS-RGBNIR/")
        tiles = {}
        for obj in images:
            match = re.search(r"_(\d+)_(\d+)\.tif$", obj["key"])
            if not match:
                raise ValueError("unexpected training member")
            tile = "_".join(match.groups())
            if tile in tiles:
                raise ValueError("duplicate training tile")
            tiles[tile] = obj
        members[catid] = tiles
        print(json.dumps({"catid": catid, "native_imds": sum(r["catid"] == catid for r in native_records),
                          "training_tiles": len(tiles), "bytes_so_far": total}), flush=True)
    label_entries, _ = listing(TRAIN + "geojson_buildings/")
    common = set.intersection(*(set(x) for x in members.values())) if members else set()
    result = {"metadata_prefix": NATIVE, "training_prefix": TRAIN,
              "native_records": native_records, "training_members": members,
              "label_file_names_only": label_entries, "common_training_tiles": sorted(common),
              "downloaded_response_bytes_cumulative": total,
              "scope": "Official PAN IMD/RPB and training filenames only. No imagery or label body downloaded. Native means are strip-level, not per-building calibration."}
    (out / "native_inventory.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"native_imds": len(native_records), "acquisitions": len(members),
                      "common_tiles": len(common), "downloaded_bytes": total}), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    collect(args.dataset_root, args.out)

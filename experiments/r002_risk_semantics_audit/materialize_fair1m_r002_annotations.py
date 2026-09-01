#!/usr/bin/env python3
"""Materialize the archived r002 FAIR1M GT contract into a temporary DOTA tree.

The archived producer stored tile names and rebuilt the annotation from the
source FAIR1M XML: clip each source polygon to its 1024 tile and mark boxes
with less than 70% retained area difficult.  The current dataset split XML
does not carry that difficulty flag, so it must not be used as a replacement
for the frozen r002 label semantics.
"""
from __future__ import annotations

import argparse
import pickle
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, box


TILE = re.compile(r"^(\d+)__1024__(\d+)___(\d+)$")


def source_objects(source: Path, image_id: str) -> list[tuple[str, Polygon]]:
    root = ET.parse(source / f"{image_id}.xml").getroot()
    objects: list[tuple[str, Polygon]] = []
    for obj in root.findall("./objects/object"):
        name = obj.findtext("./possibleresult/name")
        points = [point.text for point in obj.findall("./points/point")][:-1]
        if not name or len(points) != 4:
            continue
        xy: list[float] = []
        for point in points:
            x, y = point.split(",")
            xy.extend((float(x), float(y)))
        polygon = Polygon(np.asarray(xy).reshape(-1, 2))
        if polygon.is_valid and polygon.area > 0:
            objects.append((name, polygon))
    return objects


def materialize_one(args: tuple[str, str, str]) -> int:
    source_text, output_text, tile_name = args
    match = TILE.fullmatch(Path(tile_name).stem)
    if match is None:
        raise ValueError(f"unexpected frozen tile id: {tile_name}")
    image_id, x0, y0 = match.groups()
    x, y = int(x0), int(y0)
    frame = box(x, y, x + 1024, y + 1024)
    lines: list[str] = []
    for name, polygon in source_objects(Path(source_text), image_id):
        clipped = polygon.intersection(frame)
        if clipped.is_empty or clipped.area <= 0:
            continue
        difficult = 0 if clipped.area / polygon.area >= 0.7 else 1
        rect = cv2.minAreaRect(np.asarray(clipped.minimum_rotated_rectangle.exterior.coords[:-1], dtype=np.float32))
        points = cv2.boxPoints(rect)
        points[:, 0] -= x
        points[:, 1] -= y
        lines.append("{} {} {}".format(" ".join(f"{v:.4f}" for v in points.reshape(-1)), name, difficult))
    target = Path(output_text) / f"{Path(tile_name).stem}.txt"
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-xml", required=True, type=Path)
    parser.add_argument("--identity", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=24)
    args = parser.parse_args()
    with args.identity.open("rb") as stream:
        records = pickle.load(stream)
    tile_names = sorted({f"{record['img_id']}.txt" for record in records})
    if len(tile_names) != 4362:
        raise RuntimeError(f"frozen r002 FAIR1M tile universe is {len(tile_names)}, expected 4362")
    args.output.mkdir(parents=True, exist_ok=True)
    jobs = [(str(args.source_xml), str(args.output), name) for name in tile_names]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        counts = list(pool.map(materialize_one, jobs, chunksize=8))
    actual = len(list(args.output.glob("*.txt")))
    if actual != len(tile_names):
        raise RuntimeError(f"wrote {actual} annotations for {len(tile_names)} frozen tiles")
    print({"tiles": actual, "objects": sum(counts), "difficulty_rule": "retained_area>=0.7"})


if __name__ == "__main__":
    main()

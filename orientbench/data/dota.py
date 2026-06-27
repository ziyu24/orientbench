"""DOTA-style annotation parser.

DOTA txt format (one object per line):
    x1 y1 x2 y2 x3 y3 x4 y4 class_name difficult

The 8 coordinates are an (ordered) quadrilateral; conversion to an OBB
(cx,cy,w,h,theta) is done downstream via gt_index.poly8_to_obb so all
datasets share one geometry path (R7).
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def parse_dota_txt(path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse a DOTA annotation .txt. Returns (objects, warnings).

    Each object: {poly: [x1..y4] (8 floats), class_name, difficult}.
    Malformed lines are skipped with a warning rather than raising.
    Leading metadata lines (``imagesource:`` / ``gsd:``) are ignored.
    """
    objects: List[Dict[str, Any]] = []
    warnings: List[str] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as e:
        return [], [f"could not read {path}: {e}"]

    for ln, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("imagesource") or low.startswith("gsd"):
            continue
        parts = line.split()
        if len(parts) < 9:
            warnings.append(f"{path}:{ln}: <9 fields, skipped: {line!r}")
            continue
        try:
            poly = [float(x) for x in parts[:8]]
        except ValueError:
            warnings.append(f"{path}:{ln}: non-numeric polygon, skipped: {line!r}")
            continue
        class_name = parts[8]
        difficult = parts[9] if len(parts) >= 10 else None
        try:
            difficult_val = int(difficult) if difficult is not None else None
        except ValueError:
            difficult_val = None
        objects.append(
            {"poly": poly, "class_name": class_name, "difficult": difficult_val}
        )
    return objects, warnings

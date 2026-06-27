"""DIOR-R OBB annotation parser (PASCAL-VOC-style XML).

Each <object> carries a <robndbox> with the 4 rotated-box corners:
    x_left_top y_left_top x_right_top y_right_top
    x_right_bottom y_right_bottom x_left_bottom y_left_bottom
plus a <name> (class) and <difficult>. An <angle> field exists but the
canonical geometry is taken from the 4 corners (converted to an OBB via the
shared gt_index path) so all datasets are consistent (R7).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Tuple

_CORNER_KEYS = [
    "x_left_top", "y_left_top",
    "x_right_top", "y_right_top",
    "x_right_bottom", "y_right_bottom",
    "x_left_bottom", "y_left_bottom",
]


def parse_dior_obb_xml(path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse a DIOR obb XML. Returns (objects, warnings).

    Each object: {poly:[x1..y4], class_name, difficult, raw_angle}.
    Robust to missing fields: such objects are skipped with a warning.
    """
    objects: List[Dict[str, Any]] = []
    warnings: List[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as e:
        return [], [f"could not parse XML {path}: {e}"]
    root = tree.getroot()

    for obj in root.findall("object"):
        name_el = obj.find("name")
        class_name = name_el.text.strip() if (name_el is not None and name_el.text) else "unknown"
        diff_el = obj.find("difficult")
        try:
            difficult = int(diff_el.text) if (diff_el is not None and diff_el.text) else None
        except (ValueError, AttributeError):
            difficult = None

        rbb = obj.find("robndbox")
        if rbb is None:
            warnings.append(f"{path}: object '{class_name}' has no robndbox, skipped")
            continue
        try:
            coords = [float(rbb.find(k).text) for k in _CORNER_KEYS]
        except (AttributeError, ValueError, TypeError):
            warnings.append(f"{path}: object '{class_name}' robndbox missing/!numeric corners, skipped")
            continue

        angle_el = obj.find("angle")
        try:
            raw_angle = float(angle_el.text) if (angle_el is not None and angle_el.text) else None
        except (ValueError, AttributeError):
            raw_angle = None

        objects.append(
            {"poly": coords, "class_name": class_name,
             "difficult": difficult, "raw_angle": raw_angle}
        )
    return objects, warnings

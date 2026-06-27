"""Focused tests for the Bench-Core-0 data layer (004 task §5).

Covers: DOTA poly8 parsing; poly -> OBB -> HBB -> GV flow; invalid geometry;
missing-annotation tolerance; GT-index schema; --max-files sampling;
unsupported-format recording.
"""
from __future__ import annotations

import math
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.data.dota import parse_dota_txt
from orientbench.data.gt_index import (
    GT_SCHEMA,
    build_gt_index,
    poly8_to_obb,
    resolve_dataset_key,
)
from orientbench.metrics.gv import gv_obliquity

TOL = 1e-6

# An axis-aligned 40x20 rectangle (clockwise) centered at (520, 110).
AXIS_POLY = [500.0, 100.0, 540.0, 100.0, 540.0, 120.0, 500.0, 120.0]


def _make_dota_dataset(root, split="train", n=3, with_bad=True):
    """Create a minimal DOTA split tree under root; returns ann_dir."""
    base = os.path.join(root, "dota", "dota1.0", "split_ss_dota10", split)
    ann = os.path.join(base, "annfiles")
    img = os.path.join(base, "images")
    os.makedirs(ann)
    os.makedirs(img)
    for i in range(n):
        lines = [
            "500.0 100.0 540.0 100.0 540.0 120.0 500.0 120.0 small-vehicle 0",
            "100.0 100.0 130.0 110.0 120.0 140.0 90.0 130.0 ship 1",
        ]
        if with_bad and i == 0:
            lines.append("1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 degenerate 0")  # zero-area
            lines.append("bad line too short")
        with open(os.path.join(ann, f"P{i:04d}.txt"), "w") as fh:
            fh.write("\n".join(lines) + "\n")
        open(os.path.join(img, f"P{i:04d}.png"), "w").close()
    return ann


def test_parse_dota_txt():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "a.txt")
        with open(p, "w") as fh:
            fh.write("imagesource:GoogleEarth\n")
            fh.write("gsd:0.5\n")
            fh.write("500.0 100.0 540.0 100.0 540.0 120.0 500.0 120.0 plane 0\n")
            fh.write("short line\n")
        objs, warns = parse_dota_txt(p)
        assert len(objs) == 1
        assert objs[0]["class_name"] == "plane"
        assert objs[0]["difficult"] == 0
        assert len(objs[0]["poly"]) == 8
        assert any("skipped" in w for w in warns)


def test_poly_to_obb_to_gv_flow():
    obb, warn = poly8_to_obb(AXIS_POLY)
    assert obb is not None
    cx, cy, w, h, theta = obb
    assert abs(cx - 520.0) < 1e-3 and abs(cy - 110.0) < 1e-3
    # sides are 40 and 20 in some order
    assert abs(max(w, h) - 40.0) < 1e-3 and abs(min(w, h) - 20.0) < 1e-3
    # axis-aligned -> GV ratio ~ 1 (HBB ~ OBB)
    g = gv_obliquity(w, h, theta)
    assert abs(g["gv_ratio"] - 1.0) < 1e-3
    assert abs(g["gv_obb_needed"] - 0.0) < 1e-3


def test_poly_to_obb_45deg_gv_half():
    # square rotated 45deg, side 10 -> diagonal corners
    s = 10.0
    poly = [0.0, -s, s, 0.0, 0.0, s, -s, 0.0]  # diamond (45deg square), half-diag s
    obb, _ = poly8_to_obb(poly)
    cx, cy, w, h, theta = obb
    g = gv_obliquity(w, h, theta)
    assert abs(g["gv_ratio"] - 0.5) < 1e-3


def test_poly_to_obb_invalid():
    obb, warn = poly8_to_obb([1.0, 2.0, 3.0])  # wrong length
    assert obb is None and warn is not None
    obb2, _ = poly8_to_obb([float("nan")] * 8)
    assert obb2 is None


def test_resolve_dataset_key():
    assert resolve_dataset_key("DOTA-v1.0") == "dota10"
    assert resolve_dataset_key("dior") == "dior"
    assert resolve_dataset_key("nonsense") is None


def test_build_gt_index_schema_and_validity():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _make_dota_dataset(d, n=3)
        res = build_gt_index("dota10", data_root=d, split="train", max_files=None)
        assert res["supported"] is True
        assert res["stats"]["n_files_ok"] == 3
        # 3 files: file0 has 2 valid + 1 degenerate (+1 unparsable line);
        # files 1,2 have 2 valid each -> 6 valid + 1 invalid geometry
        assert res["stats"]["n_valid_geometry"] == 6
        assert res["stats"]["n_invalid_geometry"] == 1
        rec = res["records"][0]
        # schema completeness
        for field in GT_SCHEMA:
            assert field in rec
        assert rec["angle_unit"] == "rad"
        assert rec["source_format"] == "dota_txt_poly8"


def test_build_gt_index_max_files_sampling():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        _make_dota_dataset(d, n=5, with_bad=False)
        res = build_gt_index("dota10", data_root=d, split="train", max_files=2)
        assert res["stats"]["n_ids_considered"] == 2
        assert res["stats"]["n_files_ok"] == 2


def test_missing_annotation_dir_tolerated():
    res = build_gt_index("dota10", data_root="/no/such/root", split="train", max_files=5)
    assert res["supported"] is True
    assert res["records"] == []
    assert any("missing" in w or "no annotation" in w for w in res["warnings"])


def test_unsupported_dataset_recorded():
    res = build_gt_index("soda-a", data_root="/tmp", split="train")
    assert res["supported"] is False
    assert any("unsupported" in w for w in res["warnings"])


if __name__ == "__main__":
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                passed += 1
                print(f"PASS {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)

import math

import pytest

from orientbench.probes.multiview_geometry_support import (
    angle_distance, enumerate_triplets, ray_distance, validate_rows,
)


LIMITS = {"redundant_azimuth_max_deg": 10, "redundant_ray_max_deg": 5,
          "complementary_angle_min_deg": 60, "complementary_ray_min_deg": 15,
          "candidate_off_nadir_difference_max_deg": 2, "candidate_gsd_ratio_max": 1.05}


def row(key, azimuth, off=25):
    return {"catalog_id": key, "azimuth_deg": azimuth, "off_nadir_deg": off, "gsd_m": 0.5}


def test_directed_opposition_is_not_axial_complementarity():
    assert angle_distance(359, 1) == 2
    assert angle_distance(0, 180, 360) == 180
    assert angle_distance(0, 180, 180) == 0
    rows = [row("a", 0), row("r", 2), row("c", 180)]
    assert enumerate_triplets(rows, LIMITS, 360)
    assert not enumerate_triplets(rows, LIMITS, 180)


def test_near_nadir_azimuth_difference_is_not_a_large_ray_difference():
    rows = [row("a", 0, 1), row("r", 2, 1), row("c", 180, 1)]
    assert ray_distance(rows[0], rows[2]) == pytest.approx(2)
    assert not enumerate_triplets(rows, LIMITS, 360)


def test_rows_are_distinct_real_acquisitions_not_repeated_crops():
    with pytest.raises(ValueError, match="duplicate"):
        validate_rows([row("same", 0), row("same", 90)])
    with pytest.raises(ValueError, match="nonfinite"):
        validate_rows([row("missing", math.nan)])


def test_order_does_not_change_triplets_and_metadata_remains_bound():
    rows = [row("a", 0), row("r", 2), row("c", 90)]
    first = enumerate_triplets(rows, LIMITS, 180)
    assert first == enumerate_triplets(list(reversed(rows)), LIMITS, 180)
    assert any(t["anchor"] == "a" and t["complement"] == "c" for t in first)
    rows[-1]["gsd_m"] = 1.0
    assert not enumerate_triplets(rows, LIMITS, 180)


def test_equal_azimuth_does_not_make_large_off_nadir_change_redundant():
    rows = [row("a", 0, 5), row("r", 0, 40), row("c", 90, 40)]
    assert not any(t["anchor"] == "a" for t in enumerate_triplets(rows, LIMITS, 360))

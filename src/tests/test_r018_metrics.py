import numpy as np
import pytest

from orientbench.r018.metrics import fuse_maps, invert_rotated_prediction, summarise


def test_inverse_tta_preserves_every_row_on_a_non_square_spatial_pattern():
    original = np.arange(35).reshape(5, 7) / 35
    rotated = np.rot90(original)[None]
    aligned = invert_rotated_prediction(rotated)
    np.testing.assert_array_equal(aligned, original)
    np.testing.assert_array_equal(fuse_maps(original, aligned), original)


def test_the_actual_r017_single_row_bug_is_rejected():
    original = np.arange(35).reshape(5, 7) / 35
    q = np.rot90(original)[None]
    wrong = np.rot90(q, -1, axes=(-2, -1))[0, 0]
    assert wrong.shape == (7,)
    with pytest.raises(ValueError, match="broadcasting"):
        fuse_maps(original, wrong)


def test_class_axis_is_not_silently_squeezed():
    with pytest.raises(ValueError, match="B,H,W"):
        invert_rotated_prediction(np.zeros((1, 1, 5, 7)))


def test_block_weighting_and_seed_weighting_are_equal_despite_unequal_tile_counts():
    tiles = ["0_0", "450_0", "2700_0"]
    rows = [{"seed": s, "tile": t, "primary": (2 if s == 1702 else 0) + (10 if t == "2700_0" else 0)}
            for s in (1701, 1702) for t in tiles]
    summary = summarise(rows, tiles)
    assert summary["metric_block_equal"]["primary"] == pytest.approx(6)
    assert summary["seed_block_equal"]["1701"]["primary"] == pytest.approx(5)
    with pytest.raises(ValueError, match="complete unique"):
        summarise(rows[:-1], tiles)


def test_iou_averages_seeds_after_ratios_not_pooled_seed_counts():
    rows = [{"seed": s, "tile": "0_0", "primary": 0,
             "iou_a_intersection": 1, "iou_a_union": 1 if s == 1701 else 9} for s in (1701, 1702)]
    summary = summarise(rows, ["0_0"])
    assert summary["iou"]["a"]["equal_mean"] == pytest.approx((1 + 1 / 9) / 2)
    assert summary["iou"]["a"]["equal_mean"] != pytest.approx(2 / 10)

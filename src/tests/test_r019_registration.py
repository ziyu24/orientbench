import numpy as np
import pytest

from orientbench.r017.measurement import weighted_log_loss
from orientbench.r018.metrics import measure, summarise
from orientbench.r019.registration import loss_surface, paired_change, select_shift, shifted_core


def test_fft_matches_brute_force_every_shift_with_asymmetric_labels_and_edges():
    rng = np.random.default_rng(19)
    p = rng.uniform(size=(9, 11))
    p[0, 0], p[-1, -1] = 0, 1
    y = rng.uniform(size=p.shape) < .27
    valid, margin, pi = np.ones(p.shape, bool), 2, .19
    scores = loss_surface(p, y, valid, pi, margin)
    expected = np.empty((5, 5))
    for iy, dy in enumerate(range(-2, 3)):
        for ix, dx in enumerate(range(-2, 3)):
            expected[iy, ix] = weighted_log_loss(p[2+dy:7+dy, 2+dx:9+dx], y[2:7, 2:9], valid[2:7, 2:9], pi)
    np.testing.assert_allclose(scores, expected, rtol=0, atol=1e-12)


def test_known_displacement_recovered_and_target_never_moves():
    rng = np.random.default_rng(123)
    y = rng.random((13, 15)) < .3
    p = np.full(y.shape, .2)
    # Prediction is located two rows down and one column left of its target.
    p[5:12, 2:11] = np.where(y[3:10, 3:12], .95, .05)
    original = y.copy()
    shift = select_shift(loss_surface(p, y, np.ones_like(y), .3, 3), 3)
    assert (shift["dy"], shift["dx"]) == (2, -1)
    np.testing.assert_array_equal(y, original)
    assert shifted_core(p, 2, -1, 3).shape == shifted_core(y, 0, 0, 3).shape
    assert shift["train_loss_selected"] < shift["train_loss_zero"]


def test_flat_loss_ties_choose_zero_and_boundary_is_reported_without_expansion():
    assert select_shift(np.ones((5, 5)), 2)["dy"] == 0
    assert select_shift(np.ones((5, 5)), 2)["dx"] == 0
    scores = np.ones((5, 5))
    scores[0, 4] = 0
    result = select_shift(scores, 2)
    assert (result["dy"], result["dx"]) == (-2, 2)
    assert result["at_search_boundary"]


def test_out_of_support_cannot_wrap_or_change_masks():
    a = np.arange(81).reshape(9, 9)
    np.testing.assert_array_equal(shifted_core(a, -2, 2, 2), a[:5, 4:])
    with pytest.raises(ValueError, match="outside"):
        shifted_core(a, 3, 0, 2)
    with pytest.raises(ValueError, match="integer"):
        shifted_core(a, .5, 0, 2)
    mask = np.ones((9, 9), bool)
    mask[0, 0] = False
    with pytest.raises(ValueError, match="full valid"):
        loss_surface(np.full((9, 9), .5), np.zeros((9, 9)), mask, .2, 2)


def test_all_background_training_tiles_have_a_defined_loss_and_remain_in_mean():
    y = np.zeros((9, 9), bool)
    scores = loss_surface(np.full(y.shape, .2), y, np.ones_like(y), .1, 2)
    np.testing.assert_allclose(scores, -np.log(.8) / 1.8, atol=1e-14)


def test_contrast_reduction_is_not_confused_with_mean_risk_improvement():
    z = {f"loss_{v}": 1. for v in ("a", "b", "u", "v", "au", "av", "bv", "bu", "a_tta", "b_tta")}
    a = {k: .7 for k in z}
    z["primary"], a["primary"] = .1, .12
    difference = paired_change(z, a)
    assert difference["primary"] == pytest.approx(-.02)
    assert difference["delta_single_risk_improvement"] == pytest.approx(.3)
    assert difference["delta_residual_i"] == pytest.approx(.12)


def test_tta_and_pair_losses_use_complete_shifted_maps_on_identical_targets():
    rng = np.random.default_rng(24)
    p, rotations = rng.random((4, 13, 15)), rng.random((2, 13, 15))
    y = rng.random((13, 15)) < .2
    shifts = [(1, -2), (-2, 1), (0, 2), (2, 0)]
    base = np.stack([shifted_core(p[i], *s, 2) for i, s in enumerate(shifts)])
    rot = np.stack([shifted_core(rotations[i], *s, 2) for i, s in enumerate(shifts[:2])])
    yc, valid = y[2:-2, 2:-2], np.ones((9, 11), bool)
    result = measure(base, rot, yc, valid, .2)
    expected_tta = (p[0, 3:12, :11] + rotations[0, 3:12, :11]) / 2
    assert result["loss_a_tta"] == pytest.approx(weighted_log_loss(expected_tta, yc, valid, .2))
    assert result["loss_av"] == pytest.approx(weighted_log_loss((base[0] + base[3]) / 2, yc, valid, .2))


def test_paired_d_bootstrap_preserves_perfect_cancellation_despite_unequal_blocks():
    tiles = ["0_0", "450_0", "2700_0"]
    # Large individual I variation must cancel before resampling the paired D.
    rows = [{"seed": 1701, "tile": t, "primary": (i * 10 + .125) - i * 10}
            for i, t in enumerate(tiles)]
    result = summarise(rows, tiles, seeds=(1701,))
    assert result["metric_block_equal"]["primary"] == .125
    assert result["intervals_95"]["primary"] == [.125, .125]

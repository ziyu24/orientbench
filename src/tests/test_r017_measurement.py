import numpy as np
import pytest

from orientbench.r017.measurement import crossed_comparison, weighted_log_loss


def test_actual_labels_affect_crossed_logloss():
    p = [np.array([x]) for x in (0.9, 0.2, 0.8, 0.3)]
    positive = crossed_comparison(*p, np.ones(1), np.ones(1, bool), 0.5)
    negative = crossed_comparison(*p, np.zeros(1), np.ones(1, bool), 0.5)
    assert positive['primary'] != pytest.approx(negative['primary'])


def test_probability_fusion_is_not_hard_vote_or_mean_individual_losses():
    actual = weighted_log_loss(np.array([0.5]), np.ones(1), np.ones(1, bool), 0.5)
    assert actual == pytest.approx(np.log(2))
    assert actual != pytest.approx(-0.5 * (np.log(0.9) + np.log(0.1)))


def test_fixed_class_weights_use_pixel_count_not_weight_sum():
    value = weighted_log_loss(np.array([0.5, 0.5]), np.ones(2), np.ones(2, bool), 0.1)
    assert value == pytest.approx(5 * np.log(2))


def test_candidate_exchange_reverses_comparison():
    a, b, u, v = [np.array([x]) for x in (0.9, 0.2, 0.8, 0.3)]
    args = (np.ones(1), np.ones(1, bool), 0.5)
    first = crossed_comparison(a, b, u, v, *args)
    second = crossed_comparison(a, b, v, u, *args)
    assert first['primary'] == pytest.approx(-second['primary'])


def test_empty_common_support_is_not_zero_loss():
    with pytest.raises(ValueError, match='nonempty'):
        weighted_log_loss(np.array([0.5]), np.ones(1), np.zeros(1, bool), 0.5)


def test_invalid_individual_predictions_cannot_cancel_in_fusion():
    with pytest.raises(ValueError, match='each view'):
        crossed_comparison(np.array([1.2]), np.array([1.2]), np.array([-0.2]),
                           np.array([-0.2]), np.ones(1), np.ones(1, bool), 0.5)

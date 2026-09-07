import inspect
import json
from pathlib import Path
import numpy as np
import pytest
from orientbench.r021.forecast import Transport, choose, context, features, block_summary, risk
from orientbench.r021 import run


def example_model():
    geometry = np.array([[0., 0.], [.3, .2]])
    counts = np.zeros((2, 2, 80, 2, 16))
    # Future predictions are accurate on same image and inverted on cross image;
    # label and future-probability marginals are identical in every context.
    for i in range(2):
        for j in range(2):
            counts[i, j, :, 0, 0 if i == j else 15] = 1000
            counts[i, j, :, 1, 15 if i == j else 0] = 1000
    model = Transport(geometry, counts, np.zeros((2, 2)), .5)
    x = np.stack([features(np.full((16, 16), .5), *geometry)] * 3)
    model.fit_ridge(x, np.zeros(3))
    return model


def test_joint_dependence_changes_integrated_risk_with_fixed_marginals():
    model = example_model()
    first, second = model.geometry
    same = model.conditional_risk(first, first, True)
    cross = model.conditional_risk(first, second, False)
    assert np.all(cross > same)
    a = model.conditional_risk(first, first, True, True)
    b = model.conditional_risk(first, second, False, True)
    np.testing.assert_allclose(a, b, atol=1e-14)
    # Compare the tensor integration to an independent explicit loss calculation.
    allowed, w = model.kernel(first, first, True)
    c = np.einsum('i,icyd->cyd', w, model.counts[allowed]) + 32 * model.prior[None]
    d = c[40] / c[40].sum()
    p = (8 + .5) / 16
    expected = sum(d[y, q] * (-np.log((p + (q + .5) / 16) / 2) if y else
                   -np.log(1 - (p + (q + .5) / 16) / 2)) for y in range(2) for q in range(16))
    assert same[40] == pytest.approx(expected)


def test_query_has_no_future_or_label_input_and_ridge_constant_features_work():
    assert list(inspect.signature(Transport.predict).parameters) == ['self', 'p', 'first', 'second']
    model = example_model()
    scores = model.predict(np.full((16, 16), .5), *model.geometry)
    assert scores['transport'] < 0
    assert scores['independence'] == pytest.approx(0)
    assert scores['ridge'] == 0
    assert len(features(np.full((16, 16), .5), *model.geometry)) == 33
    with pytest.raises(ValueError):
        model.predict(np.full((16, 16), np.nan), *model.geometry)


def test_context_is_axial_and_flat_is_separate():
    p = np.tile(np.linspace(.1, .9, 16), (16, 1))
    np.testing.assert_array_equal(context(p, [.3, .1]), context(p, [-.3, -.1]))
    assert np.all(context(np.full((16, 16), .5), [.3, .1]) % 5 == 4)


def test_stop_and_fixed_order_ties():
    assert choose({2: 0., 1: -.2}, 0) == 0
    assert choose({2: .1, 1: .1}, 0) == 2
    with pytest.raises(ValueError):
        choose({1: float('nan')}, 0)


def test_equal_blocks_and_complete_anchor_table():
    tiles = ['0_0', '450_0', '2700_0']
    rows = [{'tile': t, 'anchor': a, 'gain': 1. if t == '2700_0' else 0.} for t in tiles for a in range(4)]
    summary = block_summary(rows, tiles)
    assert summary['means']['gain'] == .5  # not the image-weighted 1/3
    with pytest.raises(ValueError):
        block_summary(rows + [rows[0]], tiles)
    with pytest.raises(ValueError):
        block_summary(rows[:-1], tiles)


def test_manifest_is_double_holdout_and_download_count_is_exact():
    root = Path(__file__).resolve().parents[2]
    m = json.loads((root / 'configs/r021/data_manifest.json').read_text())
    old = json.loads((root / 'configs/r017/data_manifest.json').read_text())
    assert [len(m[s + '_tiles']) for s in ('fit', 'calibration', 'held')] == [128, 64, 64]
    assert not set(m['development_views']) & set(m['held_views'])
    assert set(m['fit_tiles']) <= set(old['training_tiles'])
    assert set(m['calibration_tiles']) <= set(old['calibration_tiles'])
    used = old['training_tiles'] + old['calibration_tiles']
    block = lambda t: tuple(int(v) // 2700 for v in t.split('_'))
    assert not set(map(block, used)) & set(map(block, m['held_tiles']))
    for t in m['held_tiles']:
        for u in used:
            gap = np.maximum(np.abs(np.array(t.split('_'), int) - np.array(u.split('_'), int)) - 450, 0)
            assert np.linalg.norm(gap) >= 450
    assert len(m['images_to_materialize']) == 1024
    assert sum(r['bytes'] for r in m['images_to_materialize']) == 5963320019
    for split, views in (('fit', m['new_development_views']), ('calibration', m['new_development_views']), ('held', m['held_views'])):
        records = [r for r in m['images_to_materialize'] if r['split'] == split]
        assert {(r['tile'], r['view']) for r in records} == {(t, v) for t in m[split + '_tiles'] for v in views}


def test_held_decisions_precede_future_model_and_labels(monkeypatch, tmp_path):
    events = []
    class FakeAssets:
        def acquire_images(self, splits):
            events.append(('images', tuple(splits)))
        def forward(self, splits, seeds):
            events.append(('forward', tuple(splits), tuple(seeds)))
        def acquire_held_labels(self):
            events.append('labels')
        def budget(self):
            pass
        def save_evidence(self):
            return {'new_forward_images': 2048}
    monkeypatch.setattr(run, 'fit_shifts', lambda *a: ([], []))
    monkeypatch.setattr(run, 'fit_forecaster', lambda *a: None)
    monkeypatch.setattr(run, 'calibrate', lambda *a: events.append('calibrate') or 'ridge')
    monkeypatch.setattr(run, 'freeze_decisions', lambda *a: events.append('freeze'))
    monkeypatch.setattr(run, 'measure_held', lambda *a: {'actual_labels': {'intervals_97_5': {'policy_gain': [-1, 1], 'mae_gain': [0, 1]}}})
    m = {'geometry': {'a': {'look_xy': [0, 0]}}, 'development_views': ['a'], 'held_views': ['a'],
         'fit_tiles': [], 'calibration_tiles': [], 'held_tiles': [], 'scope': 'test'}
    run.execute(FakeAssets(), m, {'foreground_fraction': .5}, tmp_path)
    assert events.index('calibrate') < events.index(('images', ('held',)))
    assert events.index(('forward', ('held',), (1701,))) < events.index('freeze')
    assert events.index('freeze') < events.index(('forward', ('held',), (1702,))) < events.index('labels')


def test_two_forward_loss_uses_probability_average():
    p, q, y = np.full((16, 16), .2), np.full((16, 16), .8), np.ones((16, 16), bool)
    assert risk(p, q, y, .5) == pytest.approx(-np.log(.5))


def test_numeric_fit_calibrate_freeze_measure_roundtrip(tmp_path):
    # Exercise real fitting, calibration and disk decision replay with synthetic
    # maps; no network, remote asset or held scientific outcome is accessed.
    geometry = np.array([[.1, .1], [.3, -.2]])
    gy, gx = np.indices((448, 448))
    y = (gx % 28 < 14) & (gy % 28 < 14)
    good = np.where(y, .8, .1).astype(np.float32)
    poor = np.full(y.shape, .35, np.float32)
    p = np.array([[good, poor], [poor, good]])
    class SyntheticAssets:
        def budget(self):
            pass
        def probabilities(self, split, tile, seeds=(1701, 1702)):
            return p[[0 if s == 1701 else 1 for s in seeds]]
        def development_label(self, split, tile):
            return y
        def held_labels(self, tile):
            return y, y
    assets, tiles = SyntheticAssets(), ['0_0', '2700_0']
    shifts, held = run.fit_shifts(assets, tiles, geometry, geometry, tmp_path, .25)
    model = run.fit_forecaster(assets, tiles, geometry, shifts, .25)
    baseline = run.calibrate(assets, tiles, geometry, shifts, model, .25, tmp_path)
    run.freeze_decisions(assets, tiles, geometry, held, model, tmp_path)
    summary = run.measure_held(assets, tiles, geometry, held, baseline, .25, tmp_path)
    assert summary['actual_labels'] == summary['direct448_sensitivity']
    assert summary['actual_labels']['means']['transport_oracle_regret'] >= 0
    with np.load(tmp_path / 'forecaster.npz') as z:
        assert set(z['bias_names']) == set(model.bias)
    assert len(json.loads((tmp_path / 'held_action_outcomes.json').read_text())) == 8

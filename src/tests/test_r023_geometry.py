import copy
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from orientbench.r023.geometry import catalog, render, query_geometry, prepare_manifest, infer
from orientbench.r023.run import read, summarize
from orientbench.r023.verify import reference_worlds


CFG = read(Path(__file__).resolve().parents[2]/'configs/r023/protocol.json')


def test_full_catalog_geometric_identity_without_evaluating_screen():
    hs = catalog(CFG)
    assert hs.shape == (3125, 5)
    reference, target, bits = reference_worlds(CFG, hs)
    assert np.array_equal(render(CFG, hs), reference)
    got_target, got_bits = query_geometry(CFG, hs)
    assert np.array_equal(got_target, target)
    assert np.array_equal(got_bits, bits)


def test_known_ground_and_wall_occlusion():
    hs = np.array([[0, 0, 0, 0, 0], [0, 0, 0, 8, 0], [0, 0, 8, 0, 0]])
    target, bits = query_geometry(CFG, hs)
    assert target[:, 1].tolist() == [0, 0, 8]
    assert bits[:, 1].tolist() == [7, 0, 7]


def test_geometry_only_sampling_is_fixed_and_balanced():
    a = prepare_manifest(CFG)
    assert len(a['records']) == 48
    assert len({r['catalog_id'] for r in a['records']}) == 48
    changed = copy.deepcopy(CFG)
    changed['ground_rgb'] = [99, 77, 55]
    changed['thresholds']['overall'] = 0.99
    assert prepare_manifest(changed) == a


def test_out_of_field_is_not_occlusion():
    changed = copy.deepcopy(CFG)
    changed['queries_xy'] = [[100, 0]]
    with pytest.raises(ValueError, match='field of view'):
        query_geometry(changed, catalog(changed))


def test_oracle_never_intersects_other_query_bits():
    # Three equal images; only one supplied query's bits can filter candidates.
    images = np.zeros((3, 1, 1, 1, 3), dtype=np.uint8)
    targets = np.array([[0, 2], [4, 6], [8, 0]])
    visibility = np.array([[1, 0], [1, 7], [2, 0]], dtype=np.uint8)
    ids, low, high = infer(images, images[0], targets, visibility, 0, 1)
    assert ids == [0, 1] and (low, high) == (0, 4)
    visibility[:, 1] = [7, 0, 3]
    assert infer(images, images[0], targets, visibility, 0, 1) == (ids, low, high)


def test_equal_means_not_mean_relative_reduction():
    cfg = copy.deepcopy(CFG)
    cfg['strata'] = ['one_side_occluded']
    cfg['thresholds'] = {'overall': 0.25}
    rows = [dict(catalog_id=i, stratum='one_side_occluded', base_lo=0, base_hi=w,
                 oracle_lo=0, oracle_hi=v) for i, w, v in [(0, 0, 0), (1, 2, 0), (2, 8, 8)]]
    result = summarize(rows, cfg)
    assert result['metrics']['overall']['shrinkage'] == pytest.approx(0.2)
    assert result['decision'] == 'STOP_THIS_FINITE_THREE_BIT_CANDIDATE'
    for r in rows:
        r['base_hi'] = r['oracle_hi'] = 0
    assert summarize(rows, cfg)['decision'] == 'NO_ROOM_IN_FIXED_DESIGN'

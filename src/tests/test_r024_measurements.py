import copy
from pathlib import Path
import numpy as np
import pytest
from orientbench.r023.geometry import catalog, query_geometry, prepare_manifest
from orientbench.r024.measurement import render_extra, compatible_ids, validate_view_support
from orientbench.r024.run import read, write, canonical_digest, summarize, execute
from orientbench.r024.verify import projected_images, verify


ROOT = Path(__file__).resolve().parents[2]
SCENE = read(ROOT / 'configs/r023/protocol.json')
CFG = read(ROOT / 'configs/r024/protocol.json')


def test_all_candidate_extra_geometry_without_computing_48_scene_outcomes():
    hs = catalog(SCENE)
    targets, _ = query_geometry(SCENE, hs)
    validate_view_support(SCENE, hs, targets, CFG['actions'], CFG['image_v'], 165)
    for a in CFG['actions']:
        assert np.array_equal(render_extra(SCENE, hs, a, CFG['image_v']), projected_images(SCENE, hs, a, CFG['image_v']))


def test_camera_reflection_and_known_signed_projection():
    hs = np.array([[0, 2, 4, 6, 8], [0, 0, 8, 0, 0]])
    positive, negative = CFG['actions'][2:]
    assert np.array_equal(render_extra(SCENE, hs, negative, [0]),
                          render_extra(SCENE, hs[:, ::-1], positive, [0])[:, :, ::-1])
    action = dict(name='fixture', slope=-0.75, u_start=6.75, u_stop=15.25, u_count=3)
    assert np.all(render_extra(SCENE, hs[1:], action, [0]) == SCENE['object_rgb'])
    action.update(u_start=6.5, u_stop=15.5, u_count=2)
    assert np.all(render_extra(SCENE, hs[1:], action, [0]) == SCENE['ground_rgb'])


def test_field_of_view_and_unequal_budget_rejected():
    hs = catalog(SCENE)
    targets, _ = query_geometry(SCENE, hs)
    bad = copy.deepcopy(CFG['actions'])
    bad[-1]['u_stop'] = 10
    with pytest.raises(ValueError, match='field of view'):
        validate_view_support(SCENE, hs, targets, bad, CFG['image_v'], 165)
    bad = copy.deepcopy(CFG['actions'])
    bad[-1]['u_count'] = 34
    with pytest.raises(ValueError, match='sample budget'):
        validate_view_support(SCENE, hs, targets, bad, CFG['image_v'], 165)


def test_image_only_intersection_retains_indistinguishable_worlds():
    base = np.zeros((3, 3, 1, 1, 3), dtype=np.uint8)
    extra = np.array([[[[0, 0, 0]]], [[[0, 0, 0]]], [[[1, 1, 1]]]], dtype=np.uint8)
    assert compatible_ids(base, base[0], extra, extra[0]) == [0, 1]
    perm = [2, 1, 0]
    assert compatible_ids(base[perm], base[0], extra[perm], extra[0]) == [1, 2]
    with pytest.raises(ValueError, match='empty image-compatible'):
        compatible_ids(base, base[0], extra, np.full_like(extra[0], 99))


def test_aggregate_control_is_not_a_per_query_oracle_and_zero_denominator():
    rows = []
    # Complementary controls must be compared as complete arms, not spliced by truth.
    for sid, group in enumerate(SCENE['strata']):
        for q in range(2):
            widths = {'base': 8, 'repeat': 8, 'dither': [0, 8][q], 'same_new': [8, 0][q], 'opposite_new': 2}
            rows.append({'catalog_id': sid, 'stratum': group, 'query': q,
                         'arms': {k: {'lo': 0, 'hi': w, 'visibility_patterns': [0, 7]} for k, w in widths.items()}})
    result = summarize(rows, CFG, SCENE)
    assert result['groups']['overall']['opposite_advantage'] == 0.25
    assert result['decision'] == 'OPPOSITE_VIEW_SCREEN_PASS'
    for r in rows:
        r['arms']['opposite_new']['hi'] = 8
    assert summarize(rows, CFG, SCENE)['decision'] == 'OBSERVABLE_GAIN_WITHOUT_OPPOSITE_ADVANTAGE'
    for r in rows:
        for arm in r['arms'].values():
            arm['hi'] = 8
    assert summarize(rows, CFG, SCENE)['decision'] == 'STOP_FIXED_OBSERVABLE_BRIDGE'
    for r in rows:
        for arm in r['arms'].values():
            arm['hi'] = 0
    assert summarize(rows, CFG, SCENE)['decision'] == 'NO_ROOM_IN_FIXED_DESIGN'


def test_distinct_fixture_full_execution_replay_and_tamper_rejection(tmp_path):
    # Different scene geometry, image grid, and four members; not the scientific cohort.
    scene = copy.deepcopy(SCENE)
    scene.update(box_centers_x=[0, 1, 2, 3, 4], box_width=0.75, height_values=[0, 1, 2, 3],
                 queries_xy=[[2, 0], [2.25, 0]], stratum_query_index=0, boundary_height_min=2,
                 image_u={'start': -8, 'stop': 8, 'count': 9}, image_v=[0], scenes_per_stratum=1)
    cfg = copy.deepcopy(CFG)
    for action, limits in zip(cfg['actions'], [(-8, 8), (-7, 9), (-8, 8), (-4, 12)]):
        action.update(u_start=limits[0], u_stop=limits[1], u_count=9)
    cfg.update(image_v=[0], new_samples_per_action=9)
    manifest = prepare_manifest(scene)
    cfg['base_protocol_sha256_canonical'] = canonical_digest(scene)
    cfg['manifest_sha256_canonical'] = canonical_digest(manifest)
    for task in ['r023', 'r024']:
        (tmp_path / 'configs' / task).mkdir(parents=True)
    write(tmp_path / 'configs/r023/protocol.json', scene)
    write(tmp_path / 'configs/r023/manifest.json', manifest)
    write(tmp_path / 'configs/r024/protocol.json', cfg)
    execute(tmp_path)
    assert verify(tmp_path)['replayed_queries'] == 8
    with pytest.raises(FileExistsError):
        execute(tmp_path)
    path = tmp_path / 'runs/r024/artifacts/query_rows.json'
    rows = read(path)
    rows[0]['arms']['opposite_new']['ids'] = []
    write(path, rows)
    with pytest.raises(ValueError, match='image-compatible sets'):
        verify(tmp_path)


def test_canonical_binding_is_independent_of_checkout_line_endings():
    import json
    assert canonical_digest(json.loads(json.dumps(CFG, indent=2).replace('\n', '\r\n'))) == canonical_digest(CFG)

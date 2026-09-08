"""Independent analytic silhouettes and shadow tests for saved r023 evidence."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np


def reference_worlds(cfg, heights):
    """Project solid rectangles as silhouette intervals; no ray-slab renderer."""
    us = np.linspace(cfg['image_u']['start'], cfg['image_u']['stop'], cfg['image_u']['count'])
    shape = (len(heights), 3, len(cfg['image_v']), len(us), 3)
    images = np.broadcast_to(np.array(cfg['ground_rgb'], dtype=np.uint8), shape).copy()
    half = cfg['box_width']/2
    ymin, ymax = cfg['box_y_bounds']
    for v, slope in enumerate(cfg['camera_slopes_x']):
        for b, center in enumerate(cfg['box_centers_x']):
            # Projection of x in [left,right], z in [0,h]: u in [left-s*h,right].
            for j, y in enumerate(cfg['image_v']):
                if ymin <= y <= ymax:
                    mask = (heights[:, b, None] > 0) & (us >= center-half-slope*heights[:, b, None]) & (us <= center+half)
                    images[:, v, j][mask] = cfg['object_rgb']
    targets = np.zeros((len(heights), len(cfg['queries_xy'])), dtype=np.int16)
    visible = np.full(targets.shape, 7, dtype=np.uint8)
    for q, (x, y) in enumerate(cfg['queries_xy']):
        for b, center in enumerate(cfg['box_centers_x']):
            if center-half <= x <= center+half and ymin <= y <= ymax:
                targets[:, q] = np.maximum(targets[:, q], heights[:, b])
        for v, slope in enumerate(cfg['camera_slopes_x']):
            blocked = np.zeros(len(heights), dtype=bool)
            if ymin <= y <= ymax:
                for b, center in enumerate(cfg['box_centers_x']):
                    # Positive-x camera: higher box casts a closed shadow to its left.
                    blocked |= (heights[:, b] > targets[:, q]) & (center+half > x) & (center-half <= x+slope*(heights[:, b]-targets[:, q]))
            visible[blocked, q] &= np.uint8(7 ^ (1 << v))
    return images, targets, visible


def verify(root):
    out = root/'runs/r023/artifacts'
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    cfg = load(root/'configs/r023/protocol.json')
    members = load(root/'configs/r023/manifest.json')
    if load(out/'protocol.json') != cfg or load(out/'manifest.json') != members:
        raise ValueError('saved scientific inputs differ from Git files')
    for name, digest in load(out/'bindings.json').items():
        if hashlib.sha256((root/'configs/r023'/name).read_bytes()).hexdigest() != digest:
            raise ValueError('input digest mismatch')
    expected = np.array(list(itertools.product(cfg['height_values'], repeat=len(cfg['box_centers_x']))), dtype=np.int16)
    with np.load(out/'candidate_worlds.npz', allow_pickle=False) as z:
        saved = {k: z[k] for k in z.files}
    if not np.array_equal(saved['heights'], expected):
        raise ValueError('candidate world omission or reordering')
    images, targets, visible = reference_worlds(cfg, expected)
    for key, value in [('images', images), ('targets', targets), ('visibility', visible)]:
        if not np.array_equal(saved[key], value):
            raise ValueError(f'independent geometry mismatch: {key}')
    # Check geometry-only stratum selection independently, including all catalog members.
    pools = {s: [] for s in cfg['strata']}
    q0 = cfg['stratum_query_index']
    for sid in range(len(expected)):
        mask, h = int(visible[sid, q0]), int(targets[sid, q0])
        label = ('common_occluded' if mask == 0 else 'one_side_occluded' if mask < 7 else
                 'depth_boundary' if h >= cfg['boundary_height_min'] else 'unoccluded')
        pools[label].append(sid)
    check_records = []
    for label in cfg['strata']:
        chosen = sorted(pools[label], key=lambda i: hashlib.sha256(f"{cfg['seed']}|{label}|{i}".encode()).hexdigest())[:cfg['scenes_per_stratum']]
        check_records.extend({'catalog_id': i, 'heights': expected[i].tolist(), 'stratum': label} for i in chosen)
    if members['records'] != check_records or members['pool_sizes'] != {k: len(v) for k, v in pools.items()}:
        raise ValueError('geometry-only scene selection mismatch')
    with np.load(out/'observations.npz', allow_pickle=False) as z:
        observations = z['images']
    if not np.array_equal(observations, images[[r['catalog_id'] for r in check_records]]):
        raise ValueError('observed images not bound to true scenes')
    rows, sets = load(out/'query_rows.json'), load(out/'compatible_sets.json')
    nq = len(cfg['queries_xy'])
    if len(rows) != len(check_records)*nq or len(sets) != len(rows):
        raise ValueError('query denominator mismatch')
    expected_rows = []
    for member, observation in zip(check_records, observations):
        sid = member['catalog_id']
        base = [i for i in range(len(expected)) if np.array_equal(images[i], observation)]
        for q in range(nq):
            oracle = [i for i in base if visible[i, q] == visible[sid, q]]
            if sid not in base or sid not in oracle:
                raise ValueError('truth omitted')
            vals, ovals = targets[base, q], targets[oracle, q]
            row = {'catalog_id': sid, 'stratum': member['stratum'], 'query': q, 'truth_height': int(targets[sid, q]),
                   'oracle_bits': int(visible[sid, q]), 'base_lo': int(min(vals)), 'base_hi': int(max(vals)),
                   'oracle_lo': int(min(ovals)), 'oracle_hi': int(max(ovals)), 'base_count': len(base), 'oracle_count': len(oracle)}
            j = len(expected_rows)
            if rows[j] != row or sets[j] != {'catalog_id': sid, 'query': q, 'base_ids': base, 'oracle_ids': oracle}:
                raise ValueError('compatible set or bound differs from independent replay')
            expected_rows.append(row)
    result = load(out/'summary.json')
    for label in ['overall']+cfg['strata']:
        selected = [r for r in expected_rows if label == 'overall' or r['stratum'] == label]
        by_scene = {}
        for row in selected:
            by_scene.setdefault(row['catalog_id'], []).append(row)
        b = sum(sum(r['base_hi']-r['base_lo'] for r in values)/len(values) for values in by_scene.values())/len(by_scene)
        v = sum(sum(r['oracle_hi']-r['oracle_lo'] for r in values)/len(values) for values in by_scene.values())/len(by_scene)
        s = None if b == 0 else 1-v/b
        metrics = result['metrics'][label]
        expected_metrics = {'scenes': len(by_scene), 'queries': len(selected), 'base_mean_width': b, 'oracle_mean_width': v,
                            'shrinkage': s, 'zero_base_width_queries': sum(r['base_hi'] == r['base_lo'] for r in selected),
                            'full_height_range_queries': sum(r['base_hi']-r['base_lo'] == max(cfg['height_values']) for r in selected)}
        if metrics != expected_metrics:
            raise ValueError('aggregate replay mismatch')
    overall = result['metrics']['overall']['shrinkage']
    passed = all(result['metrics'][k]['shrinkage'] is not None and result['metrics'][k]['shrinkage'] >= t for k, t in cfg['thresholds'].items())
    verdict = 'NO_ROOM_IN_FIXED_DESIGN' if overall is None else 'FINITE_PRIVILEGED_INFORMATION_SCREEN_PASS' if passed else 'STOP_THIS_FINITE_THREE_BIT_CANDIDATE'
    if result['decision'] != verdict or any(result[k] != 0 for k in ('truth_omissions', 'empty_sets', 'monotonicity_violations')):
        raise ValueError('verdict or validity mismatch')
    if any(not r['base_lo'] <= r['oracle_lo'] <= r['truth_height'] <= r['oracle_hi'] <= r['base_hi'] for r in expected_rows):
        raise ValueError('non-nested or truth-excluding interval')
    report = {'geometry_recomputed_worlds': len(expected), 'replayed_scenes': len(check_records),
              'replayed_queries': len(rows), 'decision': verdict, 'all_checks_passed': True}
    (out/'verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    verify(p.parse_args().root.resolve())

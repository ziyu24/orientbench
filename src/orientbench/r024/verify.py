"""Independent projected intervals, byte matching and Python-sum replay for r024."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
from orientbench.r023.verify import reference_worlds


def projected_images(scene, heights, action, ys):
    """Analytic projected cuboid intervals, independent of production ray slabs."""
    us = np.linspace(action['u_start'], action['u_stop'], action['u_count'])
    shape = (len(heights), len(ys), len(us), 3)
    result = np.broadcast_to(np.array(scene['ground_rgb'], dtype=np.uint8), shape).copy()
    half, slope = scene['box_width'] / 2, action['slope']
    for i, hs in enumerate(heights):
        for center, h in zip(scene['box_centers_x'], hs):
            if h == 0:
                continue
            corners = [x - slope * z for x in (center - half, center + half) for z in (0, h)]
            for j, y in enumerate(ys):
                if scene['box_y_bounds'][0] <= y <= scene['box_y_bounds'][1]:
                    result[i, j, (us >= min(corners)) & (us <= max(corners))] = scene['object_rgb']
    return result


def verify(root):
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    cfg = read(root / 'configs/r024/protocol.json')
    scene = read(root / 'configs/r023/protocol.json')
    manifest = read(root / 'configs/r023/manifest.json')
    out = root / 'runs/r024/artifacts'
    if read(out / 'inputs.json') != {'protocol': cfg, 'scene': scene, 'manifest': manifest}:
        raise ValueError('saved inputs differ from Git scientific inputs')
    for obj, key in [(scene, 'base_protocol_sha256_canonical'), (manifest, 'manifest_sha256_canonical')]:
        digest = hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        if cfg[key] != digest:
            raise ValueError('inherited input digest mismatch')
    heights = np.array(list(itertools.product(scene['height_values'], repeat=len(scene['box_centers_x']))), dtype=np.int16)
    base, targets, visibility = reference_worlds(scene, heights)
    pools = {label: [] for label in scene['strata']}
    for sid in range(len(heights)):
        v, h = int(visibility[sid, scene['stratum_query_index']]), int(targets[sid, scene['stratum_query_index']])
        label = 'common_occluded' if v == 0 else 'one_side_occluded' if v < 7 else 'depth_boundary' if h >= scene['boundary_height_min'] else 'unoccluded'
        pools[label].append(sid)
    members = []
    for label, ids in pools.items():
        chosen = sorted(ids, key=lambda sid: hashlib.sha256(f"{scene['seed']}|{label}|{sid}".encode()).hexdigest())[:scene['scenes_per_stratum']]
        members.extend({'catalog_id': sid, 'heights': heights[sid].tolist(), 'stratum': label} for sid in chosen)
    if manifest != {'task': scene['task'], 'catalog_size': len(heights), 'pool_sizes': {k: len(v) for k, v in pools.items()}, 'records': members}:
        raise ValueError('original cohort replay mismatch')
    if cfg['seed'] != scene['seed']:
        raise ValueError('seed identity mismatch')
    # Independent all-hypothesis field-of-view and equal-sample checks.
    for action in cfg['actions']:
        if action['u_count'] * len(cfg['image_v']) != cfg['new_samples_per_action']:
            raise ValueError('unequal sample budgets')
        slope = action['slope']
        for q, (x, y) in enumerate(scene['queries_xy']):
            for h in set(targets[:, q].tolist()):
                if not (action['u_start'] <= x - slope * h <= action['u_stop'] and min(cfg['image_v']) <= y <= max(cfg['image_v'])):
                    raise ValueError('query field-of-view mismatch')
        for center in scene['box_centers_x']:
            corners = [x - slope * z for x in (center - scene['box_width']/2, center + scene['box_width']/2)
                       for z in (0, max(scene['height_values']))]
            if min(corners) < action['u_start'] or max(corners) > action['u_stop']:
                raise ValueError('object field-of-view mismatch')
    extra = np.stack([projected_images(scene, heights, a, cfg['image_v']) for a in cfg['actions']], axis=1)
    with np.load(out / 'worlds.npz', allow_pickle=False) as z:
        for name, value in [('heights', heights), ('targets', targets), ('visibility', visibility), ('base_images', base), ('extra_images', extra)]:
            if not np.array_equal(z[name], value):
                raise ValueError(f'world geometry mismatch: {name}')
    true_ids = [m['catalog_id'] for m in members]
    with np.load(out / 'observations.npz', allow_pickle=False) as z:
        if not np.array_equal(z['base_images'], base[true_ids]) or not np.array_equal(z['extra_images'], extra[true_ids]):
            raise ValueError('observations not bound to source worlds')
    expected_rows = []
    for m in members:
        sid = m['catalog_id']
        base_ids = [i for i in range(len(heights)) if np.array_equal(base[i], base[sid])]
        sets = {'base': base_ids}
        for a, action in enumerate(cfg['actions']):
            sets[action['name']] = [i for i in base_ids if np.array_equal(extra[i, a], extra[sid, a])]
        if sets['repeat'] != base_ids:
            raise ValueError('repeat control differs from baseline')
        for q in range(targets.shape[1]):
            arms = {}
            for name, ids in sets.items():
                if sid not in ids or not set(ids).issubset(base_ids):
                    raise ValueError('truth omission or expanded set')
                arms[name] = {'ids': ids, 'lo': min(int(targets[i, q]) for i in ids),
                              'hi': max(int(targets[i, q]) for i in ids),
                              'visibility_patterns': sorted({int(visibility[i, q]) for i in ids})}
            expected_rows.append({'catalog_id': sid, 'stratum': m['stratum'], 'query': q,
                                  'truth_height': int(targets[sid, q]), 'arms': arms})
    if read(out / 'query_rows.json') != expected_rows:
        raise ValueError('image-compatible sets or query bounds differ from replay')
    summary = read(out / 'summary.json')
    groups = {}
    names = ['base'] + [a['name'] for a in cfg['actions']]
    for label in ['overall'] + scene['strata']:
        rows = [r for r in expected_rows if label == 'overall' or r['stratum'] == label]
        by_scene = {}
        for r in rows:
            by_scene.setdefault(r['catalog_id'], []).append(r)
        widths = {name: sum(sum(r['arms'][name]['hi'] - r['arms'][name]['lo'] for r in rs) / len(rs)
                            for rs in by_scene.values()) / len(by_scene) for name in names}
        arms = {}
        b = widths['base']
        for name in names:
            values = [r['arms'][name] for r in rows]
            arms[name] = {'mean_width': widths[name], 'shrinkage': None if b == 0 else 1 - widths[name] / b,
                          'zero_width_queries': sum(v['hi'] == v['lo'] for v in values),
                          'full_range_queries': sum(v['hi'] - v['lo'] == max(scene['height_values']) for v in values),
                          'visibility_identified_queries': sum(len(v['visibility_patterns']) == 1 for v in values)}
        best_same = min(widths[name] for name in cfg['same_side_controls'])
        groups[label] = {'scenes': len(by_scene), 'queries': len(rows), 'arms': arms,
                         'opposite_advantage': None if b == 0 else (best_same - widths[cfg['target_action']]) / b}
    if summary['groups'] != groups:
        raise ValueError('independent aggregate mismatch')
    t = cfg['thresholds']
    eligible = []
    for name in names[1:]:
        values = [groups[g]['arms'][name]['shrinkage'] for g in ['overall'] + cfg['required_subgroups']]
        thresholds = [t['overall_shrinkage_min']] + [t['subgroup_shrinkage_min']] * len(cfg['required_subgroups'])
        if all(v is not None and v >= threshold for v, threshold in zip(values, thresholds)):
            eligible.append(name)
    advantages = [groups[g]['opposite_advantage'] for g in ['overall'] + cfg['required_subgroups']]
    thresholds = [t['opposite_advantage_over_best_same_min']] + [t['opposite_subgroup_advantage_min']] * len(cfg['required_subgroups'])
    if groups['overall']['arms']['base']['mean_width'] == 0:
        decision = 'NO_ROOM_IN_FIXED_DESIGN'
    elif cfg['target_action'] in eligible and all(v is not None and v >= t for v, t in zip(advantages, thresholds)):
        decision = 'OPPOSITE_VIEW_SCREEN_PASS'
    elif eligible:
        decision = 'OBSERVABLE_GAIN_WITHOUT_OPPOSITE_ADVANTAGE'
    else:
        decision = 'STOP_FIXED_OBSERVABLE_BRIDGE'
    expected_fields = {'decision': decision, 'arms_passing_absolute_screen': eligible, 'automatic_training_authorized': False,
                       'scope': cfg['scope'], 'cohort': cfg['cohort'], 'candidate_scenes': len(heights),
                       'evaluation_scenes': len(members), 'queries': len(expected_rows), 'truth_omissions': 0,
                       'empty_sets': 0, 'monotonicity_violations': 0, 'repeat_control_violations': 0,
                       'new_samples_per_scene_per_arm': cfg['new_samples_per_action']}
    if any(summary[k] != v for k, v in expected_fields.items()):
        raise ValueError('verdict or metadata replay mismatch')
    report = {'all_checks_passed': True, 'geometry_recomputed_worlds': len(heights), 'replayed_scenes': len(members),
              'replayed_queries': len(expected_rows), 'replayed_actions': len(cfg['actions']), 'decision': decision}
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    verify(parser.parse_args().root.resolve())

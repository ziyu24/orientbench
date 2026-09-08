"""Execute the frozen, image-only r024 comparison; no training or action fitting."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from orientbench.r023.geometry import catalog, render, query_geometry, prepare_manifest
from orientbench.r024.measurement import render_extra, validate_view_support, compatible_ids


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def inputs(root):
    protocol = read(root / 'configs/r024/protocol.json')
    scene = read(root / 'configs/r023/protocol.json')
    manifest = read(root / 'configs/r023/manifest.json')
    if protocol['task'] != 'r024' or scene['noise_linf'] != 0 or protocol['seed'] != scene['seed']:
        raise ValueError('only frozen r024 noiseless comparison is supported')
    if canonical_digest(scene) != protocol['base_protocol_sha256_canonical'] or canonical_digest(manifest) != protocol['manifest_sha256_canonical']:
        raise ValueError('inherited scientific input changed')
    if manifest != prepare_manifest(scene):
        raise ValueError('original geometry-only cohort changed')
    names = [a['name'] for a in protocol['actions']]
    if names != ['repeat', 'dither', 'same_new', 'opposite_new']:
        raise ValueError('frozen arm identity changed')
    return protocol, scene, manifest


def describe(ids, targets, visibility, q):
    return {'ids': ids, 'lo': int(targets[ids, q].min()), 'hi': int(targets[ids, q].max()),
            'visibility_patterns': sorted(int(v) for v in np.unique(visibility[ids, q]))}


def summarize(rows, protocol, scene):
    names = ['base'] + [a['name'] for a in protocol['actions']]
    groups = {}
    for label in ['overall'] + scene['strata']:
        selected = [r for r in rows if label == 'overall' or r['stratum'] == label]
        ids = sorted({r['catalog_id'] for r in selected})
        widths = {name: float(np.mean([
            np.mean([r['arms'][name]['hi'] - r['arms'][name]['lo'] for r in selected if r['catalog_id'] == sid])
            for sid in ids])) for name in names}
        b = widths['base']
        arms = {}
        for name in names:
            records = [r['arms'][name] for r in selected]
            arms[name] = {'mean_width': widths[name], 'shrinkage': None if b == 0 else 1 - widths[name] / b,
                          'zero_width_queries': sum(r['hi'] == r['lo'] for r in records),
                          'full_range_queries': sum(r['hi'] - r['lo'] == max(scene['height_values']) for r in records),
                          'visibility_identified_queries': sum(len(r['visibility_patterns']) == 1 for r in records)}
        best_same = min(widths[name] for name in protocol['same_side_controls'])
        groups[label] = {'scenes': len(ids), 'queries': len(selected), 'arms': arms,
                         'opposite_advantage': None if b == 0 else (best_same - widths[protocol['target_action']]) / b}
    t = protocol['thresholds']
    required = protocol['required_subgroups']
    eligible = [name for name in names[1:] if all(
        groups[g]['arms'][name]['shrinkage'] is not None and groups[g]['arms'][name]['shrinkage'] >= threshold
        for g, threshold in [('overall', t['overall_shrinkage_min'])] + [(g, t['subgroup_shrinkage_min']) for g in required])]
    opposite = protocol['target_action']
    if groups['overall']['arms']['base']['mean_width'] == 0:
        decision = 'NO_ROOM_IN_FIXED_DESIGN'
    elif opposite in eligible and all(groups[g]['opposite_advantage'] is not None and groups[g]['opposite_advantage'] >= threshold
                                     for g, threshold in [('overall', t['opposite_advantage_over_best_same_min'])] +
                                     [(g, t['opposite_subgroup_advantage_min']) for g in required]):
        decision = 'OPPOSITE_VIEW_SCREEN_PASS'
    elif eligible:
        decision = 'OBSERVABLE_GAIN_WITHOUT_OPPOSITE_ADVANTAGE'
    else:
        decision = 'STOP_FIXED_OBSERVABLE_BRIDGE'
    return {'decision': decision, 'groups': groups, 'arms_passing_absolute_screen': eligible,
            'automatic_training_authorized': False, 'scope': protocol['scope'], 'cohort': protocol['cohort']}


def execute(root):
    started = time.monotonic()
    protocol, scene, manifest = inputs(root)
    heights = catalog(scene)
    targets, visibility = query_geometry(scene, heights)
    validate_view_support(scene, heights, targets, protocol['actions'], protocol['image_v'], protocol['new_samples_per_action'])
    out = root / 'runs/r024/artifacts'
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'inputs.json', {'protocol': protocol, 'scene': scene, 'manifest': manifest})
    base_images = render(scene, heights)
    extra = np.stack([render_extra(scene, heights, a, protocol['image_v']) for a in protocol['actions']], axis=1)
    repeat_index = scene['camera_slopes_x'].index(protocol['actions'][0]['slope'])
    if not np.array_equal(extra[:, 0], base_images[:, repeat_index]):
        raise ValueError('repeat control is not an exact repeated image')
    np.savez_compressed(out / 'worlds.npz', heights=heights, targets=targets, visibility=visibility,
                        base_images=base_images, extra_images=extra)
    true_ids = [m['catalog_id'] for m in manifest['records']]
    base_obs, extra_obs = base_images[true_ids].copy(), extra[true_ids].copy()
    np.savez_compressed(out / 'observations.npz', base_images=base_obs, extra_images=extra_obs)
    rows = []
    for m, obs, observations in zip(manifest['records'], base_obs, extra_obs):
        if time.monotonic() - started > protocol['cpu_wall_seconds_limit']:
            raise RuntimeError('CPU budget exceeded; incomplete, no scientific verdict')
        # Inference receives image evidence only. True ID is used below solely for evaluation.
        base_ids = np.flatnonzero(np.all(base_images == obs, axis=(1, 2, 3, 4))).tolist()
        sets = {'base': base_ids}
        for a, action in enumerate(protocol['actions']):
            sets[action['name']] = compatible_ids(base_images, obs, extra[:, a], observations[a])
        if sets['repeat'] != base_ids:
            raise ValueError('repeat control changed the feasible set')
        for q in range(targets.shape[1]):
            arms = {name: describe(ids, targets, visibility, q) for name, ids in sets.items()}
            truth = int(targets[m['catalog_id'], q])
            for arm in arms.values():
                if m['catalog_id'] not in arm['ids'] or not (arms['base']['lo'] <= arm['lo'] <= truth <= arm['hi'] <= arms['base']['hi']):
                    raise ValueError('truth omission or non-nested bound')
            rows.append({'catalog_id': m['catalog_id'], 'stratum': m['stratum'], 'query': q,
                         'truth_height': truth, 'arms': arms})
    write(out / 'query_rows.json', rows)
    summary = summarize(rows, protocol, scene)
    summary.update(candidate_scenes=len(heights), evaluation_scenes=len(true_ids), queries=len(rows),
                   truth_omissions=0, empty_sets=0, monotonicity_violations=0, repeat_control_violations=0,
                   new_samples_per_scene_per_arm=protocol['new_samples_per_action'], wall_seconds=time.monotonic() - started)
    write(out / 'summary.json', summary)
    total = sum(p.stat().st_size for p in out.iterdir() if p.is_file())
    if total > protocol['artifact_bytes_limit']:
        raise RuntimeError('artifact budget exceeded')
    print(json.dumps({'decision': summary['decision'], 'bytes': total}))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    execute(parser.parse_args().root.resolve())

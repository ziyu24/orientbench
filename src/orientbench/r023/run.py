"""Run the single frozen CPU screen and preserve full finite evidence."""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from orientbench.r023.geometry import catalog, render, query_geometry, prepare_manifest, infer


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def summarize(rows, cfg):
    groups = {'overall': rows}
    groups.update({g: [r for r in rows if r['stratum'] == g] for g in cfg['strata']})
    metrics = {}
    for label, items in groups.items():
        scene_ids = sorted({r['catalog_id'] for r in items})
        base, oracle = [], []
        for sid in scene_ids:
            scene = [r for r in items if r['catalog_id'] == sid]
            base.append(np.mean([r['base_hi']-r['base_lo'] for r in scene]))
            oracle.append(np.mean([r['oracle_hi']-r['oracle_lo'] for r in scene]))
        b, v = float(np.mean(base)), float(np.mean(oracle))
        metrics[label] = {'scenes': len(scene_ids), 'queries': len(items), 'base_mean_width': b, 'oracle_mean_width': v,
                          'shrinkage': None if b == 0 else 1-v/b,
                          'zero_base_width_queries': sum(r['base_hi'] == r['base_lo'] for r in items),
                          'full_height_range_queries': sum(r['base_hi']-r['base_lo'] == max(cfg['height_values']) for r in items)}
    if metrics['overall']['shrinkage'] is None:
        decision = 'NO_ROOM_IN_FIXED_DESIGN'
    elif all(metrics[k]['shrinkage'] is not None and metrics[k]['shrinkage'] >= value for k, value in cfg['thresholds'].items()):
        decision = 'FINITE_PRIVILEGED_INFORMATION_SCREEN_PASS'
    else:
        decision = 'STOP_THIS_FINITE_THREE_BIT_CANDIDATE'
    return {'decision': decision, 'metrics': metrics, 'scope': cfg['scope'], 'automatic_training_authorized': False}


def execute(root, protocol, manifest):
    start = time.monotonic()
    cfg, members = read(protocol), read(manifest)
    if cfg['noise_linf'] != 0 or cfg['task'] != 'r023':
        raise ValueError('only the frozen r023 noiseless model is implemented')
    if members != prepare_manifest(cfg):
        raise ValueError('frozen scene manifest mismatch')
    out = root/'runs/r023/artifacts'
    out.mkdir(parents=True, exist_ok=False)
    write(out/'protocol.json', cfg)
    write(out/'manifest.json', members)
    write(out/'bindings.json', {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (protocol, manifest)})
    heights = catalog(cfg)
    images = render(cfg, heights)
    targets, visibility = query_geometry(cfg, heights)
    np.savez_compressed(out/'candidate_worlds.npz', heights=heights, images=images, targets=targets, visibility=visibility)
    observations = images[[r['catalog_id'] for r in members['records']]].copy()
    np.savez_compressed(out/'observations.npz', images=observations)
    rows, sets = [], []
    for member, observation in zip(members['records'], observations):
        if time.monotonic()-start > cfg['cpu_wall_seconds_limit']:
            raise RuntimeError('CPU time budget exceeded; no scientific conclusion')
        sid = member['catalog_id']
        for q in range(targets.shape[1]):
            base, lo, hi = infer(images, observation, targets, visibility, q)
            vb = int(visibility[sid, q])
            oracle, vlo, vhi = infer(images, observation, targets, visibility, q, vb)
            truth = int(targets[sid, q])
            if sid not in base or sid not in oracle or not (lo <= vlo <= truth <= vhi <= hi):
                raise ValueError('truth retention or nested-bound violation')
            rows.append({'catalog_id': sid, 'stratum': member['stratum'], 'query': q, 'truth_height': truth,
                         'oracle_bits': vb, 'base_lo': lo, 'base_hi': hi, 'oracle_lo': vlo, 'oracle_hi': vhi,
                         'base_count': len(base), 'oracle_count': len(oracle)})
            sets.append({'catalog_id': sid, 'query': q, 'base_ids': base, 'oracle_ids': oracle})
    write(out/'query_rows.json', rows)
    write(out/'compatible_sets.json', sets)
    result = summarize(rows, cfg)
    result.update({'truth_omissions': 0, 'empty_sets': 0, 'monotonicity_violations': 0,
                   'wall_seconds': time.monotonic()-start, 'candidate_scenes': len(heights), 'evaluation_scenes': len(members['records'])})
    write(out/'summary.json', result)
    total = sum(p.stat().st_size for p in out.iterdir() if p.is_file())
    if total > cfg['artifact_bytes_limit']:
        raise RuntimeError('artifact budget exceeded')
    print(json.dumps({'artifacts': str(out), 'decision': result['decision'], 'bytes': total}))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    args = p.parse_args()
    root = args.root.resolve()
    execute(root, root/'configs/r023/protocol.json', root/'configs/r023/manifest.json')


if __name__ == '__main__':
    main()

"""Fit and freeze acquisition-gain forecasts, then measure the double holdout."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

from orientbench.r018.evaluate import read, write, digest
from orientbench.r019.registration import loss_surface, select_shift, shifted_core
from orientbench.r021.data import Assets
from orientbench.r021.forecast import Transport, joint_counts, risk, features, choose, evaluate_policies, block_summary

METHODS = ('transport', 'independence', 'geometry', 'ridge')
BASELINES = ('stop', 'max_separation', 'near_nadir', 'geometry', 'ridge')


def align(p, shifts):
    return np.stack([shifted_core(v, s['dy'], s['dx'], 32) for v, s in zip(p, shifts)])


def fit_shifts(assets, tiles, geometry, held_geometry, out, pi):
    surfaces = np.zeros((2, len(geometry), 65, 65))
    for index, tile in enumerate(tiles):
        assets.budget()
        p, y = assets.probabilities('fit', tile), assets.development_label('fit', tile)
        for s in range(2):
            for v in range(len(geometry)):
                surfaces[s, v] += loss_surface(p[s, v], y, np.ones(y.shape, bool), pi, 32) / len(tiles)
        if (index + 1) % 16 == 0:
            print(f'Fit shift surfaces: {index + 1}/{len(tiles)}', flush=True)
    shifts = [[select_shift(v, 32) for v in s] for s in surfaces]
    direct = np.zeros((2, len(geometry), 2))
    for tile in tiles:
        assets.budget()
        p, y = assets.probabilities('fit', tile), assets.development_label('fit', tile)[32:-32, 32:-32]
        for s in range(2):
            for v, shift in enumerate(shifts[s]):
                for k, (dy, dx) in enumerate(((0, 0), (shift['dy'], shift['dx']))):
                    q = shifted_core(p[s, v], dy, dx, 32)
                    direct[s, v, k] += risk(q, q, y, pi) / len(tiles)
    expected = np.array([[[v['train_loss_zero'], v['train_loss_selected']] for v in s] for s in shifts])
    error = float(np.max(np.abs(direct - expected)))
    if error > 1e-10:
        raise ValueError('training FFT/direct verification failed')
    nearest = [int(np.argmin(np.sum((geometry - g) ** 2, axis=1))) for g in held_geometry]
    transferred = [[s[j] for j in nearest] for s in shifts]
    np.savez_compressed(out / 'training_loss_surfaces.npz', surfaces=surfaces, direct=direct)
    write(out / 'frozen_shifts.json', {'development': shifts, 'held': transferred,
        'nearest_development_indices': nearest, 'fft_direct_max_error': error,
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'convention': 'q[y,x]=p[y+dy,x+dx]; held shifts transferred by nominal geometry without held outcomes'})
    return shifts, transferred


def fit_forecaster(assets, tiles, geometry, shifts, pi):
    n = len(geometry)
    counts, pair_risk = np.zeros((n, n, 80, 2, 16)), np.zeros((n, n))
    x, target = [], []
    for index, tile in enumerate(tiles):
        assets.budget()
        raw = assets.probabilities('fit', tile)
        first, second = [align(raw[s], shifts[s]) for s in range(2)]
        y = assets.development_label('fit', tile)[32:-32, 32:-32]
        costs = np.array([[risk(a, b, y, pi, sampled=True) for b in second] for a in first])
        pair_risk += costs / len(tiles)
        for i in range(n):
            for j in range(n):
                counts[i, j] += joint_counts(first[i], second[j], y, geometry[j])
                if i != j:
                    x.append(features(first[i], geometry[i], geometry[j]))
                    target.append(costs[i, i] - costs[i, j])
        if (index + 1) % 16 == 0:
            print(f'Fit conditional distribution: {index + 1}/{len(tiles)}', flush=True)
    model = Transport(geometry, counts, pair_risk, pi)
    model.fit_ridge(x, target)
    return model


def forecasts(model, p, geometry, anchor):
    return {j: model.predict(p, geometry[anchor], geometry[j]) for j in range(len(geometry)) if j != anchor}


def calibrate(assets, tiles, geometry, shifts, model, pi, out):
    records = []
    for tile in tiles:
        assets.budget()
        raw = assets.probabilities('calibration', tile)
        first, second = [align(raw[s], shifts[s]) for s in range(2)]
        y = assets.development_label('calibration', tile)[32:-32, 32:-32]
        for i in range(len(geometry)):
            records.append({'tile': tile, 'anchor': i,
                'costs': {j: risk(first[i], second[j], y, pi) for j in range(len(geometry))},
                'scores': forecasts(model, first[i], geometry, i)})
    model.bias = {name: float(np.mean([r['costs'][r['anchor']] - r['costs'][j] - s[name]
                    for r in records for j, s in r['scores'].items()])) for name in METHODS}
    rows = []
    for r in records:
        scores = {j: {name: s[name] + model.bias[name] for name in METHODS} for j, s in r['scores'].items()}
        rows.append({'tile': r['tile'], 'anchor': r['anchor'],
                     **evaluate_policies(r['costs'], scores, r['anchor'], geometry)})
    summary = block_summary(rows, tiles, anchors=range(len(geometry)))
    baseline = min(BASELINES, key=lambda name: summary['means'][name])
    model.save(out / 'forecaster.npz')
    write(out / 'development_calibration_raw.json', records)
    write(out / 'calibration.json', {'bias': model.bias, 'selected_baseline': baseline,
        'summary': summary, 'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'forecaster_sha256': digest(out / 'forecaster.npz')})
    return baseline


def freeze_decisions(assets, tiles, geometry, shifts, model, out):
    # Only first-model held maps are read. Future maps and truth are obtained later.
    records = []
    for tile in tiles:
        assets.budget()
        first = align(assets.probabilities('held', tile, seeds=(1701,))[0], shifts[0])
        for i in range(len(geometry)):
            scores = forecasts(model, first[i], geometry, i)
            records.append({'tile': tile, 'anchor': i, 'scores': scores,
                'actions': {name: choose({j: s[name] for j, s in scores.items()}, i) for name in METHODS}})
    write(out / 'decisions.json', {'forecaster_sha256': digest(out / 'forecaster.npz'),
        'calibration_sha256': digest(out / 'calibration.json'),
        'shifts_sha256': digest(out / 'frozen_shifts.json'),
        'frozen_utc': datetime.now(timezone.utc).isoformat(), 'records': records})


def measure_held(assets, tiles, geometry, shifts, baseline, pi, out):
    frozen = read(out / 'decisions.json')
    for file, key in (('forecaster.npz', 'forecaster_sha256'), ('calibration.json', 'calibration_sha256'),
                      ('frozen_shifts.json', 'shifts_sha256')):
        if digest(out / file) != frozen[key]:
            raise ValueError('frozen decision inputs changed')
    lookup = {(r['tile'], r['anchor']): r for r in frozen['records']}
    if len(lookup) != len(frozen['records']) or set(lookup) != {(t, i) for t in tiles for i in range(len(geometry))}:
        raise ValueError('incomplete fixed held decisions')
    rows = {'actual_labels': [], 'direct448_sensitivity': []}
    outcomes = []
    for tile in tiles:
        assets.budget()
        raw = assets.probabilities('held', tile)
        first, second = [align(raw[s], shifts[s]) for s in range(2)]
        targets = assets.held_labels(tile)
        for label, target in zip(rows, targets):
            y = target[32:-32, 32:-32]
            for i in range(len(geometry)):
                decision = lookup[tile, i]
                scores = {int(j): s for j, s in decision['scores'].items()}
                for name in METHODS:
                    if choose({j: s[name] for j, s in scores.items()}, i) != decision['actions'][name]:
                        raise ValueError('saved action disagrees with saved forecast')
                costs = {j: risk(first[i], second[j], y, pi) for j in range(len(geometry))}
                values = evaluate_policies(costs, scores, i, geometry)
                values.update(policy_gain=values[baseline] - values['transport'],
                              mae_gain=values['mae_ridge'] - values['mae_transport'],
                              transport_oracle_regret=values['transport'] - values['oracle'])
                rows[label].append({'tile': tile, 'anchor': i, **values})
                outcomes.append({'label': label, 'tile': tile, 'anchor': i, 'costs': costs})
    write(out / 'held_action_outcomes.json', outcomes)
    summary = {}
    for label, values in rows.items():
        write(out / f'{label}_rows.json', values)
        summary[label] = block_summary(values, tiles, anchors=range(len(geometry)))
    return summary


def execute(assets, manifest, cfg, out):
    geometry = np.array([manifest['geometry'][v]['look_xy'] for v in manifest['development_views']])
    held_geometry = np.array([manifest['geometry'][v]['look_xy'] for v in manifest['held_views']])
    pi = cfg['foreground_fraction']
    assets.acquire_images(['fit', 'calibration'])
    assets.forward(['fit', 'calibration'], (1701, 1702))
    shifts, held_shifts = fit_shifts(assets, manifest['fit_tiles'], geometry, held_geometry, out, pi)
    model = fit_forecaster(assets, manifest['fit_tiles'], geometry, shifts, pi)
    baseline = calibrate(assets, manifest['calibration_tiles'], geometry, shifts, model, pi, out)
    assets.acquire_images(['held'])
    assets.forward(['held'], (1701,))
    freeze_decisions(assets, manifest['held_tiles'], held_geometry, held_shifts, model, out)
    assets.forward(['held'], (1702,))
    assets.acquire_held_labels()
    summary = measure_held(assets, manifest['held_tiles'], held_geometry, held_shifts, baseline, pi, out)
    assets.budget()
    summary.update(selected_baseline=baseline, resources=assets.save_evidence(), scope=manifest['scope'])
    if summary['resources']['new_forward_images'] != 2048:
        raise ValueError('unexpected offline forward count')
    primary = summary['actual_labels']['intervals_97_5']
    summary['both_coprimary_lower_bounds_positive'] = all(primary[k][0] > 0 for k in ('policy_gain', 'mae_gain'))
    write(out / 'summary.json', summary)
    print({k: primary[k] for k in ('policy_gain', 'mae_gain')}, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--dataset-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--device', default='cuda:0')
    args = parser.parse_args()
    root, out = args.project_root.resolve(), args.out.resolve()
    if not out.is_relative_to(root / 'runs/r021'):
        raise ValueError('artifacts must stay inside this project runs/r021')
    cfg = read(root / 'configs/r021/protocol.json')
    manifest_path = root / 'configs/r021/data_manifest.json'
    if digest(manifest_path) != cfg['data_manifest_sha256']:
        raise ValueError('fixed metadata cohort changed')
    manifest = read(manifest_path)
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'protocol_binding.json', {'protocol_sha256': digest(root / 'configs/r021/protocol.json'),
          'manifest_sha256': digest(manifest_path)})
    assets = Assets(root, args.dataset_root.resolve(), out, manifest, cfg, args.device)
    try:
        execute(assets, manifest, cfg, out)
    finally:
        assets.save_evidence()


if __name__ == '__main__':
    main()

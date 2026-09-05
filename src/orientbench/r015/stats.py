"""Primary r015 component-equal risks and fixed simultaneous bootstrap family."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

KINDS = ('resnet50', 'vit_b16')
SIZES = (96, 224)
SEEDS = (1501, 1502, 1503)
CONDITIONS = ('I2', 'I8', 'O0', 'O5', 'O10', 'O20', 'T0')


def tag(strategy, kind, size, seed):
    return f'{strategy}_{kind}_{size}_{seed}'


def hard_probability(path: Path, condition: str):
    z = np.load(path)
    p = z[condition].mean(axis=1)
    if not np.isfinite(p).all() or not np.allclose(p.sum(-1), 1, atol=1e-6):
        raise RuntimeError(('invalid probability', str(path), condition))
    return p[..., 1] > .5, z['object_id'], z['component'], z['labels']


def source_condition(root: Path, kind, size, seed, condition):
    if condition.startswith('I'):
        return root / tag('I', kind, size, seed) / 'probabilities.npz', condition
    if condition == 'T0':
        return root / tag('T', kind, size, seed) / 'probabilities.npz', condition
    if condition == 'O5':
        return None, ('O-5', 'O5')
    if condition == 'O10':
        return None, ('O-10', 'O10')
    if condition == 'O20':
        return None, ('O-20', 'O20')
    return root / tag('O', kind, size, seed) / 'probabilities.npz', condition


def load(root: Path):
    meta = None
    hard = np.zeros((2, 2, 3, len(CONDITIONS), 7416, 3), dtype=bool)
    for mi, kind in enumerate(KINDS):
        for ni, size in enumerate(SIZES):
            for si, seed in enumerate(SEEDS):
                for qi, condition in enumerate(CONDITIONS):
                    path, item = source_condition(root, kind, size, seed, condition)
                    if path is None:
                        path = root / tag('O', kind, size, seed) / 'probabilities.npz'
                        left, oid, component, labels = hard_probability(path, item[0])
                        right, oid2, component2, labels2 = hard_probability(path, item[1])
                        value = np.stack((left, right)).mean(0) > .5
                    else:
                        value, oid, component, labels = hard_probability(path, item)
                        oid2, component2, labels2 = oid, component, labels
                    candidate = (oid, component, labels)
                    if meta is None:
                        meta = candidate
                    elif any(not np.array_equal(a, b) for a, b in zip(meta, candidate)):
                        raise RuntimeError('calibration identity')
                    if not (np.array_equal(oid, oid2) and np.array_equal(component, component2) and np.array_equal(labels, labels2)):
                        raise RuntimeError('paired dose identity')
                    hard[mi, ni, si, qi] = value
    return hard, meta


def component_errors(hard, component, labels, keys):
    error = np.zeros((2, 2, 3, len(CONDITIONS), 3, len(keys), 2))
    present = np.zeros((3, len(keys), 2), dtype=bool)
    for ai in range(3):
        for ci, key in enumerate(keys):
            for klass in range(2):
                index = (component == key) & (labels[:, ai] == klass)
                present[ai, ci, klass] = index.any()
                if index.any():
                    error[..., ai, ci, klass] = (hard[..., index, ai] != klass).mean(-1)
    return error, present


def risk(weights, error, present):
    draws, components = weights.shape
    result = np.empty((draws, 2, 2, 3, len(CONDITIONS), 3))
    for attr in range(3):
        values = 0
        for klass in range(2):
            denominator = weights @ present[attr, :, klass]
            if (denominator == 0).any():
                raise RuntimeError(('zero class denominator', attr, klass, np.flatnonzero(denominator == 0).tolist()))
            numerator = np.einsum('dc,mnsqc->dmnsq', weights, error[..., attr, :, klass])
            values = values + numerator / denominator[:, None, None, None, None]
        result[..., attr] = .5 * values
    return result


def family(r):
    # r: draws,m,n,seed,condition,attribute
    macro = r.mean(-1).mean(3)
    values, names = [], []
    for mi, kind in enumerate(KINDS):
        for ni, size in enumerate(SIZES):
            for which, source in (('G2', 0), ('G8', 1)):
                for dose, target in ((0, 2), (5, 3), (10, 4), (20, 5)):
                    values.append(macro[:, mi, ni, source] - macro[:, mi, ni, target])
                    names.append(f'{which}_{kind}_{size}_d{dose}')
            values.extend((macro[:, mi, ni, 2] - macro[:, mi, ni, 6], macro[:, mi, ni, 0], macro[:, mi, ni, 2]))
            names.extend((f'A_{kind}_{size}', f'R_I2_{kind}_{size}', f'R_O0_{kind}_{size}'))
    for mi, kind in enumerate(KINDS):
        values.append(macro[:, mi, 0, 0] - macro[:, mi, 0, 2] - (macro[:, mi, 1, 0] - macro[:, mi, 1, 2]))
        names.append(f'J_{kind}')
    return np.stack(values, -1), names


def intervals(point, draws):
    sd = draws.std(0, ddof=1)
    nonzero = sd > 0
    if np.any(~nonzero & (np.abs(draws - point) > 1e-12).any(0)):
        raise RuntimeError('nonconstant zero variance')
    statistic = np.zeros_like(draws)
    statistic[:, nonzero] = np.abs((draws[:, nonzero] - point[nonzero]) / sd[nonzero])
    q = float(np.quantile(statistic.max(1), .95, method='linear')) if nonzero.any() else 0.
    return sd, q, point - q * sd, point + q * sd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise RuntimeError('statistics output exists')
    hard, (oid, component, labels) = load(args.raw)
    keys = np.array(sorted(np.unique(component), key=lambda x: str(x)))
    if len(oid) != 7416 or len(keys) != 25:
        raise RuntimeError(('universe', len(oid), len(keys)))
    error, present = component_errors(hard, component, labels, keys)
    rng = np.random.Generator(np.random.PCG64(15015))
    draws = rng.integers(0, len(keys), size=(50000, len(keys)))
    weights = np.zeros((len(draws), len(keys)), dtype=np.int16)
    np.add.at(weights, (np.arange(len(draws))[:, None], draws), 1)
    bootstrap, names = family(risk(weights, error, present))
    point, point_names = family(risk(np.ones((1, len(keys))), error, present))
    if names != point_names or len(names) != 46:
        raise RuntimeError('family contract')
    point = point[0]
    sd, q, lower, upper = intervals(point, bootstrap)
    loo = []
    for leave in range(len(keys)):
        w = np.ones((1, len(keys))); w[0, leave] = 0
        loo.append(family(risk(w, error, present))[0][0])
    args.out.mkdir(parents=True)
    np.save(args.out / 'bootstrap_draws.npy', draws)
    np.save(args.out / 'bootstrap_replicates.npy', bootstrap.astype(np.float32))
    summary = {'protocol': 'r015-matched-support-v1', 'objects': len(oid), 'components': len(keys),
        'component_keys': [str(x) for x in keys], 'dimensions': names, 'point': point.tolist(), 'sd': sd.tolist(),
        'simultaneous_q95': q, 'lower': lower.tolist(), 'upper': upper.tolist(), 'loo': np.asarray(loo).tolist(),
        'class_present': present.tolist(), 'zero_denominator_draws': 0}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()

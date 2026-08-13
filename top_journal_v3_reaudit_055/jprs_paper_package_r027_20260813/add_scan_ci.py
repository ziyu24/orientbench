#!/usr/bin/env python3
"""DESCRIPTIVE cluster-bootstrap AR scans required by r027 T1.

The ranking order is invariant across cluster resamples, so this implementation
sorts each score vector once and evaluates all bootstrap draws in one array
operation.  It intentionally limits the CI scan to the prescribed DIOR and
DOTA units; other frozen units remain available in the point-only appendix.
"""
from pathlib import Path
import gc
import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
O = R / 'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813'

def metric(score, risk, weight, q=None):
    order = np.argsort(-score, kind='stable')
    score, risk, weight = score[order], risk[order], weight[order]
    start = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    cw = np.add.reduceat(weight, start)
    cr = np.add.reduceat(weight * risk, start)
    keep = cw > 0; cw, cr = cw[keep], cr[keep]
    cc, rr = np.cumsum(cw), np.cumsum(cr); total = cw.sum()
    if q is None:
        return float(np.sum((np.r_[0., rr[:-1] / total] + rr / total) * cw / total / 2))
    return float(rr[np.searchsorted(cc, q * total)] / cc[np.searchsorted(cc, q * total)])

def metric_reps(score, risk, cluster_ix, draw_weights, q=None):
    """One value per bootstrap draw, preserving whole score-tie blocks.

    Keep each draw separate: the host is concurrently training four detectors,
    and materializing ``draws × rows`` can be reclaimed by the kernel before
    the CSV is flushed.
    """
    order = np.argsort(-score, kind='stable')
    score, risk, cluster_ix = score[order], risk[order], cluster_ix[order]
    start = np.r_[0, np.flatnonzero(score[1:] != score[:-1]) + 1]
    out = []
    for draw in draw_weights:
        w = draw[cluster_ix]
        cw, cr = np.add.reduceat(w, start), np.add.reduceat(w * risk, start)
        keep = cw > 0; cw, cr = cw[keep], cr[keep]
        cc, rr = np.cumsum(cw), np.cumsum(cr); total = cw.sum()
        if q is None:
            out.append(float(np.sum((np.r_[0., rr[:-1] / total] + rr / total) * cw / total / 2)))
        else:
            out.append(float(rr[np.searchsorted(cc, q * total)] / cc[np.searchsorted(cc, q * total)]))
    return np.asarray(out)

def scan(frame, dataset, unit, seed):
    cluster_name = 'cluster' if 'cluster' in frame else 'mother'
    clusters = pd.unique(frame[cluster_name]); pos = {x:i for i, x in enumerate(clusters)}
    rng = np.random.RandomState(seed)
    draws = np.vstack([np.bincount(rng.randint(0, len(clusters), len(clusters)), minlength=len(clusters)) for _ in range(200)]).astype(float)
    risk_col = 'risk_main' if 'risk_main' in frame else 'risk'
    rows = []
    for cutoff in np.round(np.arange(1, 3.01, .1), 1):
        z = frame[frame.ar >= cutoff]
        ix = z[cluster_name].map(pos).to_numpy()
        risk = z[risk_col].to_numpy(float)
        raw, linear = z.raw_confidence.to_numpy(float), z.linear_source_frozen.to_numpy(float)
        for endpoint, q in [('AUGRC', None), ('Risk@70', .7), ('Risk@90', .9)]:
            point = metric(linear, risk, np.ones(len(z)), q) - metric(raw, risk, np.ones(len(z)), q)
            reps = metric_reps(linear, risk, ix, draws, q) - metric_reps(raw, risk, ix, draws, q)
            rows.append({'dataset':dataset, 'unit':unit, 'cutoff':cutoff, 'endpoint':endpoint, 'rows':len(z),
                         'delta_linear_minus_raw':point, 'ci_low':float(np.quantile(reps,.025)),
                         'ci_high':float(np.quantile(reps,.975)), 'bootstrap_replicates':200,
                         'status':'DESCRIPTIVE'})
        del z, ix, risk, raw, linear
        gc.collect()
    return rows

def dota_aggregate_scan(frames, name, seed):
    """Equal-detector DOTA aggregate with a *joint* mother-cluster bootstrap.

    A resampled mother ID receives its multiplicity in each detector's matched
    rows; each draw is then the arithmetic mean of the two detector metrics.
    Thus the reported CI is for the equal-unit aggregate itself, rather than
    an average of separately estimated confidence limits.
    """
    clusters = sorted(set().union(*(set(f.mother) for f in frames.values())))
    pos = {x:i for i, x in enumerate(clusters)}
    rng = np.random.RandomState(seed)
    draws = np.vstack([np.bincount(rng.randint(0, len(clusters), len(clusters)), minlength=len(clusters)) for _ in range(200)]).astype(float)
    rows = []
    for cutoff in np.round(np.arange(1, 3.01, .1), 1):
        unit_data = {}
        for unit, f in frames.items():
            z = f[f.ar >= cutoff]
            unit_data[unit] = (z.raw_confidence.to_numpy(float), z.linear_source_frozen.to_numpy(float),
                               z.risk.to_numpy(float), z.mother.map(pos).to_numpy())
        for endpoint, q in [('AUGRC', None), ('Risk@70', .7), ('Risk@90', .9)]:
            point_values, raw_rep_values, linear_rep_values = [], [], []
            for raw, linear, risk, ix in unit_data.values():
                one = np.ones(len(raw))
                point_values.append(metric(linear, risk, one, q) - metric(raw, risk, one, q))
                raw_rep_values.append(metric_reps(raw, risk, ix, draws, q))
                linear_rep_values.append(metric_reps(linear, risk, ix, draws, q))
            point = float(np.mean(point_values))
            reps = np.mean(np.vstack(linear_rep_values), axis=0) - np.mean(np.vstack(raw_rep_values), axis=0)
            rows.append({'dataset':'DOTA-v1.0', 'unit':name, 'cutoff':cutoff, 'endpoint':endpoint,
                         'rows':sum(len(v[0]) for v in unit_data.values()), 'delta_linear_minus_raw':point,
                         'ci_low':float(np.quantile(reps,.025)), 'ci_high':float(np.quantile(reps,.975)),
                         'bootstrap_replicates':200, 'status':'DESCRIPTIVE'})
    return rows

def main():
    core = pd.read_parquet(R / 'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000/rows.parquet')
    out = []
    for i, unit in enumerate(('A','B','C')):
        f = core[core.unit.eq(unit)]
        out += scan(f, 'DIOR-R', unit, 100+i)
    d = R / 'outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a_raw'
    dota = {u:pd.read_parquet(d / f'matched_{u}.parquet') for u in ('orcnn','rtmdet')}
    for i, (unit, f) in enumerate(dota.items()): out += scan(f, 'DOTA-v1.0', unit, 200+i)
    out += dota_aggregate_scan(dota, 'equal_unit', 300)
    # The second requested aggregate is the all-detector row-pooled summary;
    # it is resampled by the same joint mother-cluster draws.
    pooled = pd.concat(dota.values(), ignore_index=True)
    out += scan(pooled, 'DOTA-v1.0', 'pooled_units', 301)
    pd.DataFrame(out).to_csv(O/'all_ar_scans_with_cluster_ci_descriptive.csv', index=False)

if __name__ == '__main__': main()

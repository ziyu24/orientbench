"""B: independent CPU loss replay of saved r019 train/calibration probabilities."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import numpy as np


def read(p):
    return json.loads(p.read_text())


def review(root, dataset):
    sys.path.insert(0, str(root / 'src'))
    from orientbench.r018.b_readonly_review import loss, sha
    from affine import Affine
    from rasterio.features import rasterize
    from rasterio.crs import CRS
    start = datetime.now(timezone.utc).isoformat()
    remote = subprocess.check_output(['git', '-C', str(root), 'remote', 'get-url', 'origin'], text=True).strip()
    if remote not in ('https://github.com/ziyu24/orientbench.git', 'https://github.com/ziyu24/orientbench'):
        raise ValueError('wrong repository')
    old, prior, out = [root / f'runs/r{n}/artifacts' for n in ('017', '018', '019')]
    cfg = read(root / 'configs/r019/protocol.json')
    manifest = read(root / 'configs/r017/data_manifest.json')
    bind, frozen, saved = [read(out / name) for name in ('input_bindings.json', 'frozen_shifts.json', 'summary.json')]
    if sha(root / 'configs/r017/data_manifest.json') != cfg['data_manifest_sha256']:
        raise ValueError('cohort changed')
    if sha(old / 'checkpoints/seed1701_epoch30.pt') != cfg['checkpoint_sha256']:
        raise ValueError('checkpoint changed')
    pi, shifts = cfg['foreground_fraction'], [(s['dy'], s['dx']) for s in frozen['shifts']]
    crop = lambda a, dy=0, dx=0: a[..., 32+dy:416+dy, 32+dx:416+dx]
    training = np.zeros((4, 2))
    for tile in manifest['training_tiles']:
        cp, pp = old / 'cache/train' / f'{tile}.npz', out / 'train_predictions' / f'{tile}.npz'
        if sha(cp) != bind['train_cache'][tile] or sha(pp) != bind['train_predictions'][tile]:
            raise ValueError('training input changed')
        with np.load(cp) as z:
            y, valid = crop(z['label']), crop(z['valid'])
        with np.load(pp) as z:
            p = z['base']
        for i, (dy, dx) in enumerate(shifts):
            training[i, 0] += loss(crop(p[i]), y, valid, pi) / 256
            training[i, 1] += loss(crop(p[i], dy, dx), y, valid, pi) / 256
    with np.load(out / 'training_loss_surfaces.npz') as z:
        surfaces = z['surfaces']
    for i, (dy, dx) in enumerate(shifts):
        choices = [tuple(map(int, p-32)) for p in np.argwhere(surfaces[i] <= surfaces[i].min()+1e-12)]
        expected = min(choices, key=lambda s: (s[0]**2+s[1]**2, s[0], s[1]))
        if expected != (dy, dx):
            raise ValueError('selected shift not the frozen surface minimum')
    training_error = max(abs(training[i, j] - surfaces[i, 32+dy, 32+dx])
                         for i, s in enumerate(shifts) for j, (dy, dx) in enumerate(((0, 0), s)))

    labels = {x['tile']: x for x in manifest['labels']}
    label_names = ('actual_cached_labels', 'direct448_label_sensitivity')
    arms = ('full448', 'zero_core', 'aligned_core', 'paired_change')
    tables = {n: {a: read(out/f'{n}_{a}_rows.json') for a in arms} for n in label_names}
    lookup = {n: {a: {r['tile']: r for r in rows} for a, rows in ts.items()} for n, ts in tables.items()}
    for ts in tables.values():
        for rows in ts.values():
            if len(rows) != 128 or {(r['seed'], r['tile']) for r in rows} != {(1701,t) for t in manifest['calibration_tiles']}:
                raise ValueError('incomplete or duplicate calibration rows')
    loss_error, iou_error = 0., 0
    for tile in manifest['calibration_tiles']:
        cp, pp = old/'cache/calibration'/f'{tile}.npz', prior/'predictions'/f'seed1701_{tile}.npz'
        if sha(cp) != bind['calibration_cache'][tile] or sha(pp) != bind['calibration_predictions'][tile]:
            raise ValueError('calibration input changed')
        with np.load(cp) as z:
            y, valid = z['label'], z['valid']
        with np.load(pp) as z:
            p, rot = z['base'], z['aligned_rotation']
        key = labels[tile]['key'].split('spacenet/SN4_buildings/train/AOI_6_Atlanta/')[1]
        lp = dataset/'SpaceNet4/train'/key
        if sha(lp) != bind['labels'][tile]:
            raise ValueError('native label changed')
        payload = read(lp)
        assert CRS.from_user_input(payload['crs']['properties']['name']).to_epsg() == 32616
        x0, y0 = map(int, tile.split('_'))
        shapes = [(f['geometry'], 1) for f in payload['features']]
        direct = (rasterize(shapes, out_shape=(448,448), transform=Affine(450/448,0,x0,0,-450/448,y0+450),
                            all_touched=False, dtype='uint8').astype(bool) if shapes else np.zeros((448,448),bool))
        for name, target in zip(label_names, (y, direct)):
            values = {}
            for arm in arms[:3]:
                b, r, t, v = p, rot, target, valid
                if arm != 'full448':
                    s = shifts if arm == 'aligned_core' else [(0,0)]*4
                    b = np.stack([crop(p[i], *q) for i,q in enumerate(s)])
                    r = np.stack([crop(rot[i], *q) for i,q in enumerate(s[:2])])
                    t, v = crop(target), crop(valid)
                maps = dict(zip('abuv', b))
                maps.update(au=(b[0]+b[2])/2, av=(b[0]+b[3])/2, bv=(b[1]+b[3])/2, bu=(b[1]+b[2])/2,
                            a_tta=(b[0]+r[0])/2, b_tta=(b[1]+r[1])/2,
                            constant_half=np.full(t.shape,.5), constant_prevalence=np.full(t.shape,pi))
                row = lookup[name][arm][tile]
                result = {f'loss_{k}':loss(q,t,v,pi) for k,q in maps.items()}
                bf = b.astype(np.float64)
                da = loss((bf[0]+bf[2])/2,t,v,pi)-loss((bf[0]+bf[3])/2,t,v,pi)
                db = loss((bf[1]+bf[3])/2,t,v,pi)-loss((bf[1]+bf[2])/2,t,v,pi)
                result.update(primary=(da+db)/2, delta_a=da, delta_b=db,
                              tta_gain_a=result['loss_a_tta']-result['loss_av'],
                              tta_gain_b=result['loss_b_tta']-result['loss_bu'])
                loss_error = max(loss_error, max(abs(row[k]-x) for k,x in result.items()))
                for k,q in maps.items():
                    if k.startswith('constant'):
                        continue
                    pred=q>=.5
                    counts=(int((pred&t&v).sum()),int(((pred|t)&v).sum()))
                    iou_error=max(iou_error,*(abs(count-row[f'iou_{k}_{suffix}']) for count,suffix in zip(counts,('intersection','union'))))
                values[arm] = result
            z, a = values['zero_core'], values['aligned_core']
            delta = {'primary':z['primary']-a['primary'], 'delta_residual_i':a['primary'],
                     'delta_single_risk_improvement':float(np.mean([z[f'loss_{k}']-a[f'loss_{k}'] for k in 'abuv']))}
            delta.update({f'delta_risk_{k}':z[f'loss_{k}']-a[f'loss_{k}'] for k in ('a','b','u','v','au','av','bv','bu','a_tta','b_tta')})
            loss_error=max(loss_error,max(abs(lookup[name]['paired_change'][tile][k]-x) for k,x in delta.items()))

    block=lambda t:tuple(int(v)//2700 for v in t.split('_'))
    blocks=list(dict.fromkeys(map(block,manifest['calibration_tiles'])))
    indices=np.random.Generator(np.random.PCG64(17017)).integers(0,16,(20000,16))
    aggregate_error, recomputed = 0., {}
    for name in label_names:
        recomputed[name]={}
        for arm in arms:
            rows=tables[name][arm]
            keys=[k for k in rows[0] if k=='primary' or k.startswith(('loss_','delta_','tta_gain_'))]
            vals={k:np.array([np.mean([r[k] for r in rows if block(r['tile'])==b]) for b in blocks]) for k in keys}
            means={k:float(x.mean()) for k,x in vals.items()}
            ci={k:np.quantile(x[indices].mean(1),[.025,.975]).tolist() for k,x in vals.items()}
            for k in keys:
                aggregate_error=max(aggregate_error,abs(means[k]-saved[name][arm]['metric_block_equal'][k]),
                                    *np.abs(np.array(ci[k])-saved[name][arm]['intervals_95'][k]))
            recomputed[name][arm]={'means':means,'intervals':ci}
    if max(loss_error,training_error,aggregate_error)>1e-10 or iou_error:
        raise ValueError(f'replay mismatch: {loss_error}, {training_error}, {aggregate_error}, {iou_error}')
    return {'observed_start_utc':start,'observed_end_utc':datetime.now(timezone.utc).isoformat(),
            'scope':'Read-only CPU replay; no new model forward, fitting, downloads or server writes.',
            'training_tiles':256,'calibration_tiles':128,'row_tables':8,
            'training_direct_vs_saved_surface_max_abs_difference':float(training_error),
            'probability_metric_max_abs_difference':float(loss_error),'iou_count_max_abs_difference':int(iou_error),
            'aggregate_max_abs_difference':float(aggregate_error),'shifts':frozen['shifts'], 'recomputed':recomputed,
            'resources_reported_by_server':saved['resources'],
            'source_hashes':{p.name:sha(p) for p in out.glob('*.json')}}


if __name__ == '__main__':
    print(json.dumps(review(Path('/home/rspip/cqc/study/orientbench'),Path('/home/rspip/cqc/data/dataset'))),flush=True)

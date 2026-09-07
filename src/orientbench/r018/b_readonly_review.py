"""Read-only CPU audit of all frozen r018 probabilities, labels, rows and statistics."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 << 20):
            h.update(chunk)
    return h.hexdigest()


def loss(p, y, mask, pi):
    # Independent expression: pick the true-class probability before taking log.
    if p.shape != y.shape or y.shape != mask.shape or not mask.any():
        raise ValueError("invalid common-grid loss inputs")
    p = np.asarray(p, dtype=np.float64)[mask]
    truth = y[mask]
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("invalid probability")
    true_probability = np.where(truth, np.clip(p, 1e-6, 1-1e-6), 1-np.clip(p, 1e-6, 1-1e-6))
    weights = np.where(truth, 1/(2*pi), 1/(2*(1-pi)))
    return float(np.dot(weights, -np.log(true_probability)) / len(weights))


def aggregate(rows, tiles):
    lookup = {(r['seed'], r['tile']): r for r in rows}
    if len(rows) != 256 or set(lookup) != {(s,t) for s in (1701,1702) for t in tiles}:
        raise ValueError("incomplete or duplicate frozen rows")
    block = lambda t: tuple(int(v)//2700 for v in t.split('_'))
    blocks = list(dict.fromkeys(map(block, tiles)))
    metrics = ('primary','delta_a','delta_b','tta_gain_a','tta_gain_b')
    seed_blocks = {str(s): {k: [float(np.mean([lookup[s,t][k] for t in tiles if block(t)==b]))
                              for b in blocks] for k in metrics} for s in (1701,1702)}
    pooled = {k: np.mean([seed_blocks[str(s)][k] for s in (1701,1702)], axis=0) for k in metrics}
    rng = np.random.Generator(np.random.PCG64(17017))
    indices = rng.integers(0, len(blocks), (20000,len(blocks)))
    return {'block_order': blocks, 'means': {k:float(v.mean()) for k,v in pooled.items()},
            'intervals': {k:np.quantile(v[indices].mean(1),[.025,.975]).tolist() for k,v in pooled.items()},
            'seed_block_values':seed_blocks,
            'seed_means':{s:{k:float(np.mean(v)) for k,v in value.items()} for s,value in seed_blocks.items()}}


def review(project, dataset):
    from affine import Affine
    from rasterio.features import rasterize
    from rasterio.crs import CRS
    start = datetime.now(timezone.utc).isoformat()
    original, out = project/'runs/r017/artifacts', project/'runs/r018/artifacts'
    manifest = read(project/'configs/r017/data_manifest.json')
    protocol = read(project/'configs/r018/protocol.json')
    bindings = read(out/'input_bindings.json')
    if bindings['manifest'] != protocol['data_manifest_sha256'] or bindings['original_rows'] != protocol['original_rows_sha256']:
        raise ValueError('incorrect frozen input bindings')
    if bindings['checkpoints'] != protocol['checkpoint_sha256']:
        raise ValueError('wrong checkpoints')
    pi = protocol['foreground_fraction']
    names = ('actual_cached_labels','direct448_label_sensitivity')
    tables = {n:read(out/f'{n}_rows.json') for n in names}
    lookup = {n:{(r['seed'],r['tile']):r for r in table} for n,table in tables.items()}
    summary = read(out/'summary.json')
    labels = {item['tile']:item for item in manifest['labels']}
    max_loss = {n:0.0 for n in names}
    max_iou_count = 0
    prediction_files = []
    # Secondary post-result diagnostic; not a new primary or a selection rule.
    ensemble_rows = []
    for tile in manifest['calibration_tiles']:
        cache = original/'cache/calibration'/f'{tile}.npz'
        if sha(cache) != bindings['cache'][tile]:
            raise ValueError('cache changed')
        with np.load(cache) as d:
            y, valid = d['label'], d['valid']
        key = labels[tile]['key'].split('spacenet/SN4_buildings/train/AOI_6_Atlanta/')[1]
        path = dataset/'SpaceNet4/train'/key
        if sha(path) != bindings['labels'][tile]:
            raise ValueError('label changed')
        payload = read(path)
        if CRS.from_user_input(payload['crs']['properties']['name']).to_epsg()!=32616:
            raise ValueError('incorrect native label CRS')
        x0,y0 = map(int,tile.split('_'))
        transform = Affine(450/448,0,x0,0,-450/448,y0+450)
        geometries = [(feature['geometry'],1) for feature in payload['features']]
        direct = (rasterize(geometries,out_shape=(448,448),transform=transform,dtype='uint8',all_touched=False).astype(bool)
                  if geometries else np.zeros((448,448),bool))
        bases = []
        for seed in (1701,1702):
            pred_path = out/'predictions'/f'seed{seed}_{tile}.npz'
            with np.load(pred_path) as pfile:
                p, rotation = pfile['base'], pfile['aligned_rotation']
            if p.shape != (4,448,448) or rotation.shape != (2,448,448) or p.dtype!=np.float32 or rotation.dtype!=np.float32:
                raise ValueError('incomplete FP32 probability maps')
            prediction_files.append({'file':pred_path.name,'bytes':pred_path.stat().st_size,'sha256':sha(pred_path)})
            bases.append(p)
            maps = dict(zip(('a','b','u','v'),p))
            maps.update(au=(p[0]+p[2])/2,av=(p[0]+p[3])/2,bv=(p[1]+p[3])/2,bu=(p[1]+p[2])/2,
                        a_tta=(p[0]+rotation[0])/2,b_tta=(p[1]+rotation[1])/2,
                        constant_half=np.full(y.shape,.5),constant_prevalence=np.full(y.shape,pi))
            for name,target in zip(names,(y,direct)):
                row=lookup[name][seed,tile]
                for metric,prob in maps.items():
                    difference=abs(loss(prob,target,valid,pi)-row['loss_'+metric])
                    max_loss[name]=max(max_loss[name],difference)
                    if not metric.startswith('constant'):
                        pred = prob>=.5
                        intersection=int((pred & target & valid).sum())
                        union=int(((pred | target)&valid).sum())
                        max_iou_count=max(max_iou_count,abs(intersection-row[f'iou_{metric}_intersection']),abs(union-row[f'iou_{metric}_union']))
        for name,target in zip(names,(y,direct)):
            row={'tile':tile,'label_scope':name}
            for index,anchor,pair in ((0,'a','av'),(1,'b','bu')):
                same_image=(bases[0][index]+bases[1][index])/2
                ensemble=loss(same_image,target,valid,pi)
                real_pair=np.mean([lookup[name][s,tile]['loss_'+pair] for s in (1701,1702)])
                row['same_view_ensemble_'+anchor]=ensemble
                row['real_pair_gain_'+anchor]=float(ensemble-real_pair)
            ensemble_rows.append(row)
    if max(max_loss.values())>1e-10 or max_iou_count:
        raise ValueError(f'probability replay mismatch: {max_loss}, IoU {max_iou_count}')
    recomputed={n:aggregate(tables[n],manifest['calibration_tiles']) for n in names}
    differences=[]
    for n,d in recomputed.items():
        for metric,value in d['means'].items():
            differences.append(abs(value-summary[n]['metric_block_equal'][metric]))
            differences.extend(abs(a-b) for a,b in zip(d['intervals'][metric],summary[n]['intervals_95'][metric]))
    block=lambda t:tuple(int(v)//2700 for v in t.split('_'))
    block_order=list(dict.fromkeys(map(block,manifest['calibration_tiles'])))
    ensemble={}
    for name in names:
        selected=[r for r in ensemble_rows if r['label_scope']==name]
        values={k:[float(np.mean([r[k] for r in selected if block(r['tile'])==b])) for b in block_order]
                for k in ('same_view_ensemble_a','same_view_ensemble_b','real_pair_gain_a','real_pair_gain_b')}
        rng = np.random.Generator(np.random.PCG64(17017))
        indices = rng.integers(0, len(block_order), (20000,len(block_order)))
        ensemble[name]={'block_values':values,'means':{k:float(np.mean(v)) for k,v in values.items()},
                        'descriptive_95_intervals':{k:np.quantile(np.asarray(v)[indices].mean(1),[.025,.975]).tolist()
                                                    for k,v in values.items() if k.startswith('real_pair_gain')}}
    label_counts={}
    differences_rows=read(out/'label_grid_differences.json')
    for split in ('train','calibration'):
        group=[r for r in differences_rows if r['split']==split]
        changed=sum(r['mismatch_pixels'] for r in group); total=sum(r['valid_pixels'] for r in group)
        label_counts[split]={'tiles':len(group),'mismatch_pixels':changed,'valid_pixels':total,'fraction':changed/total}
    return {'observed_start_utc':start,'observed_end_utc':datetime.now(timezone.utc).isoformat(),
            'scope':'Read-only CPU replay of all 256 stored predictions; no model inference, training, downloading datasets or server writes.',
            'probability_loss_max_abs_difference':max_loss,'iou_count_max_abs_difference':max_iou_count,
            'aggregate_max_abs_difference':max(differences),'recomputed':recomputed,'label_differences':label_counts,
            'prediction_files':prediction_files,'prediction_bytes':sum(x['bytes'] for x in prediction_files),
            'posthoc_same_view_ensemble':ensemble,
            'posthoc_scope':'Additional analysis after observing r018, not preregistered and not a new confirmation. Two existing models on one image versus one model on two images: equal inference count, different model/training and acquisition costs.',
            'source_hashes':{p.name:sha(p) for p in (out/'summary.json',out/'actual_cached_labels_rows.json',out/'direct448_label_sensitivity_rows.json',out/'input_bindings.json')}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,required=True)
    parser.add_argument('--dataset-root',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(review(args.project_root,args.dataset_root)),flush=True)

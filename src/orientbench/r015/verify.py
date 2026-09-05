"""Independent r015 recomputation from raw probabilities and frozen bootstrap draws."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

K = ('resnet50', 'vit_b16'); N = (96, 224); S = (1501, 1502, 1503)
Q = ('I2', 'I8', 'O0', 'O5', 'O10', 'O20', 'T0')


def path(raw, strategy, kind, size, seed):
    return raw / f'{strategy}_{kind}_{size}_{seed}' / 'probabilities.npz'


def get(raw, kind, size, seed, name):
    if name in ('I2', 'I8'):
        source, labels = path(raw, 'I', kind, size, seed), (name,)
    elif name == 'T0':
        source, labels = path(raw, 'T', kind, size, seed), ('T0',)
    elif name in ('O5', 'O10', 'O20'):
        source, labels = path(raw, 'O', kind, size, seed), (f'O-{name[1:]}', f'O{name[1:]}')
    else:
        source, labels = path(raw, 'O', kind, size, seed), ('O0',)
    z = np.load(source)
    values = []
    for label in labels:
        p = z[label]
        if not np.isfinite(p).all() or not np.allclose(p.sum(-1), 1, atol=1e-6):
            raise RuntimeError(('probability', str(source), label))
        values.append(p.mean(1)[..., 1] > .5)
    return np.stack(values).mean(0) > .5, (z['object_id'], z['component'], z['labels'])


def compute(raw, draws):
    sample = None; hard = np.zeros((2, 2, 3, 7, 7416, 3), bool)
    for mi, kind in enumerate(K):
      for ni, size in enumerate(N):
       for si, seed in enumerate(S):
        for qi, name in enumerate(Q):
            value, meta = get(raw, kind, size, seed, name)
            if sample is None: sample = meta
            elif any(not np.array_equal(a, b) for a, b in zip(sample, meta)): raise RuntimeError('identity')
            hard[mi, ni, si, qi] = value
    oid, component, labels = sample
    keys = np.array(sorted(np.unique(component), key=lambda x: str(x)))
    if len(oid) != 7416 or len(keys) != 25: raise RuntimeError('universe')
    error = np.zeros((2,2,3,7,3,25,2)); present=np.zeros((3,25,2),bool)
    for a in range(3):
     for c,key in enumerate(keys):
      for klass in range(2):
       ix=(component==key)&(labels[:,a]==klass); present[a,c,klass]=ix.any()
       if ix.any(): error[...,a,c,klass]=(hard[...,ix,a]!=klass).mean(-1)
    weights=np.zeros((len(draws),25)); np.add.at(weights,(np.arange(len(draws))[:,None],draws),1)
    risks=np.empty((len(draws),2,2,3,7,3))
    for a in range(3):
     total=0
     for klass in range(2):
      den=weights@present[a,:,klass]
      if (den==0).any(): raise RuntimeError('zero denominator')
      total += np.einsum('dc,mnsqc->dmnsq',weights,error[...,a,:,klass])/den[:,None,None,None,None]
     risks[...,a]=.5*total
    macro=risks.mean(-1).mean(3); vals=[]
    for mi in range(2):
     for ni in range(2):
      for source in (0,1):
       vals.extend([macro[:,mi,ni,source]-macro[:,mi,ni,target] for target in (2,3,4,5)])
      vals.extend((macro[:,mi,ni,2]-macro[:,mi,ni,6],macro[:,mi,ni,0],macro[:,mi,ni,2]))
    for mi in range(2): vals.append(macro[:,mi,0,0]-macro[:,mi,0,2]-(macro[:,mi,1,0]-macro[:,mi,1,2]))
    return np.stack(vals,-1), keys


def main():
    p=argparse.ArgumentParser(); p.add_argument('--raw',type=Path,required=True);p.add_argument('--statistics',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    summary=json.loads((a.statistics/'summary.json').read_text());draws=np.load(a.statistics/'bootstrap_draws.npy')
    replicated,keys=compute(a.raw,draws)
    point,_=compute(a.raw,np.arange(25,dtype=np.int64)[None,:])
    point=point[0]
    saved=np.load(a.statistics/'bootstrap_replicates.npy')
    sd=replicated.std(0,ddof=1); active=sd>0
    z=np.zeros_like(replicated);z[:,active]=np.abs((replicated[:,active]-point[active])/sd[active])
    q=float(np.quantile(z.max(1),.95,method='linear')) if active.any() else 0.
    match= saved.shape==replicated.shape and np.allclose(saved,replicated,atol=1e-6,rtol=0) and np.allclose(point,summary['point'],atol=1e-10,rtol=0) and np.allclose(sd,summary['sd'],atol=1e-10,rtol=0) and abs(q-summary['simultaneous_q95'])<=1e-10
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps({'protocol':'r015-independent-verifier-v1','independent':True,'objects':7416,'components':len(keys),'bootstrap_match':bool(match),'max_abs_bootstrap_difference':float(np.max(np.abs(saved-replicated))),'point':point.tolist(),'q95':q,'reported_dimensions':len(summary['dimensions'])},sort_keys=True,indent=2)+'\n')
    if not match: raise RuntimeError('primary bootstrap mismatch')

if __name__=='__main__': main()

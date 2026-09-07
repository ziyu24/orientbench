"""Average assignment losses, never pool four predictions into a two-call action."""
import numpy as np
from orientbench.r017.measurement import weighted_log_loss


def measure(probabilities, target, valid, pi):
    p = np.asarray(probabilities, dtype=np.float64)
    if p.shape != (2, 4, *target.shape):
        raise ValueError('two models and four complete maps required')
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('finite probabilities in [0,1] required')
    maps = {'same_a': (p[0,0]+p[1,0])/2, 'same_b': (p[0,1]+p[1,1])/2}
    for name, anchor, other in (('av',0,3),('au',0,2),('bu',1,2),('bv',1,3)):
        maps[name+'_12']=(p[0,anchor]+p[1,other])/2
        maps[name+'_21']=(p[1,anchor]+p[0,other])/2
    result={f'loss_{k}':weighted_log_loss(q,target,valid,pi) for k,q in maps.items()}
    for name in ('av','au','bu','bv'):
        result['loss_'+name]=(result['loss_'+name+'_12']+result['loss_'+name+'_21'])/2
    result['gain_a']=result['loss_same_a']-result['loss_av']
    result['gain_b']=result['loss_same_b']-result['loss_bu']
    result['crossed_i']=(result['loss_au']-result['loss_av']+result['loss_bv']-result['loss_bu'])/2
    for name,q in maps.items():
        pred=q>=.5
        result[f'iou_{name}_intersection']=int((pred & target & valid).sum())
        result[f'iou_{name}_union']=int(((pred | target) & valid).sum())
    return result


def summarise(rows, tiles):
    lookup={r['tile']:r for r in rows}
    if len(lookup)!=len(rows) or set(lookup)!=set(tiles):
        raise ValueError('complete unique frozen region table required')
    block=lambda t:tuple(int(v)//2700 for v in t.split('_'))
    blocks=list(dict.fromkeys(map(block,tiles)))
    groups=[[t for t in tiles if block(t)==b] for b in blocks]
    keys=[k for k in rows[0] if k.startswith(('loss_','gain_')) or k=='crossed_i']
    values={k:np.array([np.mean([lookup[t][k] for t in group]) for group in groups]) for k in keys}
    index=np.random.Generator(np.random.PCG64(17017)).integers(0,len(blocks),(20000,len(blocks)))
    draws={k:v[index].mean(1) for k,v in values.items()}
    iou={}
    for key in rows[0]:
        if key.startswith('iou_') and key.endswith('_intersection'):
            uk=key.replace('_intersection','_union')
            vals=[]
            for group in groups:
                den=sum(lookup[t][uk] for t in group)
                vals.append(None if den==0 else sum(lookup[t][key] for t in group)/den)
            iou[key[4:-13]]={'blocks':vals,'mean':None if None in vals else float(np.mean(vals))}
    for pair in ('av','au','bu','bv'):
        if not all(pair+'_'+a in iou for a in ('12','21')):
            continue
        pair_means=[iou[pair+'_'+a]['mean'] for a in ('12','21')]
        iou[pair+'_assignment_average']=None if None in pair_means else float(np.mean(pair_means))
    return {'blocks':blocks,'rows':len(rows),'means':{k:float(v.mean()) for k,v in values.items()},
            'block_values':{k:v.tolist() for k,v in values.items()},
            'descriptive_95_intervals':{k:np.quantile(d,[.025,.975]).tolist() for k,d in draws.items()},
            'two_primary_bonferroni_97_5_intervals':{k:np.quantile(draws[k],[.0125,.9875]).tolist() for k in ('gain_a','gain_b')},
            'iou':iou,'scope':'Two fixed existing models; spatial post-hoc intervals, not seed variation or a fresh confirmation. Bonferroni coverage remains a bootstrap approximation.'}

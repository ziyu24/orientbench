"""Independent r014 raw/statistical verifier with executed negative-input checks."""
from __future__ import annotations
import argparse, csv, copy, json
from pathlib import Path
import numpy as np

NAMES = [f'{k}_{s}' for k in ('resnet50', 'vit_b16') for s in (1201, 1202, 1203)]

def require(condition: bool, message: str) -> None:
    if not condition: raise ValueError(message)

def inputs(raw_dir: Path, audit: Path, dataset: Path, g0: Path, arrays=None, records=None, eligible_override=None):
    arrays = arrays if arrays is not None else [dict(np.load(raw_dir / f'raw_{name}.npz')) for name in NAMES]
    require(len(arrays) == 6, 'six_models_required')
    needed = {'p_view','p_avg','error','object_id','component','labels','affected','model_sha256'}
    require(all(needed <= set(x) for x in arrays), 'raw_schema')
    base = arrays[0]; oid, component, labels = base['object_id'], base['component'], base['labels']
    require(len(oid) == 7416 and len(set(oid.tolist())) == 7416 and len(np.unique(component)) == 25, 'frozen_raw_universe')
    for row in arrays:
        p = row['p_view']; avg = row['p_avg']
        require(np.array_equal(row['object_id'], oid) and np.array_equal(row['component'], component) and np.array_equal(row['labels'], labels), 'raw_row_identity')
        require(np.isfinite(p).all() and (p >= 0).all() and (p <= 1).all() and np.allclose(p.sum(-1), 1, atol=1e-6), 'probability_range')
        require(np.array_equal(avg, p.mean(1)), 'two_view_average')
        require(np.array_equal(row['error'], (avg.argmax(-1) != labels[None]).astype(np.uint8)), 'argmax_error_contract')
    records = records if records is not None else [json.loads(x) for x in open(audit / 'source_records.jsonl') if '"partition": "calibration"' in x]
    require(len(records) == len(oid) and {int(x['object_id']) for x in records} == set(oid.tolist()), 'source_universe')
    with open(dataset / 'real/metadata_annotations/RarePlanes_Public_Metadata.csv', newline='') as stream: meta = list(csv.DictReader(stream))
    official = {(int(x['loc_id']), x['image_id'].split('_',1)[1]): x['image_id'] for x in meta}
    eligible = eligible_override if eligible_override is not None else {x['object_id']: x for x in json.load(open(g0.parent / 'eligible_manifest.json'))}
    for row in records:
        entry = eligible.get(row['object_id']); require(entry is not None, 'missing_g0_object')
        require(row['image_id'] == official.get((int(row['loc_id']),row['cat_id'])) == entry['source_cog'], 'source_identity')
        require(0 <= float(entry['theta']) < np.pi, 'theta_radian_canonical')
        require(float(entry['L']) >= float(entry['S']) > 0 and int(entry['canvas_side']) > 0, 'geometry_contract')
    return arrays, oid, component, labels

def statistic(arrays, component, labels):
    probability = np.array([x['p_avg'] for x in arrays]).reshape(2,3,3,len(labels),3,2)
    error = probability.argmax(-1) != labels[None,None,None]
    values = np.zeros((2,3,3,3,25,2)); present = np.zeros((3,25,2), bool)
    for attribute in range(3):
        for group in range(25):
            for klass in range(2):
                mask = (component == group) & (labels[:,attribute] == klass); present[attribute,group,klass] = mask.any()
                if mask.any(): values[:,:,:,attribute,group,klass] = error[:,:,:,mask,attribute].mean(-1)
    # The contract permits a class to be absent in an individual component;
    # component draws are aggregated over the components supporting that class.
    require(present.any(2).all() and present.any(1).all(), 'zero_class_denominator')
    rng=np.random.Generator(np.random.PCG64(12012)); draw=rng.integers(0,25,(50000,25)); w=np.zeros((50000,25));np.add.at(w,(np.arange(50000)[:,None],draw),1)
    def aggregate(weights):
        ans=np.empty((len(weights),2,3,3,3))
        for attribute in range(3):
            for arm in range(3):
                left=np.einsum('bj,msj->bms',weights,values[:,:,arm,attribute,:,0])/(weights@present[attribute,:,0])[:,None,None]
                right=np.einsum('bj,msj->bms',weights,values[:,:,arm,attribute,:,1])/(weights@present[attribute,:,1])[:,None,None]
                ans[:,:,:,attribute,arm]=.5*(left+right)
        return ans
    risk=aggregate(w); point=aggregate(np.ones((1,25)))[0]
    replicate=((risk[...,1]+risk[...,2])*.5-risk[...,0]).mean(2).reshape(50000,6); delta=((point[...,1]+point[...,2])*.5-point[...,0]).mean(1).reshape(6)
    def interval(x, point):
        sd=x.std(0,ddof=1); active=sd>0
        q=float(np.quantile(np.max(np.abs((x[:,active]-point[active])/sd[active]),axis=1),.95,method='linear')) if active.any() else 0.
        return sd,q,point-q*sd,point+q*sd
    sd,q,lo,hi=interval(replicate,delta); power=(.020+replicate-delta-q*sd>0).mean(0)
    clean=risk[...,0].mean(2).reshape(50000,6); cp=point[...,0].mean(1).reshape(6); cs,cq,clo,chi=interval(clean,cp)
    return {'delta':delta,'sd':sd,'q':q,'simultaneous_lower':lo,'simultaneous_upper':hi,'power':power,'clean_risk':cp,'clean_sd':cs,'clean_q':cq,'clean_simultaneous_lower':clo,'clean_simultaneous_upper':chi,'draw':draw,'zero_variance_q': interval(np.zeros((5,2)),np.zeros(2))[1:], 'risk':risk}

def rejects(fn):
    try: fn()
    except ValueError as error: return str(error)
    raise RuntimeError('mutation accepted')

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--raw',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--summary',type=Path,required=True);p.add_argument('--acceptance',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists(): raise RuntimeError('independent acceptance output exists')
    arrays,oid,component,labels=inputs(a.raw,a.audit,a.dataset,a.g0); actual=statistic(arrays,component,labels); published=json.load(open(a.summary))
    fields=('delta','sd','simultaneous_lower','simultaneous_upper','power','clean_risk','clean_sd','clean_simultaneous_lower','clean_simultaneous_upper')
    diff={x:float(np.max(np.abs(actual[x]-np.asarray(published[x]).reshape(-1)))) for x in fields};diff['q']=abs(actual['q']-published['q']);diff['clean_q']=abs(actual['clean_q']-published['clean_q'])
    bad_source=[json.loads(x) for x in open(a.audit/'source_records.jsonl') if '"partition": "calibration"' in x]; bad_source[0]['image_id']='not_an_official_source'
    one=copy.deepcopy(arrays); one[0]['labels']=one[0]['labels'].copy(); one[0]['labels'][0,0]=1-one[0]['labels'][0,0]
    two=copy.deepcopy(arrays); two[0]['p_avg']=two[0]['p_avg'].copy(); two[0]['p_avg'][:,[0,1]]=two[0]['p_avg'][:,[1,0]]
    three=copy.deepcopy(arrays); three[0]['p_view']=three[0]['p_view'].copy(); three[0]['p_view'][0,0,0,0,0]=np.nan
    four=copy.deepcopy(arrays); four[0]['p_view']=four[0]['p_view'].copy(); four[0]['p_view'][0,0,0,0]=[1.1,-.1]
    zero=copy.deepcopy(arrays); zero[0]['labels']=zero[0]['labels'].copy();zero[0]['labels'][:,0]=0
    bad_geometry={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))}; bad_geometry[oid[0]]=dict(bad_geometry[oid[0]],theta=90.)
    mutation={'wrong_source':rejects(lambda:inputs(a.raw,a.audit,a.dataset,a.g0,records=bad_source)),'wrong_label_row':rejects(lambda:inputs(a.raw,a.audit,a.dataset,a.g0,arrays=one)),'wrong_probability_row':rejects(lambda:inputs(a.raw,a.audit,a.dataset,a.g0,arrays=two)),'nan':rejects(lambda:inputs(a.raw,a.audit,a.dataset,a.g0,arrays=three)),'out_of_range_probability':rejects(lambda:inputs(a.raw,a.audit,a.dataset,a.g0,arrays=four)),'missing_model':rejects(lambda:inputs(a.raw,a.audit,a.dataset,a.g0,arrays=arrays[:-1])),'zero_class_denominator':rejects(lambda:statistic(zero,component,zero[0]['labels'])),'degree_radian':rejects(lambda:inputs(a.raw,a.audit,a.dataset,a.g0,eligible_override=bad_geometry))}
    order=np.arange(len(oid))[::-1];reordered=[]
    for z in arrays:
        reordered.append({k:(v[:, :, order] if k=='p_view' else v[:,order] if k in ('p_avg','error') else v[order] if k in ('object_id','component','labels','affected') else v) for k,v in z.items()})
    inputs(a.raw,a.audit,a.dataset,a.g0,arrays=reordered)
    acceptance=json.load(open(a.acceptance)); identity=bool(acceptance['original_execution_identity_recoverable'])
    reason='POWER' if identity and all(x>=.8 for x in actual['power']) else ('INPUT_OR_IMPLEMENTATION' if not identity else 'POWER')
    out={'protocol':'r014-independent-acceptance-v1','objects':len(oid),'components':len(np.unique(component)),'published_max_abs_difference':max(diff.values()),'field_differences':diff,'mutations':mutation,'all_mutations_rejected':len(mutation)==8,'reorder_accepted':True,'zero_variance_q':actual['zero_variance_q'][0],'original_execution_identity_recoverable':identity,'decision':{'status':'INCONCLUSIVE_R013_H1A','reason':reason,'test_opened':False,'models_retrained':False}}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()

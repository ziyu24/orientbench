"""Read-only host checks: existing hashes, logs, actual CPU rendering, and loss counterexamples."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main(root):
    torch.set_num_threads(1)
    sys.path.insert(0,str(root/'src'))
    from orientbench.r015.data import render, MEAN, STD
    base=root/'runs/r015/artifacts'
    pre=json.loads((base/'preflight.json').read_text())
    manifest=json.loads((base/'windows/manifest.json').read_text())['objects']
    fits=[]
    for p in sorted((base/'fits/fits').glob('*/train.json')):
        d=json.loads(p.read_text());logs=d['epochs'];model=p.parent/'epoch40.pt'
        fits.append({'tag':d['tag'],'epochs':len(logs),'sequential': [x['epoch'] for x in logs]==list(range(1,41)),
                     'steps':logs[-1]['optimizer_steps'],'objects':sorted(set(x['objects'] for x in logs)),
                     'final_sha256':sha(model),'registered_sha256':d['final_sha256'],
                     'epoch30_exists':(p.parent/'epoch30.pt').is_file(),
                     'fixed_loss30':logs[29]['fixed_train_loss'],'fixed_loss40':logs[39]['fixed_train_loss'],
                     'final_mtime':model.stat().st_mtime})
    assert len(fits)==36 and all(x['final_sha256']==x['registered_sha256'] for x in fits)
    chosen={}
    for r in sorted(pre['records']['train']+pre['records']['calibration'],key=lambda r:r['object_id']):
        chosen.setdefault(r['image_id'],r)
    checks=[];count=0;maxdiff=0.;maxpair=0.;maxcanonical=0.
    for image,r in chosen.items():
      p=base/'windows'/manifest[str(r['object_id'])]['window']
      raw=np.load(p,allow_pickle=False);x=torch.from_numpy(raw.transpose(2,0,1).copy()).float()[None]/255.
      assert hashlib.sha256(raw.tobytes()).hexdigest()==r['window_sha256']
      for n in (96,224):
       z=2*n;u=(2*np.arange(z,dtype=np.float64)+1)/z-1;v,w=np.meshgrid(u,u,indexing='ij')
       for strategy in ('I','O','T'):
        phi=float(np.random.Generator(np.random.PCG64(np.random.SeedSequence([15015,r['object_id']]))).uniform(0,math.pi)) if strategy=='I' else 0.
        angle=phi if strategy=='I' else r['theta']
        rho=.6*math.hypot(r['L'],r['S']);ax=.6*r['L'] if strategy=='T' else rho;ay=.6*r['S'] if strategy=='T' else rho
        c,s=math.cos(angle),math.sin(angle)
        px=c*ax*w-s*ay*v+r['center'][0]-r['origin']['left']
        py=s*ax*w+c*ay*v+r['center'][1]-r['origin']['top']
        mask=np.ones((z,z),bool) if strategy=='T' else w*w+v*v<=1
        ix=np.floor(px).astype(int);iy=np.floor(py).astype(int)
        assert np.all(ix[mask]>=0) and np.all(iy[mask]>=0)
        assert np.all(ix[mask]+1<raw.shape[1]) and np.all(iy[mask]+1<raw.shape[0])
        dx=px-ix;dy=py-iy;ix=np.clip(ix,0,raw.shape[1]-2);iy=np.clip(iy,0,raw.shape[0]-2)
        ref=(raw[iy,ix]*(1-dx)[...,None]*(1-dy)[...,None]+raw[iy,ix+1]*dx[...,None]*(1-dy)[...,None]+raw[iy+1,ix]*(1-dx)[...,None]*dy[...,None]+raw[iy+1,ix+1]*dx[...,None]*dy[...,None])/255.
        ref[~mask]=[.485,.456,.406];ref=ref.reshape(n,2,n,2,3).mean((1,3))
        a=render(x,[r],strategy,n,15015,0,False,eval_phi='fixed')
        rgb=(a*STD[None,:,None,None]+MEAN[None,:,None,None])[0].permute(1,2,0).numpy()
        diff=float(np.max(np.abs(rgb-ref))); maxdiff=max(maxdiff,diff);count+=1
        if strategy!='I':
            rpi=dict(r,theta=r['theta']+math.pi)
            b=render(x,[rpi],strategy,n,15015,0,True,eval_phi='fixed')
            pair=float(torch.max(torch.abs(a-b)*STD[None,:,None,None]));maxpair=max(maxpair,pair)
            # Equivalent raw box -> canonical long-side representation.
            swapped=dict(r,L=r['S'],S=r['L'],theta=r['theta']+math.pi/2)
            if swapped['L']<swapped['S']:
                swapped['L'],swapped['S']=swapped['S'],swapped['L'];swapped['theta']+=math.pi/2
            b=render(x,[swapped],strategy,n,15015,0,True,eval_phi='fixed')
            maxcanonical=max(maxcanonical,float(torch.max(torch.abs(a-b)*STD[None,:,None,None])))
        checks.append({'source':image,'object_id':r['object_id'],'size':n,'strategy':strategy,'rgb_max_abs':diff})
    # Explicit counterexamples: no fitted model or image outcome involved.
    z1=torch.tensor([[8.,0.]],dtype=torch.float64);z2=torch.tensor([[0.,8.]],dtype=torch.float64);y=torch.tensor([0])
    avg_loss=(F.cross_entropy(z1,y)+F.cross_entropy(z2,y))/2
    loss_avg=F.cross_entropy((z1+z2)/2,y)
    logits=torch.tensor([[2.,0.],[1.,0.],[0.,2.]],dtype=torch.float64);yy=torch.tensor([0,0,1]);ww=torch.tensor([.6,3.],dtype=torch.float64)
    mandated=(F.cross_entropy(logits,yy,reduction='none')*ww[yy]).mean()
    implemented=F.cross_entropy(logits,yy,weight=ww)
    evaluation=list((base/'evaluation').glob('*/probabilities.npz'))
    print(json.dumps({'fit_count':len(fits),'fits':fits,'source_samples':len(chosen),'render_cases':count,
                     'rgb_max_abs':maxdiff,'pi_pair_max_abs':maxpair,'canonical_pair_max_abs':maxcanonical,
                     'reference_tolerance':1e-4,'render_checks':checks,
                     'loss_examples':{'average_view_losses':float(avg_loss),'loss_of_average_logits':float(loss_avg),
                                      'fixed_object_denominator':float(mandated),'batch_weight_denominator':float(implemented)},
                     'mtime_only':{'last_model':max(x['final_mtime'] for x in fits),
                                   'first_evaluation':min(x.stat().st_mtime for x in evaluation)},
                     'scope':'No model forward/backward or training; 175 cached source windows checked, not all original COG pixels.'},
                    sort_keys=True))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();main(a.root)

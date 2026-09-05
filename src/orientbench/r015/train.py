"""Frozen 36-fit r015 supervisor; no calibration is read before every fit is complete."""
from __future__ import annotations
import argparse,hashlib,json,math,os,random,time,sys
from pathlib import Path
import numpy as np,torch
from torch import nn
from torch.utils.data import DataLoader
import torch.multiprocessing as mp
sys.path.insert(0,str(Path(__file__).parents[2]))
from orientbench.r015.data import Windows,collate,render
from orientbench.r015.model import Heads,initialize
SEEDS=(1501,1502,1503);STRATEGIES=('I','O','T');SIZES=(96,224);KINDS=('resnet50','vit_b16')
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def rows(preflight,windows):
 p=json.load(open(preflight));m=json.load(open(windows/'manifest.json'))['objects'];out=[]
 for r in p['records']['train']:
  q=dict(r);q['window']=m[str(r['object_id'])]['window'];out.append(q)
 if len(out)!=4065:return None
 return out
def run(job,device,records,window_root,out):
 strategy,kind,size,seed=job;tag=f'{strategy}_{kind}_{size}_{seed}';target=out/'fits'/tag
 if target.exists():raise RuntimeError(('duplicate_fit',tag))
 target.mkdir(parents=True);torch.cuda.set_device(device);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);np.random.seed(seed);random.seed(seed);torch.backends.cudnn.deterministic=True
 model=Heads(kind,size).to(device);initial=initialize(model);initial_hash=sha(initial);ds=Windows(records,window_root);labels=np.asarray([r['labels'] for r in records]);weights=torch.tensor([[len(labels)/(2*(labels[:,a]==k).sum()) for k in range(2)]for a in range(3)],device=device,dtype=torch.float32);opt=torch.optim.AdamW(model.parameters(),lr=3e-4,weight_decay=1e-4);steps=math.ceil(len(ds)/24);total=40*steps
 def lr(step):return (step+1)/(2*steps) if step<2*steps else 3e-6/3e-4+.5*(1-3e-6/3e-4)*(1+math.cos(math.pi*(step-2*steps)/(total-2*steps)))
 def fixed_loss():
  model.eval();values=[];dl=DataLoader(ds,batch_size=24,shuffle=False,num_workers=2,pin_memory=True,collate_fn=collate)
  with torch.no_grad():
   for x,batch in dl:
    x=x.to(device,non_blocking=True);left=render(x,batch,strategy,size,seed,0,False,eval_phi='fixed');right=render(x,batch,strategy,size,seed,0,True,eval_phi='fixed');o=(model(left)+model(right))/2;y=torch.tensor([r['labels'] for r in batch],device=device);values.append(float(sum(nn.functional.cross_entropy(o[:,j],y[:,j],weight=weights[j]) for j in range(3))/3))
  return float(np.mean(values))
 log=[];step=0
 def checkpoint(epoch,path):
  torch.save({'protocol':'r015-matched-support-v1','strategy':strategy,'kind':kind,'size':size,'seed':seed,'epoch':epoch,'state_dict':model.state_dict(),'optimizer':opt.state_dict(),'sampler':{'scheme':'epoch_lexical_pcg64','seed':seed*1000+epoch},'rng':{'python':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),'cuda':torch.cuda.get_rng_state(device)}},path)
 for epoch in range(40):
  generator=torch.Generator().manual_seed(seed*1000+epoch);dl=DataLoader(ds,batch_size=24,shuffle=True,generator=generator,num_workers=2,pin_memory=True,collate_fn=collate)
  model.train();losses=[]
  for x,batch in dl:
   x=x.to(device,non_blocking=True);a=render(x,batch,strategy,size,seed,epoch,False);b=render(x,batch,strategy,size,seed,epoch,True);o=(model(a)+model(b))/2;y=torch.tensor([r['labels'] for r in batch],device=device)
   loss=sum(nn.functional.cross_entropy(o[:,j],y[:,j],weight=weights[j]) for j in range(3))/3;opt.zero_grad();loss.backward();opt.step();step+=1
   for group in opt.param_groups:group['lr']=3e-4*lr(step)
   losses.append(float(loss.detach()))
  log.append({'epoch':epoch+1,'mean_train_loss':float(np.mean(losses)),'lr':opt.param_groups[0]['lr'],'optimizer_steps':step,'objects':len(ds)})
  # This overwrite is the exact recovery checkpoint; epoch30/40 are retained evidence.
  checkpoint(epoch+1,target/'resume.pt')
  if epoch+1 in (30,40):
   log[-1]['fixed_train_loss']=fixed_loss();checkpoint(epoch+1,target/f'epoch{epoch+1}.pt')
 (target/'train.json').write_text(json.dumps({'tag':tag,'initialization_sha256':initial_hash,'epochs':log,'final_sha256':sha(target/'epoch40.pt')},sort_keys=True,indent=2)+'\n')
def worker(rank,jobs,records,window_root,out):
 for job in jobs[rank::4]:run(job,rank,records,window_root,out)
def main():
 p=argparse.ArgumentParser();p.add_argument('--preflight',type=Path,required=True);p.add_argument('--windows',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise RuntimeError('r015 train output exists')
 pre=json.load(open(a.preflight));
 if not pre['render_pass'] or pre['counts']!={'train':4065,'calibration':7416}:raise RuntimeError('preflight gate')
 r=rows(a.preflight,a.windows)
 if r is None:raise RuntimeError('training universe')
 a.out.mkdir(parents=True);jobs=[(s,k,n,seed) for s in STRATEGIES for k in KINDS for n in SIZES for seed in SEEDS]
 if len(jobs)!=36 or torch.cuda.device_count()!=4:raise RuntimeError(('contract_gpu_or_jobs',torch.cuda.device_count(),len(jobs)))
 mp.spawn(worker,args=(jobs,r,a.windows,a.out),nprocs=4,join=True)
 fits=sorted((a.out/'fits').glob('*/train.json')); 
 if len(fits)!=36:raise RuntimeError(('incomplete',len(fits)))
 (a.out/'manifest.json').write_text(json.dumps({'protocol':'r015-matched-support-v1','fits':[json.load(open(x)) for x in fits],'calibration_opened':False,'test_opened':False},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()

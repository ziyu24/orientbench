"""r015 GPU render operator and materialized-window dataset."""
from __future__ import annotations
import math,json
from pathlib import Path
import numpy as np,torch
import torch.nn.functional as F
from torch.utils.data import Dataset
MEAN=torch.tensor([.485,.456,.406]);STD=torch.tensor([.229,.224,.225])
class Windows(Dataset):
 def __init__(self,records,root):self.rows=records;self.root=Path(root)
 def __len__(self):return len(self.rows)
 def __getitem__(self,i):
  r=self.rows[i];a=np.load(self.root/r['window'],allow_pickle=False);return torch.from_numpy(a.transpose(2,0,1)).float()/255.,r
def collate(batch):
 size=max(x.shape[-1] for x,_ in batch);out=torch.zeros((len(batch),3,size,size));rows=[]
 for i,(x,r) in enumerate(batch):out[i,:,:x.shape[-2],:x.shape[-1]]=x;rows.append(r)
 return out,rows
def angle(seed,epoch,object_id,strategy):
 rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,epoch,object_id])))
 return float(rng.uniform(0,math.pi) if strategy=='I' else rng.uniform(-math.pi/18,math.pi/18))
def render(windows,rows,strategy,n,seed,epoch,second=False,eval_phi=None,view_offset=0.0):
 device=windows.device;b=len(rows);z=2*n;u=torch.arange(z,device=device,dtype=torch.float32)*(2/z)+(-1+1/z);v=u;yy,xx=torch.meshgrid(v,u,indexing='ij');L=torch.tensor([r['L'] for r in rows],device=device)[:,None,None];S=torch.tensor([r['S'] for r in rows],device=device)[:,None,None];rho=.60*torch.sqrt(L.square()+S.square());theta=[]
 for r in rows:
  if eval_phi == 'fixed':
   base=float(np.random.Generator(np.random.PCG64(np.random.SeedSequence([15015,r['object_id']]))).uniform(0,math.pi))+view_offset if strategy=='I' else view_offset
  else: base=eval_phi if eval_phi is not None else angle(seed,epoch,r['object_id'],strategy)
  theta.append(base if strategy=='I' else float(r['theta'])+base)
 t=torch.tensor(theta,device=device)[:,None,None]+(math.pi if second else 0.);c,s=torch.cos(t),torch.sin(t);cx=torch.tensor([r['center'][0]-r['origin']['left'] for r in rows],device=device)[:,None,None];cy=torch.tensor([r['center'][1]-r['origin']['top'] for r in rows],device=device)[:,None,None]
 if strategy=='T':ax=.60*L;ay=.60*S;mask=None
 else:ax=ay=rho;mask=(xx.square()+yy.square()<=1)[None,None]
 # collate pads each real window at top-left.  grid_sample coordinates must use
 # the common padded canvas, not a row's original side length.
 canvas_h,canvas_w=windows.shape[-2:]
 px=c*ax*xx-s*ay*yy+cx;py=s*ax*xx+c*ay*yy+cy;grid=torch.stack((2*(px+.5)/canvas_w-1,2*(py+.5)/canvas_h-1),-1);out=F.grid_sample(windows,grid,mode='bilinear',padding_mode='zeros',align_corners=False)
 if mask is not None:out=torch.where(mask,out,MEAN.to(device)[None,:,None,None])
 out=F.avg_pool2d(out,2);return (out-MEAN.to(device)[None,:,None,None])/STD.to(device)[None,:,None,None]

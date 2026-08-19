#!/usr/bin/env python3
"""Frozen r048 P2C-Lift and fair direct baselines; train/val only."""
import argparse, json, math, os, random, sys, xml.etree.ElementTree as ET
from pathlib import Path
import cv2, numpy as np, torch
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import Dataset,DataLoader,DistributedSampler
from torchvision.models import resnet50
DATA=Path('/home/rspip/cqc/data/dataset/HRSC2016'); PTH=Path('/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth')
MEAN=torch.tensor([123.675,116.28,103.53]).view(3,1,1); STD=torch.tensor([58.395,57.12,57.375]).view(3,1,1)
if not hasattr(np,'_core'):
 sys.modules.setdefault('numpy._core',np.core);sys.modules.setdefault('numpy._core.multiarray',np.core.multiarray);sys.modules.setdefault('numpy._core.numeric',np.core.numeric)
def rows(split):
 out=[]
 for iid in (DATA/'splits'/f'{split}.txt').read_text().split():
  root=ET.parse(DATA/'annfiles'/f'{iid}.xml').getroot()
  for j,o in enumerate(root.findall('HRSC_Objects/HRSC_Object')):
   f=lambda k:float(o.find(k).text);cx,cy,w,h,a,hx,hy=[f(k) for k in ('mbox_cx','mbox_cy','mbox_w','mbox_h','mbox_ang','header_x','header_y')]
   if h>w:w,h,a=h,w,a+math.pi/2
   a=(a+math.pi/2)%math.pi-math.pi/2; dx,dy=hx-cx,hy-cy;u=(math.cos(a),math.sin(a))
   if math.hypot(dx,dy)<.1*w or abs(dx*u[0]+dy*u[1])<.1*w:continue
   out.append((iid,cx,cy,w,h,a,int(dx*u[0]+dy*u[1]>0)))
 return out
def crop(r,aug=False):
 iid,cx,cy,w,h,a,y=r;im=cv2.imread(str(DATA/'images'/f'{iid}.bmp'))
 if aug:
  cx+=random.uniform(-.05,.05)*w;cy+=random.uniform(-.05,.05)*h;s=random.uniform(.9,1.1);w*=s;h*=s;a+=math.radians(random.uniform(-10,10))
 M=cv2.getRotationMatrix2D((cx,cy),math.degrees(a),1);M[0,2]+=96-cx;M[1,2]+=32-cy
 z=cv2.warpAffine(im,M,(192,64),borderMode=cv2.BORDER_REFLECT);z=torch.from_numpy(cv2.cvtColor(z,cv2.COLOR_BGR2RGB).copy()).permute(2,0,1).float();z=(z-MEAN)/STD
 if aug and random.random()<.5:z=torch.flip(z,[2]);y=1-y
 return z[:,:,:64],z[:,:,128:],z,torch.tensor(y,dtype=torch.float32)
class DS(Dataset):
 def __init__(self,r,a):self.r,self.a=r,a
 def __len__(self):return len(self.r)
 def __getitem__(self,i):return crop(self.r[i],self.a)
def backbone():
 b=resnet50(weights=None);x=torch.load(PTH,map_location='cpu')['state_dict'];mp={k[9:]:v for k,v in x.items() if k.startswith('backbone.') and k[9:] in b.state_dict() and b.state_dict()[k[9:]].shape==v.shape};miss,_=b.load_state_dict(mp,strict=False)
 if len(mp)<200 or any(k.startswith(('conv1','layer')) for k in miss):raise RuntimeError('registered R50 mapping failed')
 for n,p in b.named_parameters():
  if n.startswith(('conv1','bn1','layer1','layer2','layer3','fc.')):p.requires_grad=False
 return b,len(mp)
class M(nn.Module):
 def __init__(self,mode,hidden=384):
  super().__init__();self.mode=mode;self.b,self.mapped=backbone();self.proj=nn.Linear(2048,hidden);self.tok=nn.TransformerEncoder(nn.TransformerEncoderLayer(hidden,8,hidden*2,batch_first=True),num_layers=2)
  self.head=nn.Linear(hidden*(3 if mode=='CONCAT_ENDPOINT_BINARY' else 1),2 if mode in ('HEADPOINT_2D','P2C_LIFT') else 1)
  if mode=='P2C_LIFT':self.axis=nn.Linear(hidden,3);self.pole=nn.Linear(hidden,1)
 def feat(self,x):
  x=self.b.relu(self.b.bn1(self.b.conv1(x)));x=self.b.maxpool(x);x=self.b.layer1(x);x=self.b.layer2(x);x=self.b.layer3(x);return self.b.avgpool(self.b.layer4(x)).flatten(1)
 def forward(self,a,b,g):
  fa,fb,fg=self.feat(a),self.feat(b),self.feat(g)
  if self.mode=='WHOLE_CROP_BINARY':return self.head(self.proj(fg)),None
  if self.mode=='CONCAT_ENDPOINT_BINARY':return self.head(torch.cat([self.proj(fa),self.proj(fb),self.proj(fg)],1)),None
  if self.mode=='HEADPOINT_2D':return self.head(self.proj(fg)),None
  if self.mode=='DIRECT_S1_VM':return self.head(self.proj(fg)),None
  t=self.tok(torch.stack([self.proj(fg),self.proj(fa),self.proj(fb)],1));h=t[:,0]+t[:,2]-t[:,1];return self.pole(h),self.axis(h)
def score(z,mode):return z[:,0] if z.ndim==2 and z.shape[1]>1 else z.flatten()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',required=True,choices=['P2C_LIFT','WHOLE_CROP_BINARY','CONCAT_ENDPOINT_BINARY','HEADPOINT_2D','DIRECT_S1_VM']);ap.add_argument('--out',required=True);ap.add_argument('--epochs',type=int,default=30);ap.add_argument('--smoke',action='store_true');ap.add_argument('--smoke-iterations',type=int,default=200);a=ap.parse_args();rank=int(os.getenv('LOCAL_RANK','0'));world=int(os.getenv('WORLD_SIZE','1'))
 if world>1:dist.init_process_group('nccl');torch.cuda.set_device(rank)
 random.seed(20260819);np.random.seed(20260819);torch.manual_seed(20260819);dev=torch.device('cuda',rank) if torch.cuda.is_available() else torch.device('cpu');tr,va=rows('train'),rows('val');sam=DistributedSampler(DS(tr,True),shuffle=True) if world>1 else None;dl=DataLoader(DS(tr,True),batch_size=64//world,sampler=sam,shuffle=sam is None,num_workers=4,pin_memory=True);vl=DataLoader(DS(va,False),batch_size=64,num_workers=4)
 m=M(a.mode).to(dev);m=DDP(m,device_ids=[rank],find_unused_parameters=True) if world>1 else m;opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],1e-4,weight_decay=.05);sc=torch.cuda.amp.GradScaler(enabled=dev.type=='cuda');out=Path(a.out);out.mkdir(parents=True,exist_ok=True);best=-1;epochs=999 if a.smoke else a.epochs;iters=0
 for ep in range(epochs):
  if sam:sam.set_epoch(ep)
  m.train()
  for xm,xp,g,y in dl:
   xm,xp,g,y=[q.to(dev) for q in (xm,xp,g,y)]
   with torch.cuda.amp.autocast(enabled=dev.type=='cuda'):
    z,aux=m(xm,xp,g);log=score(z,a.mode);loss=nn.functional.binary_cross_entropy_with_logits(log,y)
    if a.mode=='HEADPOINT_2D':loss=nn.functional.mse_loss(z,torch.stack([y*2-1,torch.zeros_like(y)],1))
    if a.mode=='P2C_LIFT':loss=loss+.25*nn.functional.mse_loss(aux[:,:2],torch.stack([torch.ones_like(y),torch.zeros_like(y)],1))+.25*nn.functional.mse_loss(aux[:,2],torch.ones_like(y))
   opt.zero_grad();sc.scale(loss).backward();sc.step(opt);sc.update()
   iters+=1
   if a.smoke and iters>=a.smoke_iterations:break
  m.eval();n=ok=0
  with torch.no_grad():
   for xm,xp,g,y in vl:
    xm,xp,g,y=[q.to(dev) for q in (xm,xp,g,y)];z,_=m(xm,xp,g);pr=score(z,a.mode)>0;ok+=int((pr==y.bool()).sum());n+=len(y)
  rec={'epoch':ep+1,'val_accuracy':ok/n,'world_size':world,'mode':a.mode};
  if rank==0:
   with (out/'epochs.jsonl').open('a') as f:f.write(json.dumps(rec)+'\n')
   torch.save((m.module if isinstance(m,DDP) else m).state_dict(),out/'latest.pt')
   if rec['val_accuracy']>best:best=rec['val_accuracy'];torch.save((m.module if isinstance(m,DDP) else m).state_dict(),out/'best.pt')
  if a.smoke and iters>=a.smoke_iterations:break
 if rank==0:(out/'summary.json').write_text(json.dumps({'mode':a.mode,'best_val_accuracy':best,'train_instances':len(tr),'val_instances':len(va),'formal':not a.smoke,'four_rank_ddp':world==4},indent=2)+'\n')
 if world>1:dist.barrier();dist.destroy_process_group()
if __name__=='__main__':main()

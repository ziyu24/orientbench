#!/usr/bin/env python3
"""Formal r048 model/baseline training; train/val only, no test access."""
import argparse,json,math,os,sys,numpy as np,torch
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader,DistributedSampler
from torchvision.models import resnet50
sys.path.insert(0,os.path.dirname(__file__))
from data_contract import records,HeadingDS
from p2c_distribution import P2CHeads,axial_vm_nll,distribution_kl,intrinsic_confidence,circular_bayes_action,wrap
from metrics_g1 import summary
if not hasattr(np,'_core'):
 sys.modules.setdefault('numpy._core',np.core);sys.modules.setdefault('numpy._core.multiarray',np.core.multiarray);sys.modules.setdefault('numpy._core.numeric',np.core.numeric)
PTH='/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth'
def enc():
 b=resnet50(weights=None);x=torch.load(PTH,map_location='cpu')['state_dict'];m={k[9:]:v for k,v in x.items() if k.startswith('backbone.') and k[9:] in b.state_dict() and b.state_dict()[k[9:]].shape==v.shape};b.load_state_dict(m,strict=False)
 for n,p in b.named_parameters():p.requires_grad=not n.startswith(('conv1','bn1','layer1','layer2','layer3','fc.'))
 return b
class Net(nn.Module):
 def __init__(self,kind,hid=384,layers=3):
  super().__init__();self.kind=kind;self.b=enc();self.p=nn.Linear(2048,hid);self.t=nn.TransformerEncoder(nn.TransformerEncoderLayer(hid,8,hid*2,batch_first=True),layers);self.p2c=P2CHeads(hid);self.head=nn.Linear(hid*(3 if kind=='CONCAT_ENDPOINT_BINARY' else 1),2 if kind in ('HEADPOINT_2D','DIRECT_S1_VM') else 1)
 def f(self,x):
  x=self.b.relu(self.b.bn1(self.b.conv1(x)));x=self.b.maxpool(x);x=self.b.layer1(x);x=self.b.layer2(x);x=self.b.layer3(x);return self.b.avgpool(self.b.layer4(x)).flatten(1)
 def forward(self,a,b,g):
  fa,fb,fg=self.f(a),self.f(b),self.f(g)
  if self.kind=='P2C_LIFT':return self.p2c(self.t(torch.stack([self.p(fg),self.p(fa),self.p(fb)],1))[:,0])
  z=self.p(fg) if self.kind!='CONCAT_ENDPOINT_BINARY' else torch.cat([self.p(fg),self.p(fa),self.p(fb)],1);return self.head(z)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kind',required=True,choices=['P2C_LIFT','WHOLE_CROP_BINARY','CONCAT_ENDPOINT_BINARY','HEADPOINT_2D','DIRECT_S1_VM']);ap.add_argument('--out',required=True);ap.add_argument('--hid',type=int,default=384);ap.add_argument('--layers',type=int,default=3);ap.add_argument('--epochs',type=int,default=30);a=ap.parse_args();rank=int(os.getenv('LOCAL_RANK','0'));world=int(os.getenv('WORLD_SIZE','1'))
 if world>1:dist.init_process_group('nccl');torch.cuda.set_device(rank)
 dev=torch.device('cuda',rank);tr,va=records('train'),records('val');sam=DistributedSampler(HeadingDS(tr,True)) if world>1 else None;dl=DataLoader(HeadingDS(tr,True),64//world,sampler=sam,shuffle=sam is None,num_workers=4);vl=DataLoader(HeadingDS(va,False),64,num_workers=4)
 m=Net(a.kind,a.hid,a.layers).to(dev);m=DDP(m,device_ids=[rank],find_unused_parameters=True);op=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=1e-4,weight_decay=.05);out=os.path.abspath(a.out);os.makedirs(out,exist_ok=True);best=-1
 for ep in range(a.epochs):
  sam.set_epoch(ep);m.train()
  for am,bm,g,t,aa,ba,ga,ta,rot in dl:
   am,bm,g,t,aa,ba,ga,ta=[z.to(dev) for z in (am,bm,g,t,aa,ba,ga,ta)];op.zero_grad()
   if a.kind=='P2C_LIFT':
    mu,k,p,v=m(am,bm,g);rel=t[:,1];pole=(torch.cos(rel)>0).float();loss=axial_vm_nll(rel,mu,k)+nn.functional.binary_cross_entropy_with_logits(p,pole)+.25*nn.functional.mse_loss(v,t[:,2:])
    mu2,k2,p2,_=m(aa,ba,ga);loss=loss+.25*distribution_kl(mu2,k2,p2,mu,k,p)
   else:
    z=m(am,bm,g);phi=t[:,0];
    if a.kind=='HEADPOINT_2D':loss=nn.functional.mse_loss(torch.tanh(z),t[:,2:])
    elif a.kind=='DIRECT_S1_VM':loss=nn.functional.mse_loss(torch.tanh(z),torch.stack([torch.cos(phi),torch.sin(phi)],1))
    else:loss=nn.functional.binary_cross_entropy_with_logits(z.flatten(),(torch.cos(t[:,1])>0).float())
   loss.backward();op.step()
  m.eval();ph=[];pr=[];cf=[];pb=[]
  with torch.no_grad():
   for am,bm,g,t,*_ in vl:
    am,bm,g=[z.to(dev) for z in (am,bm,g)];z=m(am,bm,g);ph+=t[:,0].tolist()
    if a.kind=='P2C_LIFT':mu,k,p,v=z;pr+=circular_bayes_action(mu,p).tolist();cf+=intrinsic_confidence(k,p).tolist();pb+=torch.sigmoid(p).tolist()
    elif a.kind=='HEADPOINT_2D':q=torch.tanh(z);pr+=torch.atan2(q[:,1],q[:,0]).tolist();cf+=q.norm(dim=1).clamp(0,1).tolist();pb+=cf[-len(q):]
    elif a.kind=='DIRECT_S1_VM':q=torch.tanh(z);pr+=torch.atan2(q[:,1],q[:,0]).tolist();cf+=q.norm(dim=1).clamp(0,1).tolist();pb+=cf[-len(q):]
    else:q=z.flatten();pr+=torch.where(q>0,torch.zeros_like(q),torch.full_like(q,math.pi)).tolist();cf+=torch.sigmoid(q).sub(.5).abs().mul(2).tolist();pb+=torch.sigmoid(q).tolist()
  met=summary(ph,pr,pb,cf);met['epoch']=ep+1
  if rank==0:
   open(out+'/epochs.jsonl','a').write(json.dumps(met)+'\n');torch.save(m.module.state_dict(),out+'/latest.pt')
   if met['accuracy']>best:best=met['accuracy'];torch.save(m.module.state_dict(),out+'/best.pt')
 if rank==0:open(out+'/summary.json','w').write(json.dumps({'kind':a.kind,'best_accuracy':best,'hid':a.hid,'layers':a.layers,'formal':True},indent=2))
 if world>1:dist.destroy_process_group()
if __name__=='__main__':main()

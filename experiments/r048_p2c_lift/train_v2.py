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
from p2c_distribution import (P2CHeads, axial_vm_nll, equivariance_kl,
    intrinsic_confidence, circular_bayes_action, pole_logit, p2c_logprob,
    probability_within, vm_logprob, wrap)
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
  super().__init__();self.kind=kind;self.b=enc();self.p=nn.Linear(2048,hid);self.t=nn.TransformerEncoder(nn.TransformerEncoderLayer(hid,8,hid*2,batch_first=True),layers);self.p2c=P2CHeads(hid);self.head=nn.Linear(hid*(3 if kind=='CONCAT_ENDPOINT_BINARY' else 1),3 if kind=='DIRECT_S1_VM' else (2 if kind=='HEADPOINT_2D' else 1))
  for q in self.b.modules():
   if isinstance(q,nn.BatchNorm2d):q.eval()
 def f(self,x):
  self.b.eval()
  x=self.b.relu(self.b.bn1(self.b.conv1(x)));x=self.b.maxpool(x);x=self.b.layer1(x);x=self.b.layer2(x);x=self.b.layer3(x);return self.b.avgpool(self.b.layer4(x)).flatten(1)
 def forward(self,a,b,g):
  fa,fb,fg=self.f(a),self.f(b),self.f(g)
  tokens=torch.stack([self.p(fg),self.p(fa),self.p(fb)],1)
  if self.kind=='P2C_LIFT':return self.p2c(self.t(tokens)[:,0])
  # Whole-crop baselines deliberately receive no signed endpoint appearance;
  # repeated global tokens retain the same declared transformer parameter budget.
  if self.kind=='CONCAT_ENDPOINT_BINARY':z=self.t(tokens).flatten(1)
  else:z=self.t(tokens[:,0:1].expand(-1,3,-1))[:,0]
  return self.head(z)
def direct_params(z):
 return torch.atan2(z[:,1],z[:,0]),torch.nn.functional.softplus(z[:,2])+1e-4
def direct_mass(pred,mu,kappa):
 g=torch.linspace(-math.pi,math.pi,144,device=mu.device)[None,:];w=torch.softmax(vm_logprob(g,mu[:,None],kappa[:,None]),1);return (w*(torch.abs(wrap(g-pred[:,None]))<math.pi/2)).sum(1)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kind',required=True,choices=['P2C_LIFT','WHOLE_CROP_BINARY','CONCAT_ENDPOINT_BINARY','HEADPOINT_2D','DIRECT_S1_VM']);ap.add_argument('--out',required=True);ap.add_argument('--hid',type=int,default=384);ap.add_argument('--layers',type=int,default=3);ap.add_argument('--epochs',type=int,default=30);ap.add_argument('--max-steps',type=int,default=0);ap.add_argument('--w-vector',type=float,default=.25);ap.add_argument('--w-equiv',type=float,default=.25);a=ap.parse_args();rank=int(os.getenv('LOCAL_RANK','0'));world=int(os.getenv('WORLD_SIZE','1'))
 if world>1:dist.init_process_group('nccl');torch.cuda.set_device(rank)
 dev=torch.device('cuda',rank);tr,va=records('train'),records('val');sam=DistributedSampler(HeadingDS(tr,True)) if world>1 else None;dl=DataLoader(HeadingDS(tr,True),64//world,sampler=sam,shuffle=sam is None,num_workers=4);vl=DataLoader(HeadingDS(va,False),64,num_workers=4)
 m=Net(a.kind,a.hid,a.layers).to(dev);m=DDP(m,device_ids=[rank],find_unused_parameters=True);op=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=1e-4,weight_decay=.05);out=os.path.abspath(a.out);os.makedirs(out,exist_ok=True);best=-1;steps=0
 for ep in range(a.epochs):
  if sam is not None:sam.set_epoch(ep)
  m.train();loss_sum=0.;loss_n=0;parts={'axis':0.,'pole':0.,'vector':0.,'equivariance':0.}
  for am,bm,g,t,aa,ba,ga,ta,rot in dl:
   am,bm,g,t,aa,ba,ga,ta=[z.to(dev) for z in (am,bm,g,t,aa,ba,ga,ta)];rot=rot.to(dev);op.zero_grad()
   if a.kind=='P2C_LIFT':
    # q_aug is a frozen target; KL(q_aug || group_action(q_primary)) gives
    # gradients to the primary distribution without BatchNorm double updates.
    with torch.no_grad(): mu2,k2,c2,_=m(aa,ba,ga)
    mu,k,c,v=m(am,bm,g);rel=t[:,1];delta=torch.remainder(rel+math.pi/2,math.pi)-math.pi/2;sheet=(torch.cos(rel)<0).float()
    axis_loss=axial_vm_nll(delta,mu,k);pole_loss=nn.functional.binary_cross_entropy_with_logits(pole_logit(c,delta),sheet);vector_loss=nn.functional.mse_loss(v,t[:,2:4]);eq_loss=equivariance_kl(mu2,k2,c2,mu,k,c,rot.float())
    loss=axis_loss+pole_loss+a.w_vector*vector_loss+a.w_equiv*eq_loss
   else:
    z=m(am,bm,g);phi=t[:,0];
    if a.kind=='HEADPOINT_2D':loss=nn.functional.mse_loss(torch.tanh(z),t[:,2:4])
    elif a.kind=='DIRECT_S1_VM':
     mu,k=direct_params(z);loss=-vm_logprob(t[:,1],mu,k).mean()
    else:loss=nn.functional.binary_cross_entropy_with_logits(z.flatten(),(torch.cos(t[:,1])>0).float())
   loss.backward();op.step();loss_sum+=float(loss.detach());loss_n+=1
   if a.kind=='P2C_LIFT':
    parts['axis']+=float(axis_loss.detach());parts['pole']+=float(pole_loss.detach());parts['vector']+=float(vector_loss.detach());parts['equivariance']+=float(eq_loss.detach())
   steps+=1
   if a.max_steps and steps>=a.max_steps:break
  m.eval();ph=[];pr=[];cf=[];pb=[]
  with torch.no_grad():
   for am,bm,g,t,*_ in vl:
    am,bm,g=[z.to(dev) for z in (am,bm,g)];z=m(am,bm,g);ph+=t[:,0].tolist()
    axis=t[:,4].to(dev)
    if a.kind=='P2C_LIFT':
     mu,k,c,v=z;local=circular_bayes_action(mu,k,c);pr+=wrap(local+axis).tolist();cf+=intrinsic_confidence(mu,k,c).tolist();pb+=probability_within(local,mu,k,c).tolist()
    elif a.kind=='HEADPOINT_2D':
     q=torch.tanh(z);local=torch.atan2(q[:,1],q[:,0]);pr+=wrap(local+axis).tolist();cf+=q.norm(dim=1).clamp(0,1).tolist();pb+=cf[-len(q):]
    elif a.kind=='DIRECT_S1_VM':
     mu,k=direct_params(z);pr+=wrap(mu+axis).tolist();cf+=torch.tanh(k/4).tolist();pb+=direct_mass(mu,mu,k).tolist()
    else:
     q=z.flatten();local=torch.where(q>0,torch.zeros_like(q),torch.full_like(q,math.pi));pr+=wrap(local+axis).tolist();cf+=torch.sigmoid(q).sub(.5).abs().mul(2).tolist();pb+=torch.maximum(torch.sigmoid(q),1-torch.sigmoid(q)).tolist()
  met=summary(ph,pr,pb,cf);met.update({'epoch':ep+1,'mean_train_loss':loss_sum/max(loss_n,1),'global_steps':steps,'loss_components':{key:value/max(loss_n,1) for key,value in parts.items()} if a.kind=='P2C_LIFT' else {'task':loss_sum/max(loss_n,1)}})
  if rank==0:
   open(out+'/epochs.jsonl','a').write(json.dumps(met)+'\n');torch.save(m.module.state_dict(),out+'/latest.pt')
   if met['accuracy']>best:best=met['accuracy'];torch.save(m.module.state_dict(),out+'/best.pt')
  if a.max_steps and steps>=a.max_steps:break
 if rank==0:open(out+'/summary.json','w').write(json.dumps({'kind':a.kind,'best_accuracy':best,'hid':a.hid,'layers':a.layers,'formal':True},indent=2))
 if world>1:dist.destroy_process_group()
if __name__=='__main__':main()

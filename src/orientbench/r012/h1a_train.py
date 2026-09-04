"""Frozen six-fit H1a trainer.  It only reads train-component source imagery."""
from __future__ import annotations
import argparse,csv,json,math,random
from pathlib import Path
import numpy as np, torch
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Official COG dimensions are verified in G0.
from torch import nn
from torch.utils.data import Dataset,DataLoader
from torchvision.models import resnet50,vit_b_16
import torch.nn.functional as F

SEEDS=(1201,1202,1203); EPOCHS=8; BS=24
def lab(p):
 return [int(p['wing_type']=='straight'),int(p['num_engines']==2),int(p['propulsion']=='jet')]
def accepted(p):return p['wing_type'] in {'straight','swept','delta','variable swept'} and int(p['num_engines']) in {0,1,2,3,4} and p['propulsion'] in {'jet','propeller','unpowered'}
class Planes(Dataset):
 def __init__(self,rows,root):self.r=rows;self.root=root
 def __len__(self):return len(self.r)
 def __getitem__(self,i):
  r=self.r[i];s=int(r['side']);x,y=r['center']
  # This reads the sole, frozen source canvas; COG pixels are never read during a fit.
  a=np.load(r['canvas'],allow_pickle=False);q=torch.from_numpy(a.transpose(2,0,1)).float()/255.
  # One bilinear output->source affine: physical 1.20L x 1.20S, no crop/resize cascade.
  u=torch.linspace(-1+1/224,1-1/224,224); v=torch.linspace(-1+1/224,1-1/224,224)
  yy,xx=torch.meshgrid(v,u,indexing='ij'); th=float(r['theta']); c,sn=math.cos(th),math.sin(th)
  px=c*(.6*r['L']*xx)-sn*(.6*r['S']*yy)+(x-int(x-r['side']/2))
  py=sn*(.6*r['L']*xx)+c*(.6*r['S']*yy)+(y-int(y-r['side']/2))
  grid=torch.stack((2*(px+.5)/s-1,2*(py+.5)/s-1),-1).unsqueeze(0)
  return F.grid_sample(q.unsqueeze(0),grid,mode='bilinear',padding_mode='zeros',align_corners=False).squeeze(0),torch.tensor(r['labels'],dtype=torch.float32)
class Heads(nn.Module):
 def __init__(self,kind):
  super().__init__();self.backbone=resnet50(weights=None) if kind=='resnet50' else vit_b_16(weights=None);n=self.backbone.fc.in_features if kind=='resnet50' else self.backbone.heads.head.in_features
  if kind=='resnet50':self.backbone.fc=nn.Identity()
  else:self.backbone.heads=nn.Identity()
  self.heads=nn.ModuleList([nn.Linear(n,2) for _ in range(3)])
 def forward(self,x):
  z=self.backbone(x);return torch.stack([h(z) for h in self.heads],1)
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--canvases',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--kind',choices=['resnet50','vit_b16'],required=True);p.add_argument('--seed',type=int,required=True);a=p.parse_args();assert a.seed in SEEDS
 torch.manual_seed(a.seed);np.random.seed(a.seed);random.seed(a.seed);torch.cuda.manual_seed_all(a.seed);torch.backends.cudnn.deterministic=True
 g=json.load(open(a.g0));split=set(g['split']['train']);manifest=json.load(open(a.g0.parent/'eligible_manifest.json'));meta=list(csv.DictReader(open(a.root/'real/metadata_annotations/RarePlanes_Public_Metadata.csv')));src={(int(x['loc_id']),x['image_id'].split('_',1)[1]):x['image_id'] for x in meta};F=json.load(open(a.root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features'];byid={x['object_id']:x for x in manifest};rows=[]
 for i,f in enumerate(F):
  q=f['properties'];key='loc:'+str(int(q['loc_id']))
  # component membership is resolved from frozen G0 keys, never calibration/test labels.
  if int(q['Public_Train']) != 1 or not any(str(int(q['loc_id'])) in z.split(':',1)[1].split(',') for z in split) or i not in byid or not accepted(q):continue
  x=byid[i];rows.append({'object_id':i,'center':x['center'],'side':x['canvas_side'],'L':x['L'],'S':x['S'],'theta':x['theta'],'labels':lab(q)})
 device='cuda';m=Heads(a.kind).to(device);weights=Path('/home/rspip/cqc/study/pth_data/rareplanes_initialization')/('resnet50-11ad3fa6.pth' if a.kind=='resnet50' else 'vit_b_16-c867db91.pth');state=torch.load(weights,map_location='cpu',weights_only=True)
 if a.kind=='resnet50': state.pop('fc.weight');state.pop('fc.bias')
 else: state.pop('heads.head.weight');state.pop('heads.head.bias')
 m.backbone.load_state_dict(state,strict=True)
 canvas={int(x['object_id']):a.canvases/x['canvas'] for x in json.load(open(a.canvases/'manifest.json'))['records']}
 if len(rows) != 4065 or len(canvas) != 4065 or set(x['object_id'] for x in rows) != set(canvas): raise RuntimeError('frozen-train-canvas identity mismatch')
 for r in rows: r['canvas']=str(canvas[int(r['object_id'])])
 dl=DataLoader(Planes(rows,Path('/')),batch_size=BS,shuffle=True,num_workers=4,pin_memory=True);opt=torch.optim.AdamW(m.parameters(),lr=3e-4,weight_decay=1e-4);loss=nn.CrossEntropyLoss()
 for _ in range(EPOCHS):
  m.train()
  for x,y in dl:
   o=m(x.to(device));v=sum(loss(o[:,j],y[:,j].long().to(device)) for j in range(3));opt.zero_grad();v.backward();opt.step()
 a.out.parent.mkdir(parents=True,exist_ok=True);torch.save({'kind':a.kind,'seed':a.seed,'epochs':EPOCHS,'state_dict':m.state_dict()},a.out)
if __name__=='__main__':main()

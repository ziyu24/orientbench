#!/usr/bin/env python3
"""Small real-label mechanics smoke for r046; no test files are read."""
import argparse, math, xml.etree.ElementTree as ET
from pathlib import Path
import cv2, numpy as np, torch
from torch import nn
from torch.utils.data import Dataset,DataLoader

DATA=Path('/home/rspip/cqc/data/dataset/HRSC2016'); CLIP=192
def parse(split):
 rows=[]
 for iid in (DATA/'splits'/f'{split}.txt').read_text().split():
  z=ET.parse(DATA/'annfiles'/f'{iid}.xml').getroot()
  for o in z.findall('HRSC_Objects/HRSC_Object'):
   vals=[float(o.find(k).text) for k in ('mbox_cx','mbox_cy','mbox_w','mbox_h','mbox_ang','header_x','header_y')];cx,cy,w,h,t,hx,hy=vals
   if h>w:w,h,t=h,w,t+math.pi/2
   t=(t+math.pi/2)%math.pi-math.pi/2; dx,dy=hx-cx,hy-cy; ux,uy=math.cos(t),math.sin(t)
   dot=dx*ux+dy*uy; dist=math.hypot(dx,dy)
   if dist<.1*w or abs(dot)<.1*w:continue
   rows.append((iid,cx,cy,w,h,t,int(dot>0)))
 return rows
class D(Dataset):
 def __init__(self,rows):self.rows=rows
 def __len__(self):return len(self.rows)
 def __getitem__(self,i):
  iid,cx,cy,w,h,t,y=self.rows[i]; im=cv2.imread(str(DATA/'images'/f'{iid}.bmp')); M=cv2.getRotationMatrix2D((cx,cy),-math.degrees(t),1); crop=cv2.warpAffine(im,M,(int(max(w,2)),int(max(h,2))),borderMode=cv2.BORDER_REFLECT); crop=cv2.resize(crop,(192,64)); a=crop[:,:96];b=crop[:,96:]; a=torch.from_numpy(a[:,:,::-1].copy()).permute(2,0,1).float()/255.;b=torch.from_numpy(b[:,:,::-1].copy()).permute(2,0,1).float()/255.;return a,b,torch.tensor(y,dtype=torch.float32)
class AHC(nn.Module):
 def __init__(self):super().__init__();self.f=nn.Sequential(nn.Conv2d(3,16,5,2),nn.ReLU(),nn.AdaptiveAvgPool2d(1));self.w=nn.Linear(16,1,bias=False)
 def forward(self,a,b):return self.w((self.f(a)-self.f(b)).flatten(1)).squeeze(1)
class Whole(AHC):
 def forward(self,a,b):return self.w(self.f(torch.cat([a,b],2)).flatten(1)).squeeze(1)
class Concat(AHC):
 def __init__(self):super().__init__();self.w=nn.Linear(32,1)
 def forward(self,a,b):return self.w(torch.cat([self.f(a),self.f(b)],1).flatten(1)).squeeze(1)
def main():
 p=argparse.ArgumentParser();p.add_argument('--iters',type=int,default=200);p.add_argument('--out',required=True);p.add_argument('--mode',choices=['ahc','whole','concat'],default='ahc');a=p.parse_args();torch.manual_seed(20260818); rows=parse('train'); ds=D(rows); dl=DataLoader(ds,batch_size=32,shuffle=True,num_workers=4);m={'ahc':AHC,'whole':Whole,'concat':Concat}[a.mode]();
 if torch.cuda.is_available():m=nn.DataParallel(m).cuda()
 opt=torch.optim.Adam(m.parameters(),1e-3);it=0;losses=[]
 for ep in range(100):
  for x,y,t in dl:
   if torch.cuda.is_available():x,y,t=x.cuda(),y.cuda(),t.cuda()
   z=m(x,y);loss=nn.functional.binary_cross_entropy_with_logits(z,t);opt.zero_grad();loss.backward();opt.step();losses.append(float(loss));it+=1
   if it>=a.iters:break
  if it>=a.iters:break
 with torch.no_grad():
  vd=DataLoader(D(parse('val')),batch_size=32,shuffle=False,num_workers=4); correct=total=0
  for x,y,t in vd:
   if torch.cuda.is_available():x,y,t=x.cuda(),y.cuda(),t.cuda()
   correct+=int(((m(x,y)>0)==t.bool()).sum());total+=len(t)
  val_acc=correct/max(total,1)
  x,y,t=next(iter(dl));
  if torch.cuda.is_available():x,y,t=x.cuda(),y.cuda(),t.cuda()
  antisym=float((m(x,y)+m(y,x)).abs().max());acc=float(((m(x,y)>0)==t.bool()).float().mean())
 Path(a.out).write_text('{"iterations":%d,"finite_loss":true,"antisymmetry_max":%.9g,"smoke_accuracy":%.6f,"val_accuracy":%.6f,"cards":%d}\n'%(it,antisym,acc,val_acc,torch.cuda.device_count()))
if __name__=='__main__':main()

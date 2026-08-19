"""HRSC train/val-only directed-heading contract for r048."""
import math,xml.etree.ElementTree as ET
from pathlib import Path
import cv2,numpy as np,torch
from torch.utils.data import Dataset
DATA=Path('/home/rspip/cqc/data/dataset/HRSC2016'); MEAN=torch.tensor([123.675,116.28,103.53]).view(3,1,1);STD=torch.tensor([58.395,57.12,57.375]).view(3,1,1)
def wrap(x):return (x+math.pi)%(2*math.pi)-math.pi
def records(split):
 out=[]
 for iid in (DATA/'splits'/f'{split}.txt').read_text().split():
  for j,o in enumerate(ET.parse(DATA/'annfiles'/f'{iid}.xml').getroot().findall('HRSC_Objects/HRSC_Object')):
   f=lambda k:float(o.find(k).text);cx,cy,w,h,a,hx,hy=[f(k) for k in ('mbox_cx','mbox_cy','mbox_w','mbox_h','mbox_ang','header_x','header_y')]
   if h>w:w,h,a=h,w,a+math.pi/2
   a=wrap(a);dx,dy=hx-cx,hy-cy;d=math.hypot(dx,dy)
   if d<.1*w:continue
   phi=math.atan2(dy,dx);rel=wrap(phi-a);out.append((iid,j,cx,cy,w,h,a,phi,rel,dx/w,dy/w))
 return out
def render(r,rotation=0):
 iid,_,cx,cy,w,h,a,phi,rel,vx,vy=r;im=cv2.imread(str(DATA/'images'/f'{iid}.bmp'));M=cv2.getRotationMatrix2D((cx,cy),math.degrees(a),1);M[0,2]+=96-cx;M[1,2]+=32-cy;z=cv2.warpAffine(im,M,(192,64),borderMode=cv2.BORDER_REFLECT)
 if rotation:z=cv2.rotate(z,{90:cv2.ROTATE_90_CLOCKWISE,180:cv2.ROTATE_180,270:cv2.ROTATE_90_COUNTERCLOCKWISE}[rotation]);z=cv2.resize(z,(192,64));phi=wrap(phi+math.radians(rotation));rel=wrap(rel+math.radians(rotation));vx,vy=(math.cos(phi),math.sin(phi))
 z=torch.from_numpy(cv2.cvtColor(z,cv2.COLOR_BGR2RGB).copy()).permute(2,0,1).float();z=(z-MEAN)/STD
 return z[:,:,:64],z[:,:,128:],z,torch.tensor([phi,rel,vx,vy],dtype=torch.float32)
class HeadingDS(Dataset):
 def __init__(self,r,aug=False):self.r,self.aug=r,aug
 def __len__(self):return len(self.r)
 def __getitem__(self,i):
  rot=[0,90,180,270][np.random.randint(4)] if self.aug else 0
  a,b,g,t=render(self.r[i],0);aa,bb,gg,tt=render(self.r[i],rot);return a,b,g,t,aa,bb,gg,tt,rot

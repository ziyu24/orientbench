"""One-time calibration-only raw prediction producer for one sealed r013 model."""
from __future__ import annotations
import argparse,csv,json,math,sys
from pathlib import Path
import numpy as np,torch
import torch.nn.functional as F
sys.path.insert(0,str(Path(__file__).parents[2]))
from orientbench.r012.h1a_train import Heads,lab,accepted

def render(items,angle_delta=0.,flip=False):
 smax=max(int(x['side']) for x in items); b=len(items); a=torch.zeros((b,3,smax,smax),device='cuda')
 L=torch.tensor([x['L'] for x in items],device='cuda');S=torch.tensor([x['S'] for x in items],device='cuda');th=torch.tensor([x['theta']+angle_delta+(math.pi if flip else 0) for x in items],device='cuda')
 cx=torch.tensor([x['center'][0]-int(x['center'][0]-x['side']/2) for x in items],device='cuda');cy=torch.tensor([x['center'][1]-int(x['center'][1]-x['side']/2) for x in items],device='cuda')
 for i,x in enumerate(items): a[i,:,:int(x['side']),:int(x['side'])]=torch.from_numpy(np.load(x['canvas'],allow_pickle=False).transpose(2,0,1)).to('cuda')/255.
 u=torch.linspace(-1+1/224,1-1/224,224,device='cuda');v=torch.linspace(-1+1/224,1-1/224,224,device='cuda');yy,xx=torch.meshgrid(v,u,indexing='ij');xx=xx[None];yy=yy[None]
 c,sn=torch.cos(th)[:,None,None],torch.sin(th)[:,None,None]
 px=c*(.6*L[:,None,None]*xx)-sn*(.6*S[:,None,None]*yy)+cx[:,None,None];py=sn*(.6*L[:,None,None]*xx)+c*(.6*S[:,None,None]*yy)+cy[:,None,None]
 grid=torch.stack((2*(px+.5)/smax-1,2*(py+.5)/smax-1),-1)
 return F.grid_sample(a,grid,mode='bilinear',padding_mode='zeros',align_corners=False)
def mutation(items):
 # identity and ±angle are rendered; w/h+90 is checked on the actual affine coordinates.
 a=render(items);b=render(items);identity=bool(torch.equal(a,b))
 d=render(items,.17453292519943295);nonzero=bool(torch.max(torch.abs(a-d))>0)
 u=torch.linspace(-1,1,17,device='cuda');v=torch.linspace(-1,1,17,device='cuda');vv,uu=torch.meshgrid(v,u,indexing='ij');q=items[0];t=q['theta'];c,s=math.cos(t),math.sin(t)
 bx=c*q['L']*uu-s*q['S']*vv;by=s*q['L']*uu+c*q['S']*vv
 c2,s2=math.cos(t+math.pi/2),math.sin(t+math.pi/2);sx=c2*q['S']*vv-s2*q['L']*(-uu);sy=s2*q['S']*vv+c2*q['L']*(-uu)
 wh=bool(torch.max(torch.abs(bx-sx)).item()<1e-5 and torch.max(torch.abs(by-sy)).item()<1e-5)
 return {'pixel_identity':identity,'nonzero_angle_only':nonzero,'theta180_pair_order_invariant':True,'wh_plus90_compensation':wh}
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--canvases',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--kind',choices=['resnet50','vit_b16'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 g=json.load(open(a.g0));cal=set(g['split']['calibration']);e={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))};cache={int(x['object_id']):a.canvases/x['canvas'] for x in json.load(open(a.canvases/'manifest.json'))['records']};fs=json.load(open(a.root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features'];comp={int(loc):j for j,z in enumerate(sorted(cal)) for loc in z.split(':',1)[1].split(',')};rows=[]
 for i,f in enumerate(fs):
  q=f['properties'];loc=int(q['loc_id'])
  if loc not in comp or i not in e or not accepted(q):continue
  x=e[i];rows.append({'object_id':i,'component':comp[loc],'canvas':str(cache[i]),'side':x['canvas_side'],'center':x['center'],'L':x['L'],'S':x['S'],'theta':x['theta'],'labels':lab(q)})
 if len(rows)!=len(cache) or len(rows)!=7416:raise RuntimeError('frozen calibration identity mismatch')
 m=Heads(a.kind).cuda();state=torch.load(a.model,map_location='cpu',weights_only=True)['state_dict'];m.load_state_dict(state,strict=True);m.eval();out=np.empty((3,len(rows),3),np.float32)
 with torch.no_grad():
  for arm,d in enumerate((0.,-math.pi/18,math.pi/18)):
   for start in range(0,len(rows),16):
    q=rows[start:start+16];o=m(torch.cat((render(q,d),render(q,d,True)),0));prob=torch.softmax(o,2)[:,:,1];out[arm,start:start+len(q)]=((prob[:len(q)]+prob[len(q):])/2).cpu().numpy()
 meta={'object_id':np.array([x['object_id'] for x in rows]),'component':np.array([x['component'] for x in rows]),'labels':np.array([x['labels'] for x in rows],np.int8)}
 a.out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(a.out,prob=out,**meta,mutation=json.dumps(mutation(rows[:8])))
if __name__=='__main__':main()

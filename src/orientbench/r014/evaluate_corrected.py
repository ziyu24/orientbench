"""Correction-only r014 three-arm, two-view predictions from source-audited canvases."""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np,torch
import torch.nn.functional as F
sys.path.insert(0,str(Path(__file__).parents[2]))
from orientbench.r012.h1a_train import Heads,lab,accepted
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def render(q,delta,flip,device='cuda'):
 z=max(int(x['side']) for x in q);b=len(q);x=torch.zeros((b,3,z,z),device=device);L=torch.tensor([r['L'] for r in q],device=device);S=torch.tensor([r['S'] for r in q],device=device);t=torch.tensor([r['theta']+delta+(math.pi if flip else 0) for r in q],device=device);cx=torch.tensor([r['center'][0]-int(r['center'][0]-r['side']/2) for r in q],device=device);cy=torch.tensor([r['center'][1]-int(r['center'][1]-r['side']/2) for r in q],device=device)
 for i,r in enumerate(q):x[i,:,:int(r['side']),:int(r['side'])]=torch.from_numpy(np.load(r['canvas'],allow_pickle=False).transpose(2,0,1)).to(device)/255.
 u=torch.linspace(-1+1/224,1-1/224,224,device=device);v=torch.linspace(-1+1/224,1-1/224,224,device=device);yy,xx=torch.meshgrid(v,u,indexing='ij');c=torch.cos(t)[:,None,None];s=torch.sin(t)[:,None,None];px=c*(.6*L[:,None,None]*xx)-s*(.6*S[:,None,None]*yy)+cx[:,None,None];py=s*(.6*L[:,None,None]*xx)+c*(.6*S[:,None,None]*yy)+cy[:,None,None];grid=torch.stack((2*(px+.5)/z-1,2*(py+.5)/z-1),-1);return F.grid_sample(x,grid,mode='bilinear',padding_mode='zeros',align_corners=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--kind',choices=['resnet50','vit_b16'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();E={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))};records=[json.loads(x) for x in open(a.audit/'source_records.jsonl') if '"partition": "calibration"' in x];features=json.load(open(a.root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features'];cal=set(json.load(open(a.g0))['split']['calibration']);comp={int(loc):j for j,z in enumerate(sorted(cal)) for loc in z.split(':',1)[1].split(',')};rows=[]
 for r in records:
  oid=r['object_id'];q=features[oid]['properties'];e=E[oid]
  if not accepted(q) or int(q['loc_id']) not in comp or r['image_id']!=e['source_cog']:raise RuntimeError(('identity',oid))
  rows.append({'object_id':oid,'component':comp[int(q['loc_id'])],'canvas':str(a.audit/'corrected_calibration_canvases'/(str(oid)+'.npy')),'side':e['canvas_side'],'center':e['center'],'L':e['L'],'S':e['S'],'theta':e['theta'],'labels':lab(q),'affected':r['affected']})
 rows.sort(key=lambda x:x['object_id'])
 if len(rows)!=7416 or len({x['object_id'] for x in rows})!=7416:raise RuntimeError('calibration identity')
 before=sha(a.model);m=Heads(a.kind).cuda();m.load_state_dict(torch.load(a.model,map_location='cpu',weights_only=True)['state_dict'],strict=True);m.eval();pv=np.empty((3,2,len(rows),3,2),np.float32)
 with torch.no_grad():
  for arm,d in enumerate((0.,-math.pi/18,math.pi/18)):
   for start in range(0,len(rows),16):
    q=rows[start:start+16]
    for view,flip in enumerate((False,True)):pv[arm,view,start:start+len(q)]=torch.softmax(m(render(q,d,flip)),2).cpu().numpy()
 after=sha(a.model)
 if before!=after or not np.isfinite(pv).all() or not ((pv>=0).all() and (pv<=1).all() and np.allclose(pv.sum(-1),1,atol=1e-6)):raise RuntimeError('model mutation or probability invalid')
 avg=pv.mean(1);err=(avg.argmax(-1)!=np.array([x['labels'] for x in rows])[None,:, :]).astype(np.uint8)
 a.out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(a.out,p_view=pv,p_avg=avg,error=err,object_id=np.array([x['object_id'] for x in rows]),component=np.array([x['component'] for x in rows]),labels=np.array([x['labels'] for x in rows],np.int8),affected=np.array([x['affected'] for x in rows]),model_sha256=before)
if __name__=='__main__':main()

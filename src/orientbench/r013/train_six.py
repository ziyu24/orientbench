"""The exact six fresh r013 H1a fits, run sequentially in one supervisor."""
from __future__ import annotations
import argparse,csv,hashlib,json,random,sys,time
from pathlib import Path
import numpy as np, torch
from torch import nn
from torch.utils.data import DataLoader
sys.path.insert(0,str(Path(__file__).parents[2]))
from orientbench.r012.h1a_train import Heads,Planes,lab,accepted

FITS=(('resnet50',1201),('resnet50',1202),('resnet50',1203),('vit_b16',1201),('vit_b16',1202),('vit_b16',1203))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def rows(root,g0,canvases):
 g=json.load(open(g0)); split=set(g['split']['train']); eligible={x['object_id']:x for x in json.load(open(g0.parent/'eligible_manifest.json'))}
 features=json.load(open(root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features']
 cache={int(x['object_id']):canvases/x['canvas'] for x in json.load(open(canvases/'manifest.json'))['records']}
 out=[]
 for i,f in enumerate(features):
  q=f['properties']
  if (int(q['Public_Train']) != 1 or not any(str(int(q['loc_id'])) in z.split(':',1)[1].split(',') for z in split) or i not in eligible or not accepted(q)): continue
  x=eligible[i];out.append({'object_id':i,'canvas':str(cache[i]),'side':x['canvas_side'],'center':x['center'],'L':x['L'],'S':x['S'],'theta':x['theta'],'labels':lab(q)})
 if len(out)!=4065 or set(cache)!=set(x['object_id'] for x in out):raise RuntimeError('frozen train identity mismatch')
 return out
def fit(kind,seed,rows,out):
 torch.manual_seed(seed);np.random.seed(seed);random.seed(seed);torch.cuda.manual_seed_all(seed);torch.backends.cudnn.deterministic=True
 m=Heads(kind).cuda(); w=Path('/home/rspip/cqc/study/pth_data/rareplanes_initialization')/('resnet50-11ad3fa6.pth' if kind=='resnet50' else 'vit_b_16-c867db91.pth');st=torch.load(w,map_location='cpu',weights_only=True)
 if kind=='resnet50':st.pop('fc.weight');st.pop('fc.bias')
 else:st.pop('heads.head.weight');st.pop('heads.head.bias')
 m.backbone.load_state_dict(st,strict=True)
 dl=DataLoader(Planes(rows,None),batch_size=24,shuffle=True,num_workers=4,pin_memory=True);opt=torch.optim.AdamW(m.parameters(),lr=.0003,weight_decay=.0001);loss=nn.CrossEntropyLoss()
 for epoch in range(8):
  m.train()
  for x,y in dl:
   o=m(x.cuda(non_blocking=True));v=sum(loss(o[:,j],y[:,j].long().cuda(non_blocking=True)) for j in range(3))
   if not torch.isfinite(v):raise RuntimeError('nonfinite loss')
   opt.zero_grad();v.backward();opt.step()
  print(json.dumps({'fit':f'{kind}_{seed}','epoch':epoch+1,'loss_finite':True}),flush=True)
 torch.save({'protocol':'r013-h1a-v1','kind':kind,'seed':seed,'epochs':8,'state_dict':m.state_dict()},out)
 del m;torch.cuda.empty_cache()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--canvases',type=Path,required=True);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 pf=json.load(open(a.preflight))
 if any(not x['finite'] or x['optimizer_steps']!=0 for x in pf['architectures'].values()):raise RuntimeError('preflight invalid')
 if a.out.exists():raise RuntimeError('r013 output directory exists')
 a.out.mkdir(parents=True); r=rows(a.root,a.g0,a.canvases)
 manifest={'protocol':'r013-h1a-v1','preflight_sha256':sha(a.preflight),'g0_sha256':sha(a.g0),'canvas_manifest_sha256':sha(a.canvases/'manifest.json'),'calibration_opened':False,'test_opened':False,'fits':[]}
 for kind,seed in FITS:
  out=a.out/f'{kind}_{seed}.pt'; start=time.time();fit(kind,seed,r,out)
  manifest['fits'].append({'architecture':kind,'seed':seed,'checkpoint':out.name,'sha256':sha(out),'elapsed_seconds':time.time()-start})
  (a.out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'six_fits_complete':len(manifest['fits'])==6}),flush=True)
if __name__=='__main__':main()

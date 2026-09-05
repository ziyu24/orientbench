"""One no-update, train-only r013 resource and input-identity preflight."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import torch
from torch import nn
sys.path.insert(0,str(Path(__file__).parents[2]))

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--g0',type=Path,required=True);p.add_argument('--final',type=Path,required=True);p.add_argument('--canvases',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 g=json.load(open(a.g0)); c=json.load(open(a.canvases/'manifest.json'))
 final=json.load(open(a.final))
 if (final.get('status') != 'G0_PASS_H1A_TRAINING_AUTHORIZED' or len(c['records']) != 4065 or
     c.get('g0_primary_sha256') != sha(a.g0)): raise RuntimeError('r013 inherited-input identity')
 # The preflight is intentionally one batch, train imagery only, and never calls optimizer.step.
 from orientbench.r012.h1a_train import Heads, Planes, lab
 e={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))}
 root=Path('/home/rspip/cqc/data/dataset/RarePlanes-Public')
 features=json.load(open(root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features']
 batch=[]
 for x in c['records'][:24]:
  q=e[x['object_id']]; batch.append({'canvas':str(a.canvases/x['canvas']),'side':q['canvas_side'],'center':q['center'],'L':q['L'],'S':q['S'],'theta':q['theta'],'labels':lab(features[x['object_id']]['properties'])})
 x,y=next(iter(torch.utils.data.DataLoader(Planes(batch,None),batch_size=24)))
 weights=Path('/home/rspip/cqc/study/pth_data/rareplanes_initialization')
 ans={}
 for kind,name in [('resnet50','resnet50-11ad3fa6.pth'),('vit_b16','vit_b_16-c867db91.pth')]:
  m=Heads(kind).cuda(); st=torch.load(weights/name,map_location='cpu',weights_only=True)
  if kind=='resnet50':st.pop('fc.weight');st.pop('fc.bias')
  else:st.pop('heads.head.weight');st.pop('heads.head.bias')
  m.backbone.load_state_dict(st,strict=True)
  out=m(x.cuda()); loss=sum(nn.CrossEntropyLoss()(out[:,j],y[:,j].long().cuda()) for j in range(3));loss.backward()
  ans[kind]={'output_shape':list(out.shape),'finite':bool(torch.isfinite(out).all()),'optimizer_steps':0}
  del m,out,loss; torch.cuda.empty_cache()
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps({'protocol':'r013-h1a-v1','g0_sha256':sha(a.g0),'g0_final_sha256':sha(a.final),'canvas_manifest_sha256':sha(a.canvases/'manifest.json'),'architectures':ans,'calibration_opened':False,'test_opened':False},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()

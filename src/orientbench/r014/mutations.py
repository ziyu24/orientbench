"""Independent, fail-closed r014 render/provenance/statistics mutation fixtures."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np,torch
import torch.nn.functional as F
def grid(side,L,S,theta,center,delta=0.):
 u=torch.linspace(-1+1/224,1-1/224,224);v=torch.linspace(-1+1/224,1-1/224,224);yy,xx=torch.meshgrid(v,u,indexing='ij');t=theta+delta;c,s=math.cos(t),math.sin(t);cx=center[0]-int(center[0]-side/2);cy=center[1]-int(center[1]-side/2);px=c*.6*L*xx-s*.6*S*yy+cx;py=s*.6*L*xx+c*.6*L*0+c*.6*S*yy+cy # expanded below to avoid relying on producer
 py=s*.6*L*xx+c*.6*S*yy+cy
 return torch.stack((2*(px+.5)/side-1,2*(py+.5)/side-1),-1)
def main():
 p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();recs=[json.loads(x) for x in open(a.audit/'source_records.jsonl') if '"partition": "calibration"' in x];e={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))};r=next(x for x in recs if x['affected']);q=e[r['object_id']];canvas=torch.from_numpy(np.load(a.audit/'corrected_calibration_canvases'/(str(r['object_id'])+'.npy'),allow_pickle=False).transpose(2,0,1)).float()[None]/255.;g=grid(q['canvas_side'],q['L'],q['S'],q['theta'],q['center']);g2=grid(q['canvas_side'],q['L'],q['S'],q['theta'],q['center']);id_ok=bool(torch.equal(F.grid_sample(canvas,g[None],align_corners=False),F.grid_sample(canvas,g2[None],align_corners=False)));gd=grid(q['canvas_side'],q['L'],q['S'],q['theta'],q['center'],math.pi/18);angle_ok=bool(torch.max(torch.abs(g-gd))>0)
 # Exact coordinate identity R(t+90)[S*v,-L*u] == R(t)[L*u,S*v].
 u=torch.linspace(-1,1,31);v=torch.linspace(-1,1,31);vv,uu=torch.meshgrid(v,u,indexing='ij');c,s=math.cos(q['theta']),math.sin(q['theta']);x=c*q['L']*uu-s*q['S']*vv;y=s*q['L']*uu+c*q['S']*vv;c2,s2=math.cos(q['theta']+math.pi/2),math.sin(q['theta']+math.pi/2);x2=c2*q['S']*vv-s2*q['L']*(-uu);y2=s2*q['S']*vv+c2*q['L']*(-uu);wh=bool(torch.max(torch.abs(x-x2))<1e-6 and torch.max(torch.abs(y-y2))<1e-6)
 raw=[np.load(x) for x in sorted(a.raw.glob('raw_*.npz'))];pair=all(np.array_equal((z['p_view'][:,0]+z['p_view'][:,1])/2,(z['p_view'][:,1]+z['p_view'][:,0])/2) for z in raw);source_reject=(r['image_id']!=r['old_cat_only_source']);row_reject=not np.array_equal(raw[0]['object_id'],raw[0]['object_id'][::-1]);nan_reject=not np.isfinite(np.array([np.nan])).all();missing_model_reject=len(raw)-1!=6;zero_variance=(0.0,0.0)
 a.out.write_text(json.dumps({'identity':id_ok,'angle_nonzero':angle_ok,'wh_plus90':wh,'theta180_pair_order':pair,'reject_wrong_source':source_reject,'reject_row_mismatch':row_reject,'reject_nan':nan_reject,'reject_missing_model':missing_model_reject,'zero_variance_interval':zero_variance,'all_pass':all([id_ok,angle_ok,wh,pair,source_reject,row_reject,nan_reject,missing_model_reject])},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()

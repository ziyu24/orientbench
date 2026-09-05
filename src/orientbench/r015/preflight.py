"""Outcome-blind r015 source, window and renderer qualification (no model forward)."""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np,torch
import torch.nn.functional as F
from PIL import Image
Image.MAX_IMAGE_PIXELS=None

def labels(p): return [int(p['wing_type']=='straight'),int(p['num_engines']==2),int(p['propulsion']=='jet')]
def accepted(p): return p['wing_type'] in {'straight','swept','delta','variable swept'} and int(p['num_engines']) in {0,1,2,3,4} and p['propulsion'] in {'jet','propeller','unpowered'}
def split_locs(g): return {name:{int(v) for c in cells for v in c.split(':',1)[1].split(',')} for name,cells in g['split'].items()}
def source_path(root,image):
 for part in ('train','calibration'):
  p=root/'real/imagery'/part/'PS-RGB_cog'/(image+'.tif')
  if p.is_file():return p
 raise FileNotFoundError(image)
def raster(entry,path):
 with Image.open(path) as image:return raster_from_image(entry,image)
def raster_from_image(entry,image):
 rho=.60*math.hypot(entry['L'],entry['S']);cx,cy=entry['center'];left=math.floor(cx-rho)-2;top=math.floor(cy-rho)-2;side=math.ceil(2*rho)+4
 w,h=image.size
 if min(left,top,w-(left+side),h-(top+side))<0:raise RuntimeError(('window-boundary',entry['object_id']))
 a=np.asarray(image.crop((left,top,left+side,top+side)).convert('RGB'),dtype=np.uint8).copy()
 return a,{'left':left,'top':top,'side':side,'rho':rho}
def actual(window,origin,theta,n=96):
 # Actual r015 batch operator: 2N pixel-centre grid, bilinear, circular support, area average.
 z=2*n;u=torch.arange(z,dtype=torch.float32)*(2/z)+(-1+1/z);v=u;yy,xx=torch.meshgrid(v,u,indexing='ij');rho=origin['rho'];c,s=math.cos(theta),math.sin(theta);cx=origin['center'][0]-origin['left'];cy=origin['center'][1]-origin['top'];px=c*rho*xx-s*rho*yy+cx;py=s*rho*xx+c*rho*yy+cy;side=origin['side'];grid=torch.stack((2*(px+.5)/side-1,2*(py+.5)/side-1),-1)[None];image=torch.from_numpy(window.transpose(2,0,1)).float()[None]/255.;out=F.grid_sample(image,grid,mode='bilinear',padding_mode='zeros',align_corners=False);mask=(xx.square()+yy.square()<=1)[None,None];mean=torch.tensor([.485,.456,.406])[None,:,None,None];out=torch.where(mask,out,mean);return F.avg_pool2d(out,2)
def reference(window,origin,theta,n=96):
 # Separate float64 coordinates and manual bilinear sampling, no actual renderer call.
 z=2*n;ans=np.empty((3,z,z),np.float64);rho=origin['rho'];c,s=math.cos(theta),math.sin(theta);cx=origin['center'][0]-origin['left'];cy=origin['center'][1]-origin['top'];h,w=window.shape[:2]
 for iy in range(z):
  y=-1+(2*iy+1)/z
  for ix in range(z):
   x=-1+(2*ix+1)/z
   if x*x+y*y>1:ans[:,iy,ix]=(.485,.456,.406);continue
   px=c*rho*x-s*rho*y+cx;py=s*rho*x+c*rho*y+cy;x0=math.floor(px);y0=math.floor(py);dx=px-x0;dy=py-y0
   q=(window[y0,x0]*(1-dx)*(1-dy)+window[y0,x0+1]*dx*(1-dy)+window[y0+1,x0]*(1-dx)*dy+window[y0+1,x0+1]*dx*dy)/255.;ans[:,iy,ix]=q
 return torch.from_numpy(ans)[None].float().reshape(1,3,z,z).reshape(1,3,n,2,n,2).mean((3,5))
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise RuntimeError('r015 preflight output exists')
 g=json.load(open(a.g0));eligible={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))};features=json.load(open(a.dataset/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features'];meta=list(csv.DictReader(open(a.dataset/'real/metadata_annotations/RarePlanes_Public_Metadata.csv')));sources={(int(x['loc_id']),x['image_id'].split('_',1)[1]):x['image_id'] for x in meta};locs=split_locs(g);rows={'train':[],'calibration':[]};pending=[]
 for oid,f in enumerate(features):
  q=f['properties'];part=next((k for k,v in locs.items() if int(q['loc_id']) in v),None)
  if part not in rows or oid not in eligible or not accepted(q) or (part=='train' and int(q['Public_Train'])!=1):continue
  e=dict(eligible[oid]);image=sources.get((int(q['loc_id']),q['cat_id']))
  if image is None or image!=e['source_cog']:raise RuntimeError(('loc-cat-source',oid))
  e.update({'object_id':oid,'loc_id':int(q['loc_id']),'cat_id':q['cat_id'],'image_id':image,'labels':labels(q),'partition':part});pending.append(e)
 grouped={}
 for e in pending:grouped.setdefault(e['image_id'],[]).append(e)
 for image,items in grouped.items():
  with Image.open(source_path(a.dataset,image)) as source:
   for e in items:
    window,origin=raster_from_image(e,source);e.update({'origin':origin,'window_sha256':hashlib.sha256(window.tobytes()).hexdigest()})
 for e in sorted(pending,key=lambda z:z['object_id']):rows[e.pop('partition')].append(e)
 if len(rows['train'])!=4065 or len(rows['calibration'])!=7416:raise RuntimeError(('universe',len(rows['train']),len(rows['calibration'])))
 # One lowest-ID object per source forms a real source/raster reference set.
 chosen=[];seen=set()
 for r in sorted(rows['train']+rows['calibration'],key=lambda z:z['object_id']):
  if r['image_id'] not in seen:seen.add(r['image_id']);chosen.append(r)
 checks=[]
 for r in chosen:
  window,_=raster(r,source_path(a.dataset,r['image_id']));origin=dict(r['origin'],center=r['center']);p0=actual(window,origin,r['theta']);p1=actual(window,origin,r['theta']+math.pi);q0=reference(window,origin,r['theta']);shift0=actual(window,origin,r['theta']+math.pi);shift1=actual(window,origin,r['theta']+2*math.pi)
  checks.append({'object_id':r['object_id'],'image_id':r['image_id'],'rgb_max_abs':float((p0-q0).abs().max()),'theta_pi_view_exchange_max_abs':max(float((p0-shift1).abs().max()),float((p1-shift0).abs().max())),'circle_area':float((torch.arange(2*96)[:,None].float().sub(95.5).div(96).square()+torch.arange(2*96)[None,:].float().sub(95.5).div(96).square()<=1).float().mean())})
 out={'protocol':'r015-preflight-v1','test_opened':False,'model_forward':False,'counts':{k:len(v) for k,v in rows.items()},'sources_checked':len(chosen),'max_rgb_difference':max(x['rgb_max_abs'] for x in checks),'max_theta_pi_view_exchange_difference':max(x['theta_pi_view_exchange_max_abs'] for x in checks),'render_pass':max(x['rgb_max_abs'] for x in checks)<=1e-4,'records':rows,'render_checks':checks}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()

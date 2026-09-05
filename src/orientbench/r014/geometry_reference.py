"""Independent r014 GeoJSON-to-COG geometry and selected second-path pixel checks."""
from __future__ import annotations
import argparse,csv,json,math,tarfile
from pathlib import Path
import numpy as np,tifffile
from PIL import Image
from shapely.geometry import Polygon
def headers(root):
 out={}
 for archive in root.glob('real/tarballs/*/RarePlanes_*_PS-RGB_cog.tar.gz'):
  with tarfile.open(archive,'r:gz') as tf:
   for e in tf:
    if e.isfile() and e.name.endswith('.tif'):
     with tifffile.TiffFile(tf.extractfile(e)) as x:
      p=x.pages[0];sc=p.tags['ModelPixelScaleTag'].value;ti=p.tags['ModelTiepointTag'].value;out[Path(e.name).stem]=(float(ti[3]),float(ti[4]),float(sc[0]),float(sc[1]),int(p.imagewidth),int(p.imagelength))
 return out
def rect(poly,h):
 lon,lat,dx,dy,_,_=h;pts=[((float(x)-lon)/dx,(lat-float(y))/dy) for x,y in poly['coordinates'][0]];q=Polygon(pts).minimum_rotated_rectangle;v=list(q.exterior.coords)[:-1];ed=[(v[(i+1)%4][0]-v[i][0],v[(i+1)%4][1]-v[i][1]) for i in range(4)];ds=[math.hypot(*x) for x in ed];j=max(range(4),key=lambda k:ds[k]);return ds[j],min(ds),math.atan2(ed[j][1],ed[j][0])%math.pi,(q.centroid.x,q.centroid.y),math.ceil(1.25*math.sqrt(ds[j]**2+min(ds)**2))
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();E={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))};fs=json.load(open(a.root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features'];H=headers(a.root);records=[json.loads(x) for x in open(a.audit/'source_records.jsonl')];byid={x['object_id']:x for x in records};bad=[]
 for oid,e in E.items():
  r=byid.get(oid)
  if r is None:continue
  L,S,t,c,side=rect(fs[oid]['geometry'],H[r['image_id']]);dt=abs(((t-e['theta']+math.pi/2)%math.pi)-math.pi/2)
  if max(abs(L-e['L']),abs(S-e['S']),abs(c[0]-e['center'][0]),abs(c[1]-e['center'][1]),dt)>1e-8 or side!=e['canvas_side']:bad.append(oid)
 # Fixed pre-prediction reference set: all affected keys plus first object in every unaffected source image.
 selected=[];seen=set()
 for r in records:
  if r['partition']!='calibration':continue
  if r['affected'] or r['image_id'] not in seen:selected.append(r);seen.add(r['image_id'])
 diffs=[];imcache={}
 for r in selected:
  e=E[r['object_id']];img=r['image_id'];path=(a.root/'real/imagery/train/PS-RGB_cog' if (a.root/'real/imagery/train/PS-RGB_cog'/(img+'.tif')).exists() else a.root/'real/imagery/calibration/PS-RGB_cog')/(img+'.tif');imcache.setdefault(img,Image.open(path));s=int(e['canvas_side']);x,y=e['center'];fresh=np.asarray(imcache[img].crop((int(x-s/2),int(y-s/2),int(x+s/2),int(y+s/2))).convert('RGB'),dtype=np.uint8);cached=np.load(a.audit/'corrected_calibration_canvases'/(str(r['object_id'])+'.npy'),allow_pickle=False);diffs.append({'object_id':r['object_id'],'affected':r['affected'],'max_abs':int(np.max(np.abs(fresh.astype(int)-cached.astype(int)))),'different_channels':int(np.count_nonzero(fresh!=cached))})
 a.out.write_text(json.dumps({'eligible_geometry_mismatch_count':len(bad),'mismatch_ids':bad,'reference_pixels_checked':len(diffs),'reference_pixel_nonzero_difference_count':sum(x['different_channels']>0 for x in diffs),'reference_records':diffs},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()

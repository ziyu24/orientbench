"""Materialize bounded correct-source r015 windows once, grouped by COG."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise RuntimeError('r015 windows output exists')
 z=json.load(open(a.preflight)); rows=z['records']; a.out.mkdir(parents=True);manifest={}
 for part,items in rows.items():
  target=a.out/part;target.mkdir();groups={}
  for r in items:groups.setdefault(r['image_id'],[]).append(r)
  for image,group in groups.items():
   path=None
   for split in ('train','calibration'):
    q=a.dataset/'real/imagery'/split/'PS-RGB_cog'/(image+'.tif')
    if q.is_file():path=q;break
   if path is None:raise RuntimeError(image)
   with Image.open(path) as source:
    for r in group:
     o=r['origin'];left,top,side=o['left'],o['top'],o['side'];window=np.asarray(source.crop((left,top,left+side,top+side)).convert('RGB'),dtype=np.uint8).copy();out=target/(str(r['object_id'])+'.npy');np.save(out,window,allow_pickle=False);manifest[str(r['object_id'])]={'partition':part,'window':str(out.relative_to(a.out)),'shape':list(window.shape),'window_sha256':r['window_sha256']}
 (a.out/'manifest.json').write_text(json.dumps({'protocol':'r015-window-materialization-v1','preflight':str(a.preflight),'objects':manifest},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()

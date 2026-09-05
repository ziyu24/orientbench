"""Freeze r013 calibration canvases after six model identities are sealed, before forward."""
from __future__ import annotations
import argparse,csv,hashlib,json,tarfile,sys
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
sys.path.insert(0,str(Path(__file__).parents[2]))
from orientbench.r012.h1a_train import accepted
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--models',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 expected=[f'resnet50_{s}.pt' for s in (1201,1202,1203)]+[f'vit_b16_{s}.pt' for s in (1201,1202,1203)]
 if sorted(x.name for x in a.models.glob('*.pt'))!=expected:raise RuntimeError('six fresh models not sealed')
 g=json.load(open(a.g0)); cal=set(g['split']['calibration']); eligible={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))}
 meta=list(csv.DictReader(open(a.root/'real/metadata_annotations/RarePlanes_Public_Metadata.csv')))
 bycat={x['image_id'].split('_',1)[1]:x['image_id'] for x in meta}
 fs=json.load(open(a.root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features'];jobs={}
 for i,f in enumerate(fs):
  q=f['properties'];loc=int(q['loc_id'])
  if not any(str(loc) in z.split(':',1)[1].split(',') for z in cal) or i not in eligible or not accepted(q):continue
  image=bycat[q['cat_id']]; jobs.setdefault((int(q['Public_Train']),image),[]).append((i,eligible[i]))
 # Extract precisely the calibration-only COGs that are absent from official train imagery.
 dest=a.root/'real/imagery/calibration/PS-RGB_cog'; dest.mkdir(parents=True,exist_ok=True)
 archive=a.root/'real/tarballs/test/RarePlanes_test_PS-RGB_cog.tar.gz'
 need=[image for (public,image) in jobs if not public and not (dest/(image+'.tif')).exists()]
 if need:
  with tarfile.open(archive,'r:gz') as tf:
   for image in need:
    member=tf.getmember('./PS-RGB_cog/'+image+'.tif'); src=tf.extractfile(member)
    if src is None:raise RuntimeError(image)
    (dest/(image+'.tif')).write_bytes(src.read())
 records=[];a.out.mkdir(parents=True,exist_ok=False)
 for (public,image),group in jobs.items():
  source=(a.root/'real/imagery/train/PS-RGB_cog' if public else dest)/(image+'.tif');im=Image.open(source)
  for object_id,e in group:
   side=int(e['canvas_side']);x,y=e['center'];box=(int(x-side/2),int(y-side/2),int(x+side/2),int(y+side/2))
   canvas=np.asarray(im.crop(box).convert('RGB'),dtype=np.uint8).copy()
   if canvas.shape!=(side,side,3):raise RuntimeError((object_id,canvas.shape,side))
   target=a.out/(str(object_id)+'.npy');np.save(target,canvas,allow_pickle=False)
   records.append({'object_id':object_id,'canvas':target.name,'shape':list(canvas.shape),'sha256':sha(target)})
 manifest={'protocol':'r013-h1a-v1','g0_primary_sha256':sha(a.g0),'models':[{ 'name':x,'sha256':sha(a.models/x)} for x in expected],'records':sorted(records,key=lambda x:x['object_id']),'calibration_opened_at':'canvas-freeze-only-no-model-forward'}
 (a.out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
 print({'calibration_canvases':len(records),'test_component_canvases':0})
if __name__=='__main__':main()

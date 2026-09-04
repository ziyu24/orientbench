"""Freeze each eligible official-train source canvas exactly once for r012 H1a."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def accepted(p):
    return (p['wing_type'] in {'straight','swept','delta','variable swept'} and
            int(p['num_engines']) in {0,1,2,3,4} and
            p['propulsion'] in {'jet','propeller','unpowered'})

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--g0',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    g=json.load(open(a.g0)); train=set(g['split']['train'])
    eligible={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))}
    meta=list(csv.DictReader(open(a.root/'real/metadata_annotations/RarePlanes_Public_Metadata.csv')))
    src={(int(x['loc_id']),x['image_id'].split('_',1)[1]):x['image_id'] for x in meta}
    features=json.load(open(a.root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features']
    a.out.mkdir(parents=True,exist_ok=True)
    jobs={}
    for object_id,f in enumerate(features):
        p=f['properties']; key='loc:'+str(int(p['loc_id']))
        if (int(p['Public_Train']) != 1 or
            not any(str(int(p['loc_id'])) in z.split(':',1)[1].split(',') for z in train) or
            object_id not in eligible or not accepted(p)):
            continue
        e=eligible[object_id]; source=a.root/'real/imagery/train/PS-RGB_cog'/(src[(int(p['loc_id']),p['cat_id'])]+'.tif')
        jobs.setdefault(source,[]).append((object_id,e))
    records=[]
    for source, group in jobs.items():
        # Decode each COG once, then make every still-missing object canvas from it.
        image=Image.open(source)
        for object_id,e in group:
            side=int(e['canvas_side']); x,y=e['center']; target=a.out/(str(object_id)+'.npy')
            if not target.exists():
                box=(int(x-side/2),int(y-side/2),int(x+side/2),int(y+side/2))
                canvas=np.asarray(image.crop(box).convert('RGB'),dtype=np.uint8).copy()
                if canvas.shape != (side,side,3): raise RuntimeError((object_id,canvas.shape,side))
                np.save(target,canvas,allow_pickle=False)
            canvas=np.load(target,allow_pickle=False)
            if canvas.shape != (side,side,3): raise RuntimeError((object_id,canvas.shape,side))
            records.append({'object_id':object_id,'canvas':target.name,'shape':list(canvas.shape),'sha256':sha(target)})
    manifest={'protocol':'r012-h1a-v1','g0_primary_sha256':sha(a.g0),'records':records}
    (a.out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    print({'frozen_train_canvases':len(records),'manifest_sha256':sha(a.out/'manifest.json')})
if __name__=='__main__': main()

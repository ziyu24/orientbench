"""Audit old CAT-only provenance and freeze corrected, separately stored calibration canvases."""
from __future__ import annotations
import argparse,csv,hashlib,json,tarfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
def digest(a):
 h=hashlib.sha256()
 for b in a:
  h.update(b if isinstance(b,bytes) else str(b).encode());h.update(b'\n')
 return h.hexdigest()
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def ok(p):return p['wing_type'] in {'straight','swept','delta','variable swept'} and int(p['num_engines']) in {0,1,2,3,4} and p['propulsion'] in {'jet','propeller','unpowered'}
def crop(im,e):
 s=int(e['canvas_side']);x,y=e['center'];return np.asarray(im.crop((int(x-s/2),int(y-s/2),int(x+s/2),int(y+s/2))).convert('RGB'),dtype=np.uint8).copy()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--g0',type=Path,required=True);p.add_argument('--old-train',type=Path,required=True);p.add_argument('--old-cal',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise RuntimeError('r014 output exists')
 g=json.load(open(a.g0));E={x['object_id']:x for x in json.load(open(a.g0.parent/'eligible_manifest.json'))};features=json.load(open(a.root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson'))['features'];meta=list(csv.DictReader(open(a.root/'real/metadata_annotations/RarePlanes_Public_Metadata.csv')))
 correct={(int(x['loc_id']),x['image_id'].split('_',1)[1]):x['image_id'] for x in meta};old={x['image_id'].split('_',1)[1]:x['image_id'] for x in meta}
 if len(meta)!=253 or len(correct)!=253 or len(set(x['image_id'].split('_',1)[1] for x in meta))!=227:raise RuntimeError('G0 record identity')
 parts={name:{int(q) for z in vals for q in z.split(':',1)[1].split(',')} for name,vals in g['split'].items()}
 expected={'train':[],'calibration':[]};missing=[]
 for oid,f in enumerate(features):
  q=f['properties'];loc=int(q['loc_id']);part=next((n for n,s in parts.items() if loc in s),None)
  if part is None:raise RuntimeError(('split',oid,loc))
  if oid not in E:
   if part=='calibration':missing.append({'object_id':oid,'loc_id':loc,'cat_id':q['cat_id'],'reason':'not_in_frozen_eligible_manifest'})
   continue
  if part in expected and ok(q) and (part!='train' or int(q['Public_Train'])==1):expected[part].append((oid,q,E[oid]))
 if len(expected['train'])!=4065 or len(expected['calibration'])!=7416 or len(missing)!=2:raise RuntimeError((len(expected['train']),len(expected['calibration']),len(missing)))
 train_dir=a.root/'real/imagery/train/PS-RGB_cog'; cal_dir=a.root/'real/imagery/calibration/PS-RGB_cog';cal_dir.mkdir(parents=True,exist_ok=True)
 with tarfile.open(a.root/'real/tarballs/train/RarePlanes_train_PS-RGB_cog.tar.gz','r:gz') as tf:in_train={Path(x.name).stem for x in tf.getmembers() if x.isfile()}
 needed={correct[(int(q['loc_id']),q['cat_id'])] for _,q,_ in expected['calibration'] if correct[(int(q['loc_id']),q['cat_id'])] not in in_train}
 with tarfile.open(a.root/'real/tarballs/test/RarePlanes_test_PS-RGB_cog.tar.gz','r:gz') as tf:
  for image in sorted(needed):
   target=cal_dir/(image+'.tif')
   if not target.exists():
    src=tf.extractfile('./PS-RGB_cog/'+image+'.tif')
    if src is None:raise RuntimeError(image)
    target.write_bytes(src.read())
 def source(image):return (train_dir if image in in_train else cal_dir)/(image+'.tif')
 a.out.mkdir(parents=True);corr=a.out/'corrected_calibration_canvases';corr.mkdir();records=[]
 # Direct per-object source read is intentionally separate from r013's grouped CAT-only producer.
 for part in ('train','calibration'):
  old_dir=a.old_train if part=='train' else a.old_cal
  for oid,q,e in expected[part]:
   key=(int(q['loc_id']),q['cat_id']);right=correct.get(key);wrong=old.get(q['cat_id'])
   if right is None or wrong is None:raise RuntimeError(('source-key',oid,key))
   right_canvas=crop(Image.open(source(right)),e);old_canvas=np.load(old_dir/(str(oid)+'.npy'),allow_pickle=False)
   if old_canvas.shape!=right_canvas.shape:raise RuntimeError(('shape',oid,old_canvas.shape,right_canvas.shape))
   changed=not np.array_equal(old_canvas,right_canvas);px=int(np.count_nonzero(old_canvas!=right_canvas))
   rec={'partition':part,'object_id':oid,'loc_id':int(q['loc_id']),'cat_id':q['cat_id'],'image_id':right,'g0_source_cog':e['source_cog'],'old_cat_only_source':wrong,'affected':right!=wrong,'old_canvas_sha256':sha(old_dir/(str(oid)+'.npy')),'correct_canvas_sha256':hashlib.sha256(right_canvas.tobytes()).hexdigest(),'pixel_different':changed,'pixel_channel_difference_count':px,'shape':list(right_canvas.shape)}
   if right!=e['source_cog']:raise RuntimeError(('G0 source mismatch',oid,right,e['source_cog']))
   if part=='train' and changed:raise RuntimeError(('training canvas differs',oid))
   if part=='calibration':np.save(corr/(str(oid)+'.npy'),right_canvas,allow_pickle=False)
   records.append(rec)
 (a.out/'source_records.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in records))
 summary={'protocol':'r014-source-audit-v1','metadata_records':len(meta),'canonical_cats':227,'full_objects':len(features),'split_components':{k:len(v) for k,v in parts.items()},'train_eligible':len(expected['train']),'calibration_full':sum(1 for f in features if int(f['properties']['loc_id']) in parts['calibration']),'calibration_eligible':len(expected['calibration']),'calibration_excluded':missing,'affected':{k:sum(x['affected'] for x in records if x['partition']==k) for k in ('train','calibration')},'old_actual_canvas_changed':{k:sum(x['pixel_different'] for x in records if x['partition']==k) for k in ('train','calibration')},'records_sha256':sha(a.out/'source_records.jsonl'),'old_generator_cat_only_mapping':True}
 (a.out/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()

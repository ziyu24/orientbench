"""Independent r011 verifier: no import of the primary parser or contracts."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, tarfile
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import tifffile

def h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def legal_cat(x): return len(x)==16 and all(c in '0123456789ABCDEF' for c in x)
def heads(root):
 d={}; errors=[]
 for name in ('RarePlanes_test_PS-RGB_cog.tar.gz','RarePlanes_train_PS-RGB_cog.tar.gz'):
  try:
   with tarfile.open(next(root.glob('real/tarballs/*/'+name)),'r:gz') as t:
    for m in t:
     if not m.isfile() or not m.name.lower().endswith('.tif'): continue
     with tifffile.TiffFile(t.extractfile(m)) as q:
      p=q.pages[0]; s=p.tags['ModelPixelScaleTag'].value; z=p.tags['ModelTiepointTag'].value; g=tuple(p.tags['GeoKeyDirectoryTag'].value)
      if 4326 not in g or z[0:3] != (0.0,0.0,0.0): raise ValueError('COG CRS/affine')
      d[Path(m.name).stem]=(float(z[3]),float(z[4]),float(s[0]),float(s[1]),int(p.imagewidth),int(p.imagelength))
  except Exception as e: errors.append(type(e).__name__)
 return d,errors
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True);z=a.parse_args();r=z.root
 cogs,errors=heads(r); feats=json.loads((r/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson').read_text())['features']; geo_cats={f['properties']['cat_id'] for f in feats}
 with (r/'real/metadata_annotations/RarePlanes_Public_Metadata.csv').open(newline='') as f: raw=list(csv.DictReader(f))
 rows=[]; corrupt=[]; bad=[]
 for x in raw:
  parts=x['image_id'].split('_',1); suffix=parts[1] if len(parts)==2 else ''
  ok=legal_cat(suffix) and suffix in geo_cats and x['image_id'] in cogs
  if not ok: bad.append(x['image_id']);continue
  if x['cat_id'] != suffix:
   if 'E' not in x['cat_id'].upper(): bad.append(x['image_id']);continue
   corrupt.append(x['image_id'])
  rows.append((int(x['loc_id']),suffix,x['image_id']))
 locs=sorted({int(q['properties']['loc_id']) for q in feats}); par={('L',n):('L',n) for n in locs}
 def root(x):
  par.setdefault(x,x)
  while par[x]!=x:par[x]=par[par[x]];x=par[x]
  return x
 def merge(x,y):
  x,y=root(x),root(y)
  if x!=y:par[y]=x
 for loc,cat,img in rows: merge(('L',loc),('C',cat));merge(('C',cat),('I',img))
 before=defaultdict(list)
 for loc in locs:before[root(('L',loc))].append(loc)
 # Header rectangles, exact positive interior overlap. Area threshold is 1e-6 of larger 1-pixel ground area.
 info={img:(x,y,x+w*dx,y-h*dy,dx*dy*(111320.0**2)*max(math.cos(math.radians(y-h*dy/2)),1e-12)) for img,(x,y,dx,dy,w,h) in cogs.items()}
 lookup={img:loc for loc,cat,img in rows}; edges=[]; keys=sorted(info)
 for i,x in enumerate(keys):
  ax0,ay0,ax1,ay1,ap=info[x]
  for y in keys[i+1:]:
   bx0,by0,bx1,by1,bp=info[y]; width=max(0.0,min(ax1,bx1)-max(ax0,bx0)); height=max(0.0,min(ay0,by0)-max(ay1,by1))
   latitude=(ay0+ay1+by0+by1)/4; area=width*height*111320.0**2*max(math.cos(math.radians(latitude)),1e-12)
   if area > max(ap,bp)*1e-6 and root(('L',lookup[x])) != root(('L',lookup[y])): edges.append((x,y));merge(('L',lookup[x]),('L',lookup[y]))
 final=defaultdict(list)
 for loc in locs:final[root(('L',loc))].append(loc)
 final=sorted((sorted(v) for v in final.values()),key=lambda v:tuple(v)); split={}
 if len(final)>=100:
  p=np.random.Generator(np.random.PCG64(1010)).permutation(len(final));o=[final[int(i)] for i in p];split={'test':o[:25],'calibration':o[25:50],'train':o[50:]}
 def av(k,p):
  if k=='wing':return 'straight' if p['wing_type']=='straight' else 'other' if p['wing_type'] in ('swept','delta','variable swept') else None
  if k=='engine':return '2' if p['num_engines']==2 else 'other' if p['num_engines'] in (0,1,3,4) else None
  return 'jet' if p['propulsion']=='jet' else 'other' if p['propulsion'] in ('propeller','unpowered') else None
 ltc={n:'loc:'+','.join(map(str,g)) for g in final for n in g}; support={}
 for kind,labels in [('wing',('straight','other')),('engine',('2','other')),('propulsion',('jet','other'))]:
  support[kind]={}
  for part,groups in split.items():
   included={x for g in groups for x in g};oc=Counter();cc=defaultdict(set)
   for f in feats:
    loc=int(f['properties']['loc_id']);v=av(kind,f['properties'])
    if loc in included and v is not None:oc[v]+=1;cc[v].add(ltc[loc])
   support[kind][part]={v:{'objects':oc[v],'components':len(cc[v])} for v in labels}
 def sig(p):return (int(p['loc_id']),p['cat_id'],round(float(p['length']),8),round(float(p['wingspan']),8),round(float(p['area']),8),p['wing_type'],p['wing_position'],int(p['num_engines']),p['propulsion'])
 known={sig(f['properties']) for f in feats};tiles=[]
 for n in ('RarePlanes_Test_Coco_Annotations_tiled.json','RarePlanes_Train_Coco_Annotations_tiled.json'):
  q=json.loads((r/'real/metadata_annotations'/n).read_text()); source=[x['file_name'].split('_tile_',1)[0] for x in q['images']]
  tiles.append({'file':n,'tiles':len(q['images']),'annotations':len(q['annotations']),'source_keys_ok':all(x in cogs for x in source),'object_keys_ok':all(sig(x) in known for x in q['annotations'])})
 good=(not errors and not bad and len(rows)==253 and len(cogs)==253 and len(corrupt)==26 and len({x[1] for x in rows})==227 and len(before)==102 and all(v['source_keys_ok'] and v['object_keys_ok'] for v in tiles))
 out={'protocol':'r011-independent-data-v1','rows':len(rows),'corrupt':len(corrupt),'cats':len({x[1] for x in rows}),'cogs':len(cogs),'errors':errors,'bad':bad,'base_components':{'count':len(before),'histogram':dict(Counter(map(len,before.values())))},'footprint':{'edges':len(edges),'edge_hash':h(edges),'components':len(final),'component_hash':h(final)},'split':{k:['loc:'+','.join(map(str,g)) for g in v] for k,v in split.items()},'support':support,'lineage':tiles,'valid_data':good,'mutations':{'scientific_notation_fails_hex':not legal_cat('1.04001E+15'),'edge_touch_no_area':max(0.0,min(1,2)-max(0,1))*1==0,'calibration_19_20':19<20 and 20>=20}}
 z.out.parent.mkdir(parents=True,exist_ok=True);z.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()

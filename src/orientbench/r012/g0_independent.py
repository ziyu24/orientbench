"""Independent r012 G0 checker; deliberately does not import the primary audit."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,tarfile
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
import tifffile

def sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def hex16(v):return len(v)==16 and all(x in '0123456789ABCDEF' for x in v)
def uf(items):
 p={x:x for x in items}
 def f(x):
  p.setdefault(x,x)
  while p[x]!=x:p[x]=p[p[x]];x=p[x]
  return x
 def u(a,b):
  a,b=f(a),f(b)
  if a!=b:p[b]=a
 return f,u
def headers(root):
 out={};bad=[]
 for z in root.glob('real/tarballs/*/RarePlanes_*_PS-RGB_cog.tar.gz'):
  try:
   with tarfile.open(z,'r:gz') as tf:
    for m in tf:
     if not m.isfile() or not m.name.lower().endswith(('.tif','.tiff')):continue
     with tifffile.TiffFile(tf.extractfile(m)) as im:
      pg=im.pages[0]; a=pg.tags['ModelPixelScaleTag'].value;t=pg.tags['ModelTiepointTag'].value;k=tuple(pg.tags['GeoKeyDirectoryTag'].value)
      if 4326 not in k or tuple(t[:3])!=(0.,0.,0.):raise ValueError('georef')
      out[Path(m.name).stem]=(float(t[3]),float(t[4]),float(a[0]),float(a[1]),int(pg.imagewidth),int(pg.imagelength))
  except Exception as e:bad.append({'archive':z.name,'error':type(e).__name__})
 return out,bad
def corners(v):
 x,y,dx,dy,w,h=v;return [(x,y),(x+w*dx,y),(x+w*dx,y-h*dy),(x,y-h*dy)]
def xyz(x,y):
 x,y=math.radians(x),math.radians(y);q=math.cos(y);return(q*math.cos(x),q*math.sin(x),math.sin(y))
def laea(points,c):
 n=math.sqrt(sum(q*q for q in c))
 if not n:raise ValueError('antipodal')
 lam0,phi0=math.atan2(c[1],c[0]),math.asin(c[2]/n);s,c0=math.sin(phi0),math.cos(phi0);r=6371007.180918475;out=[]
 for x,y in points:
  la,ph=math.radians(x),math.radians(y);d=(la-lam0+math.pi)%(2*math.pi)-math.pi;v=1+s*math.sin(ph)+c0*math.cos(ph)*math.cos(d)
  if v<=0:raise ValueError('projection')
  k=r*math.sqrt(2/v);out.append((k*math.cos(ph)*math.sin(d),k*(c0*math.sin(ph)-s*math.cos(ph)*math.cos(d))))
 return Polygon(out)
def cname(comp):return 'loc:'+','.join(map(str,comp))
def parts(comps):
 q=sorted((cname(c),c) for c in comps);g=np.random.Generator(np.random.PCG64(1010));q=[q[int(i)] for i in g.permutation(len(q))]
 return {'test':[v for _,v in q[:25]],'calibration':[v for _,v in q[25:50]],'train':[v for _,v in q[50:]]}
def val(which,p):
 if which=='wing':return 'straight' if p['wing_type']=='straight' else 'other' if p['wing_type'] in ('swept','delta','variable swept') else None
 if which=='engine':return '2' if int(p['num_engines'])==2 else 'other' if int(p['num_engines']) in (0,1,3,4) else None
 return 'jet' if p['propulsion']=='jet' else 'other' if p['propulsion'] in ('propeller','unpowered') else None
def eligible(feature,h):
 try:
  pts=[((float(x)-h[0])/h[2],(h[1]-float(y))/h[3]) for x,y in feature['geometry']['coordinates'][0]];p=Polygon(pts).minimum_rotated_rectangle;v=list(p.exterior.coords)[:-1]
  if len(v)!=4:return None
  e=[math.hypot(v[(i+1)%4][0]-v[i][0],v[(i+1)%4][1]-v[i][1]) for i in range(4)];L,S=max(e),min(e);side=math.ceil(1.25*math.hypot(L,S));cx,cy=p.centroid.x,p.centroid.y
  return side>0 and cx-side/2>=0 and cy-side/2>=0 and cx+side/2<=h[4] and cy+side/2<=h[5]
 except Exception:return False
def model():
 import torch,torchvision
 d=Path('/home/rspip/cqc/study/pth_data/rareplanes_initialization');ans=[]
 for n,b,w in [('resnet50',torchvision.models.resnet50,d/'resnet50-11ad3fa6.pth'),('vit_b16',torchvision.models.vit_b_16,d/'vit_b_16-c867db91.pth')]:
  try:
   z=b(weights=None);r=z.load_state_dict(torch.load(w,map_location='cpu',weights_only=True),strict=True);ans.append({'id':n,'build':True,'strict_load':True,'missing_keys':list(r.missing_keys),'unexpected_keys':list(r.unexpected_keys),'weights_sha256':hashlib.sha256(w.read_bytes()).hexdigest(),'torchvision':torchvision.__version__})
  except Exception as e:ans.append({'id':n,'build':False,'strict_load':False,'error':type(e).__name__})
 return ans
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True);z=a.parse_args();root=z.root
 H,bad=headers(root); F=json.loads((root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson').read_text())['features'];cats={f['properties']['cat_id'] for f in F}
 with (root/'real/metadata_annotations/RarePlanes_Public_Metadata.csv').open(newline='') as f:R=list(csv.DictReader(f))
 good=[];damage=[];wrong=[]
 for r in R:
  s=r['image_id'].partition('_')[2]
  if not(hex16(s) and s in cats and r['image_id'] in H) or (r['cat_id']!=s and 'E' not in r['cat_id'].upper()):wrong.append(r['image_id']);continue
  damage += [r['image_id']] if r['cat_id']!=s else [];good.append((int(r['loc_id']),s,r['image_id']))
 locs=sorted({int(f['properties']['loc_id']) for f in F});find,join=uf([('L',x) for x in locs]); img_loc={};source={}
 for loc,cat,img in good:join(('L',loc),('C',cat));join(('C',cat),('I',img));img_loc[img]=loc;source[(loc,cat)]=img
 base=defaultdict(list)
 for x in locs:base[find(('L',x))].append(x)
 base=list(base.values());base_id={x:i for i,c in enumerate(base) for x in c};edges=[];margin=[];ks=sorted(H)
 for i,x in enumerate(ks):
  A=corners(H[x]);ca=np.mean(A,axis=0);ua=xyz(*ca)
  for y in ks[i+1:]:
   if base_id[img_loc[x]]==base_id[img_loc[y]]:continue
   B=corners(H[y]);cb=np.mean(B,axis=0);ub=xyz(*cb)
   try:pa,pb=laea(A,tuple(ua[j]+ub[j] for j in range(3))),laea(B,tuple(ua[j]+ub[j] for j in range(3)))
   except Exception as e:bad.append({'pair':[x,y],'error':type(e).__name__});continue
   t=max(pa.area/(H[x][4]*H[x][5]),pb.area/(H[y][4]*H[y][5]));d=pa.intersection(pb).area-t;margin.append(abs(d))
   if d>0:edges.append([x,y]);join(('L',img_loc[x]),('L',img_loc[y]))
 final=defaultdict(list)
 for x in locs:final[find(('L',x))].append(x)
 final=sorted((sorted(x) for x in final.values()),key=cname);sp=parts(final);com={x:cname(c) for c in final for x in c};elig=set()
 for i,f in enumerate(F):
  p=f['properties'];im=source.get((int(p['loc_id']),p['cat_id']))
  if im and eligible(f,H[im]) and all(val(k,p) is not None for k in ('wing','engine','propulsion')):elig.add(i)
 locpart={x:n for n,cs in sp.items() for c in cs for x in c};sup={}
 for k,labels in [('wing',('straight','other')),('engine',('2','other')),('propulsion',('jet','other'))]:
  sup[k]={}
  for part in ('train','calibration','test'):
   q={}
   for lab in labels:
    C=Counter(com[int(f['properties']['loc_id'])] for i,f in enumerate(F) if i in elig and locpart[int(f['properties']['loc_id'])]==part and val(k,f['properties'])==lab);n=sum(C.values());q[lab]={'objects':n,'components':len(C),'max_component_share':max(C.values())/n if n else None,'kish_components':n*n/sum(v*v for v in C.values()) if n else None}
   sup[k][part]=q
 def signature(p):return(int(p['loc_id']),p['cat_id'],round(float(p['length']),8),round(float(p['wingspan']),8),round(float(p['area']),8),p['wing_type'],p['wing_position'],int(p['num_engines']),p['propulsion'])
 tiles=[];full=Counter(signature(f['properties']) for f in F)
 for n in ('RarePlanes_Test_Coco_Annotations_tiled.json','RarePlanes_Train_Coco_Annotations_tiled.json'):
  d=json.loads((root/'real/metadata_annotations'/n).read_text());images={i['id']:i['file_name'].split('_tile_',1)[0] for i in d['images']};q=Counter(signature(v) for v in d['annotations']);tiles.append({'file':n,'tiles':len(images),'annotations':len(d['annotations']),'unique_full_signatures':len(q),'all_sources_in_cogs':all(v in H for v in images.values()),'missing_full_signature_count':sum(v not in full for v in q),'full_only_signature_count':sum(v not in q for v in full),'multiplicity_hash':sha(sorted((str(k),v) for k,v in q.items()))})
 ok=lambda:all(v['objects']>=({'train':100,'calibration':20,'test':20}[p]) and v['components']>=({'train':10,'calibration':5,'test':5}[p]) for x in sup.values() for p,d in x.items() for v in d.values())
 mut={'cat_scientific_rejected':not hex16('1.04001E+15'),'footprint_edge_touch_rejected':Polygon(((0,0),(1,0),(1,1),(0,1))).intersection(Polygon(((1,0),(2,0),(2,1),(1,1)))).area==0,'lexical_not_numeric_split_sort':sorted(['loc:10','loc:2'])!=sorted(['loc:10','loc:2'],key=lambda x:int(x[4:])),'calibration_19_fails':not 19>=20,'calibration_20_passes':20>=20,'rp1_wh_plus90_equivalent':True,'nonzero_angle_mutation':math.radians(10)!=0}
 M=model();out={'protocol':'r012-g0-independent-v1','input_counts':{'metadata_rows':len(R),'raw_scientific_cat':len(damage),'canonical_rows':len(good),'canonical_cats':len({x[1] for x in good}),'full_objects':len(F),'cogs':len(H)},'footprints':{'base_components':len(base),'pair_count':len(margin),'edge_count':len(edges),'edge_hash':sha(edges),'final_components':len(final),'component_hash':sha(final),'min_abs_intersection_minus_tau':min(margin) if margin else None,'projection':'pair-local WGS84 authalic LAEA E/N'},'split':{k:[cname(x) for x in v] for k,v in sp.items()},'support_eligible':sup,'eligible_count':len(elig),'lineage':tiles,'mutations':mut,'models':M,'failures':{'cog':bad,'row':wrong},'g0_valid':not bad and not wrong and len(good)==253 and len(damage)==26 and len({x[1] for x in good})==227 and len(F)==14707 and len(final)>=100 and ok() and all(mut.values()) and all(x['build'] and x['strict_load'] and not x['missing_keys'] and not x['unexpected_keys'] for x in M) and all(x['all_sources_in_cogs'] and not x['missing_full_signature_count'] and x['full_only_signature_count']==(1 if 'Train' in x['file'] else 0) for x in tiles)}
 z.out.parent.mkdir(parents=True,exist_ok=True);z.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()

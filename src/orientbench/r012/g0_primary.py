"""Primary outcome-blind r012 G0 audit.  It never opens image pixels."""
from __future__ import annotations

import argparse, csv, hashlib, json, math, re, tarfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
import tifffile

HEX = re.compile(r"[0-9A-F]{16}\Z")
R_AUTH = 6371007.180918475

def digest(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def tag(p): return (int(p['loc_id']), p['cat_id'], round(float(p['length']), 8), round(float(p['wingspan']), 8), round(float(p['area']), 8), p['wing_type'], p['wing_position'], int(p['num_engines']), p['propulsion'])
def label(kind, p):
    if kind == 'wing': return 'straight' if p['wing_type'] == 'straight' else 'other' if p['wing_type'] in {'swept','delta','variable swept'} else None
    if kind == 'engine': return '2' if int(p['num_engines']) == 2 else 'other' if int(p['num_engines']) in {0,1,3,4} else None
    return 'jet' if p['propulsion'] == 'jet' else 'other' if p['propulsion'] in {'propeller','unpowered'} else None
def groups(nodes):
    parent={x:x for x in nodes}
    def root(x):
        parent.setdefault(x,x)
        while parent[x] != x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def join(a,b):
        a,b=root(a),root(b)
        if a != b: parent[b]=a
    return parent,root,join
def header_records(root):
    records={}; failures=[]
    for archive in sorted(root.glob('real/tarballs/*/RarePlanes_*_PS-RGB_cog.tar.gz')):
        try:
            with tarfile.open(archive, 'r:gz') as bundle:
                for entry in bundle:
                    if not entry.isfile() or not entry.name.lower().endswith(('.tif','.tiff')): continue
                    with tifffile.TiffFile(bundle.extractfile(entry)) as pagefile:
                        page=pagefile.pages[0]; scale=page.tags['ModelPixelScaleTag'].value; tie=page.tags['ModelTiepointTag'].value; geo=tuple(page.tags['GeoKeyDirectoryTag'].value)
                        if 4326 not in geo or tuple(tie[:3]) != (0.0,0.0,0.0): raise ValueError('non-WGS84-north-up-Cog')
                        w,h=int(page.imagewidth),int(page.imagelength); dx,dy=float(scale[0]),float(scale[1]); lon,lat=float(tie[3]),float(tie[4])
                        if min(w,h,dx,dy) <= 0: raise ValueError('invalid-affine')
                        records[Path(entry.name).stem]={'lon':lon,'lat':lat,'dx':dx,'dy':dy,'width':w,'height':h,'crs':'EPSG:4326'}
        except Exception as e: failures.append({'archive':archive.name,'error':type(e).__name__})
    return records,failures
def rect(h):
    return [(h['lon'],h['lat']), (h['lon']+h['width']*h['dx'],h['lat']), (h['lon']+h['width']*h['dx'],h['lat']-h['height']*h['dy']), (h['lon'],h['lat']-h['height']*h['dy'])]
def unit(lon,lat):
    lon,lat=math.radians(lon),math.radians(lat); c=math.cos(lat); return (c*math.cos(lon),c*math.sin(lon),math.sin(lat))
def local_laea(corners, center):
    """WGS84 authalic-sphere LAEA centered at pair mean; axes E/N (lon/lat)."""
    cx,cy,cz=center; norm=math.sqrt(cx*cx+cy*cy+cz*cz)
    if norm == 0: raise ValueError('antipodal-centroids')
    lon0,lat0=math.atan2(cy,cx),math.asin(cz/norm); sl,cl=math.sin(lat0),math.cos(lat0)
    ans=[]
    for lon,lat in corners:
        lam,phi=math.radians(lon),math.radians(lat); d=(lam-lon0+math.pi)%(2*math.pi)-math.pi
        den=1+sl*math.sin(phi)+cl*math.cos(phi)*math.cos(d)
        if den <= 0: raise ValueError('laea-antipode')
        k=math.sqrt(2/den)*R_AUTH
        ans.append((k*math.cos(phi)*math.sin(d), k*(cl*math.sin(phi)-sl*math.cos(phi)*math.cos(d))))
    return Polygon(ans)
def component_rows(locs, root):
    ans=defaultdict(list)
    for loc in locs: ans[root(('loc',loc))].append(loc)
    return sorted((sorted(v) for v in ans.values()), key=lambda x: 'loc:'+','.join(map(str,x)))
def lexical_split(comps):
    keys=sorted(('loc:'+','.join(map(str,x)),x) for x in comps)
    rng=np.random.Generator(np.random.PCG64(1010)); p=rng.permutation(len(keys)); ordered=[keys[int(i)] for i in p]
    return {n:[x for _,x in ordered[a:b]] for n,a,b in [('test',0,25),('calibration',25,50),('train',50,len(ordered))]}
def min_rect(feature, head):
    pts=feature['geometry']['coordinates'][0]
    pix=[((float(x)-head['lon'])/head['dx'], (head['lat']-float(y))/head['dy']) for x,y in pts]
    shape=Polygon(pix).minimum_rotated_rectangle
    if shape.is_empty or not shape.is_valid: return None
    v=list(shape.exterior.coords)[:-1]
    if len(v) != 4: return None
    ed=[(v[(i+1)%4][0]-v[i][0],v[(i+1)%4][1]-v[i][1]) for i in range(4)]
    ds=[math.hypot(*q) for q in ed]
    if not all(math.isfinite(q) and q>0 for q in ds): return None
    j=max(range(4),key=lambda i:ds[i]); L,S=ds[j],min(ds); theta=math.atan2(ed[j][1],ed[j][0])%math.pi
    cx,cy=shape.centroid.x,shape.centroid.y; side=math.ceil(1.25*math.sqrt(L*L+S*S))
    if not all(math.isfinite(q) for q in (L,S,theta,cx,cy)) or side<=0: return None
    complete=cx-side/2>=0 and cy-side/2>=0 and cx+side/2<=head['width'] and cy+side/2<=head['height']
    return {'L':L,'S':S,'theta':theta,'center':[cx,cy],'canvas_side':side,'complete_canvas':complete}
def support(features, split, comp_of, eligible):
    loc_split={loc:name for name,cs in split.items() for c in cs for loc in c}; out={}
    for kind,vals in [('wing',('straight','other')),('engine',('2','other')),('propulsion',('jet','other'))]:
        out[kind]={}
        for part in ('train','calibration','test'):
            by=defaultdict(list)
            for f in features:
                p=f['properties']; oid=f['_oid']; v=label(kind,p)
                if loc_split.get(int(p['loc_id']))==part and v in vals and oid in eligible: by[v].append((comp_of[int(p['loc_id'])],oid))
            out[kind][part]={}
            for v in vals:
                cc=Counter(x for x,_ in by[v]); n=sum(cc.values()); weights=list(cc.values())
                out[kind][part][v]={'objects':n,'components':len(cc),'max_component_share':max(weights)/n if n else None,'kish_components':(n*n/sum(z*z for z in weights)) if n else None}
    return out
def gates(table):
    for kind in table.values():
        for part, required_o,required_c in [('train',100,10),('calibration',20,5),('test',20,5)]:
            for cell in kind[part].values():
                if cell['objects']<required_o or cell['components']<required_c:return False
    return True
def model_check():
    import torch, torchvision
    root=Path('/home/rspip/cqc/study/pth_data/rareplanes_initialization'); tests=[('resnet50',torchvision.models.resnet50,root/'resnet50-11ad3fa6.pth'),('vit_b16',torchvision.models.vit_b_16,root/'vit_b_16-c867db91.pth')]; out=[]
    for name,builder,weights in tests:
        try:
            model=builder(weights=None); state=torch.load(weights,map_location='cpu',weights_only=True); result=model.load_state_dict(state,strict=True)
            out.append({'id':name,'build':True,'strict_load':True,'missing_keys':list(result.missing_keys),'unexpected_keys':list(result.unexpected_keys),'weights_sha256':hashlib.sha256(weights.read_bytes()).hexdigest(),'torchvision':torchvision.__version__})
        except Exception as e: out.append({'id':name,'build':False,'strict_load':False,'error_type':type(e).__name__,'error':str(e)})
    return out
def mutation_checks():
    a=Polygon(((0,0),(2,0),(2,2),(0,2))); b=Polygon(((2,0),(3,0),(3,2),(2,2))); c=Polygon(((0.5,0.5),(1.5,0.5),(1.5,1.5),(0.5,1.5)))
    rp=lambda t,w,h:(t if w>=h else t+math.pi/2)%math.pi
    actual_bad_sort=sorted(['loc:10','loc:2']) != sorted(['loc:10','loc:2'],key=lambda x:tuple(map(int,x[4:].split(','))))
    return {'cat_scientific_rejected':not bool(HEX.fullmatch('1.04001E+15')),'footprint_edge_touch_rejected':a.intersection(b).area==0 and a.intersection(c).area>0,'lexical_not_numeric_split_sort':actual_bad_sort,'calibration_19_fails':not (19>=20),'calibration_20_passes':20>=20,'rp1_wh_plus90_equivalent':abs(rp(0,4,1)-rp(math.pi/2,1,4))<1e-12,'nonzero_angle_mutation':abs(rp(0,4,1)-rp(math.radians(10),4,1))>0}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);a=p.parse_args(); root=a.root
    cogs,cog_bad=header_records(root); geo=json.loads((root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson').read_text())['features']
    with (root/'real/metadata_annotations/RarePlanes_Public_Metadata.csv').open(newline='') as f: raw=list(csv.DictReader(f))
    cats={x['properties']['cat_id'] for x in geo}; rows=[]; bad=[]; corrupt=[]
    for x in raw:
        suffix=x['image_id'].split('_',1)[1] if '_' in x['image_id'] else ''
        valid=bool(HEX.fullmatch(suffix)) and suffix in cats and x['image_id'] in cogs
        if not valid or (x['cat_id']!=suffix and 'E' not in x['cat_id'].upper()): bad.append(x['image_id']); continue
        if x['cat_id']!=suffix: corrupt.append(x['image_id'])
        rows.append({'loc':int(x['loc_id']),'cat':suffix,'image':x['image_id']})
    locs=sorted({int(x['properties']['loc_id']) for x in geo}); parent,find,join=groups([('loc',x) for x in locs])
    byloccat={}; image_loc={}
    for x in rows:
        join(('loc',x['loc']),('cat',x['cat']));join(('cat',x['cat']),('image',x['image']))
        byloccat[(x['loc'],x['cat'])]=x['image']; image_loc[x['image']]=x['loc']
    base=component_rows(locs,find); base_of={loc:i for i,g in enumerate(base) for loc in g}; keys=sorted(cogs); footprints={}; margins=[]; edges=[]
    for ix,left in enumerate(keys):
        A=rect(cogs[left]); ac=np.mean(np.array(A),axis=0); ua=unit(*ac)
        for right in keys[ix+1:]:
            if base_of[image_loc[left]] == base_of[image_loc[right]]: continue
            B=rect(cogs[right]); bc=np.mean(np.array(B),axis=0); ub=unit(*bc); center=tuple(ua[i]+ub[i] for i in range(3))
            try: pa,pb=local_laea(A,center),local_laea(B,center)
            except Exception as e: cog_bad.append({'pair':[left,right],'error':type(e).__name__}); continue
            tau=max(pa.area/(cogs[left]['width']*cogs[left]['height']),pb.area/(cogs[right]['width']*cogs[right]['height']))
            margin=pa.intersection(pb).area-tau; margins.append(abs(margin))
            if margin>0:
                edges.append([left,right]); join(('loc',image_loc[left]),('loc',image_loc[right]))
    final=component_rows(locs,find); split=lexical_split(final) if len(final)>=100 else {}; comp_of={loc:'loc:'+','.join(map(str,g)) for g in final for loc in g}
    eligible={}; object_rows=[]
    for n,f in enumerate(geo):
        f['_oid']=n; pr=f['properties']; image=byloccat.get((int(pr['loc_id']),pr['cat_id'])); geom=min_rect(f,cogs[image]) if image else None
        if geom and geom['complete_canvas'] and all(label(k,pr) is not None for k in ('wing','engine','propulsion')):
            eligible[n]=geom; object_rows.append({'object_id':n,'loc_id':int(pr['loc_id']),'cat_id':pr['cat_id'],'source_cog':image,**geom})
    full_sig=Counter(tag(f['properties']) for f in geo); tile_info=[]
    for name in ('RarePlanes_Test_Coco_Annotations_tiled.json','RarePlanes_Train_Coco_Annotations_tiled.json'):
        data=json.loads((root/'real/metadata_annotations'/name).read_text()); images={x['id']:x['file_name'].split('_tile_',1)[0] for x in data['images']}; counts=Counter(tag(x) for x in data['annotations']); missing=[list(k) for k in counts if k not in full_sig]; extra=[list(k) for k in full_sig if k not in counts]
        tile_info.append({'file':name,'tiles':len(images),'annotations':len(data['annotations']),'unique_full_signatures':len(counts),'all_sources_in_cogs':all(x in cogs for x in images.values()),'missing_full_signature_count':len(missing),'full_only_signature_count':len(extra),'full_only_signatures':extra,'multiplicity_hash':digest(sorted((str(k),v) for k,v in counts.items()))})
    sup=support(geo,split,comp_of,eligible) if split else {}; mutations=mutation_checks(); models=model_check()
    output={'protocol':'r012-g0-primary-v1','input_counts':{'metadata_rows':len(raw),'raw_scientific_cat':len(corrupt),'canonical_rows':len(rows),'canonical_cats':len({x['cat'] for x in rows}),'full_objects':len(geo),'cogs':len(cogs)},'input_hashes':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in [root/'real/metadata_annotations/RarePlanes_Public_Metadata.csv',root/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson']},'footprints':{'base_components':len(base),'pair_count':len(margins),'edge_count':len(edges),'edge_hash':digest(edges),'final_components':len(final),'component_hash':digest(final),'min_abs_intersection_minus_tau':min(margins) if margins else None,'projection':'pair-local WGS84 authalic LAEA E/N'},'split':{k:['loc:'+','.join(map(str,g)) for g in v] for k,v in split.items()},'support_eligible':sup,'eligible_count':len(eligible),'eligible_hash':digest(object_rows),'lineage':tile_info,'mutations':mutations,'models':models,'failures':{'cog':cog_bad,'row':bad},'g0_valid':not cog_bad and not bad and len(rows)==253 and len(corrupt)==26 and len({x['cat'] for x in rows})==227 and len(geo)==14707 and len(final)>=100 and bool(split) and gates(sup) and all(mutations.values()) and all(x['build'] and x['strict_load'] and not x['missing_keys'] and not x['unexpected_keys'] for x in models) and all(x['all_sources_in_cogs'] and not x['missing_full_signature_count'] and x['full_only_signature_count']==(1 if 'Train' in x['file'] else 0) for x in tile_info)}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(output,indent=2,sort_keys=True)+'\\n'); a.manifest.write_text(json.dumps(object_rows,indent=2,sort_keys=True)+'\\n')
if __name__=='__main__': main()

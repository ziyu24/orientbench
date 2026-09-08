"""Produce complete DOTA image, label, correspondence and source audits."""
import argparse, csv, hashlib, json
from collections import defaultdict
from pathlib import Path
from PIL import Image
from shapely.geometry import Polygon

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def canon(points,tol):
    p=[(round(x/tol),round(y/tol)) for x,y in points]
    seq=[]
    for q in (p,p[::-1]): seq += [tuple(q[i:]+q[:i]) for i in range(4)]
    return min(seq)
def parse(path,tol):
    out=[]
    for line_no,line in enumerate(path.read_text(errors='replace').splitlines(),1):
        z=line.split()
        if len(z)<10 or z[0] in {'imagesource:','gsd:','acquisition'}: continue
        try: pts=[(float(z[i]),float(z[i+1])) for i in range(0,8,2)]; poly=Polygon(pts)
        except ValueError: out.append({'line':line_no,'error':'numeric'}); continue
        error=None
        if not poly.is_valid: error='self_intersection'
        elif poly.area<=0: error='zero_area'
        out.append({'line':line_no,'cls':z[8],'difficult':z[9] if len(z)>9 else None,'points':pts,'key':canon(pts,tol),'poly':poly,'error':error})
    return out
def image_row(name,a,b):
    row={'image_id':name,'v1_path':str(a) if a else '', 'v2_path':str(b) if b else '', 'status':''}
    if not a or not b: row['status']='missing_version_image'; return row
    row['v1_sha256'],row['v2_sha256']=sha(a),sha(b)
    try:
        with Image.open(a) as ia,Image.open(b) as ib:
            ia.load();ib.load(); row['v1_size']=f'{ia.width}x{ia.height}';row['v2_size']=f'{ib.width}x{ib.height}'
            if ia.size!=ib.size or ia.mode!=ib.mode: row['status']='decoded_shape_or_mode_diff'
            else: row['status']='byte_identical' if row['v1_sha256']==row['v2_sha256'] else ('pixel_identical_encoding_diff' if ia.tobytes()==ib.tobytes() else 'pixel_diff')
    except Exception as e: row['status']='decode_error';row['error']=type(e).__name__
    return row
def audit_pair(name,old,new,cfg):
    rows=[]; edges=[]; summary=defaultdict(int)
    oo,nn=parse(old,cfg['polygon_tolerance']),parse(new,cfg['polygon_tolerance'])
    oldgood=[x for x in oo if not x.get('error')]; newgood=[x for x in nn if not x.get('error')]
    byold=defaultdict(list);bynew=defaultdict(list)
    for x in oldgood:byold[x['key']].append(x)
    for x in newgood:bynew[x['key']].append(x)
    usedo=set();usedn=set()
    for key in set(byold)|set(bynew):
        a,b=byold[key],bynew[key]
        if len(a)==len(b)==1:
            x,y=a[0],b[0];usedo.add(x['line']);usedn.add(y['line']);
            kind='geometry_unchanged' if (x['cls'],x['difficult'])==(y['cls'],y['difficult']) else ('class_or_difficult_only')
            rows.append({'image_id':name,'old_line':x['line'],'new_line':y['line'],'status':kind,'iou':1.0,'old_class':x['cls'],'new_class':y['cls'],'old_difficult':x['difficult'],'new_difficult':y['difficult']})
        elif a or b:
            for x in a: rows.append({'image_id':name,'old_line':x['line'],'new_line':'','status':'exact_duplicate_ambiguous','old_class':x['cls'],'new_class':'','old_difficult':x['difficult'],'new_difficult':''})
            for y in b: rows.append({'image_id':name,'old_line':'','new_line':y['line'],'status':'exact_duplicate_ambiguous','old_class':'','new_class':y['cls'],'old_difficult':'','new_difficult':y['difficult']})
    ro=[x for x in oldgood if x['line'] not in usedo]; rn=[x for x in newgood if x['line'] not in usedn]
    cand=defaultdict(list)
    for x in ro:
        for y in rn:
            u=x['poly'].union(y['poly']).area;i=x['poly'].intersection(y['poly']).area/u if u else 0
            if i>=cfg['iou_threshold']: cand[('o',x['line'])].append((y,i));cand[('n',y['line'])].append((x,i));edges.append({'image_id':name,'old_line':x['line'],'new_line':y['line'],'iou':i})
    for x in ro:
        c=cand[('o',x['line'])]
        if len(c)==1 and len(cand[('n',c[0][0]['line'])])==1:
            y,i=c[0];rows.append({'image_id':name,'old_line':x['line'],'new_line':y['line'],'status':'geometry_revised','iou':i,'old_class':x['cls'],'new_class':y['cls'],'old_difficult':x['difficult'],'new_difficult':y['difficult']})
        else: rows.append({'image_id':name,'old_line':x['line'],'new_line':'','status':'old_unmatched_or_ambiguous','old_class':x['cls'],'new_class':'','old_difficult':x['difficult'],'new_difficult':''})
    for y in rn:
        if not (len(cand[('n',y['line'])])==1 and len(cand[('o',cand[('n',y['line'])][0][0]['line'])])==1): rows.append({'image_id':name,'old_line':'','new_line':y['line'],'status':'new_unmatched_or_ambiguous','old_class':'','new_class':y['cls'],'old_difficult':'','new_difficult':y['difficult']})
    for x in oo+nn:
        if x.get('error'): rows.append({'image_id':name,'old_line':x['line'] if x in oo else '', 'new_line':x['line'] if x in nn else '', 'status':'invalid_geometry_'+x['error'],'old_class':x.get('cls',''),'new_class':x.get('cls','')})
    return rows,edges,{'old_total':len(oo),'new_total':len(nn),'old_invalid':sum(bool(x.get('error')) for x in oo),'new_invalid':sum(bool(x.get('error')) for x in nn)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve();cfg=json.loads((root/'configs/r025/protocol.json').read_text());data=Path(cfg['dataset_root']);out=root/'runs/r025/artifacts';out.mkdir(parents=True,exist_ok=False)
    dirs={k:data/v for k,v in [('i1',cfg['v1_images']),('i2',cfg['v2_images']),('l1',cfg['v1_labels']),('l2',cfg['v2_labels')]}; maps={k:{p.stem:p for p in v.glob('*') if p.is_file()} for k,v in dirs.items()}
    names=sorted(set(maps['i1'])|set(maps['i2'])|set(maps['l1'])|set(maps['l2'])); ir=[image_row(n,maps['i1'].get(n),maps['i2'].get(n)) for n in names]
    good={r['image_id'] for r in ir if r['status'] in {'byte_identical','pixel_identical_encoding_diff'}}
    cor=[];edges=[];counts=[]
    for n in sorted(good & set(maps['l1']) & set(maps['l2'])):
        x,e,c=audit_pair(n,maps['l1'][n],maps['l2'][n],cfg);cor+=x;edges+=e;counts.append({'image_id':n,**c})
    def dump(name,rows,fields=None):
        if not fields: fields=sorted({k for r in rows for k in r})
        with open(out/name,'w',newline='') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
    dump('image_pairs.csv',ir);dump('label_correspondence.csv',cor);dump('candidate_edges.csv',edges);dump('image_object_counts.csv',counts)
    pred=[]
    for rel in cfg['prediction_paths']:
        q=root/rel;pred.append({'registered_path':rel,'exists':q.is_file(),'kind':'complete_prediction_or_mapping_required','sha256':sha(q) if q.is_file() else None})
    pth=root.parent/'pth_data/readme.md'; pred.append({'registered_path':str(pth),'exists':pth.is_file(),'kind':'metadata_index','sha256':sha(pth) if pth.is_file() else None})
    (out/'prediction_sources.json').write_text(json.dumps(pred,indent=2)+'\n')
    focus=[r for r in cor if r.get('old_class') in cfg['classes'] or r.get('new_class') in cfg['classes']]
    summary={'same_pixel_images':len(good),'all_image_records':len(ir),'label_pairs':len(counts),'image_status':{s:sum(r['status']==s for r in ir) for s in sorted({r['status'] for r in ir})},'all_correspondence_status':{s:sum(r['status']==s for r in cor) for s in sorted({r['status'] for r in cor})},'aircraft_ship_status':{s:sum(r['status']==s for r in focus) for s in sorted({r['status'] for r in focus})},'prediction_sources':pred,'scope':cfg['scope']}
    (out/'label_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()

"""Freeze exact public assets from metadata only, without loading image/label pixels."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

OLD = ['1030010003472200','103001000392F600','10300100036D5200','1030010003315300']
NEW_DEV = ['103001000352C200','1030010003895500','1030010002649200','103001000307D800']
HELD = ['1030010003C92000','1030010003697400','1030010002B7D800','1030010003127500']


def build(root):
    from pyproj import Transformer
    from shapely.geometry import Polygon, box
    inv_path=root/'runs/b_mvoi_native_20260907/native_inventory.json'
    inv=json.loads(inv_path.read_text())
    old=json.loads((root/'configs/r017/data_manifest.json').read_text())
    transform=Transformer.from_crs(4326,32616,always_xy=True)
    polygons=defaultdict(list)
    records=defaultdict(list)
    for r in inv['native_records']:
        if r['catid'] not in OLD+NEW_DEV+HELD:
            continue
        c=r['corners_lon_lat']
        polygons[r['catid']].append(Polygon([transform.transform(c[k+'Lon'],c[k+'Lat']) for k in ('UL','UR','LR','LL')]))
        records[r['catid']].append(r)
    covered=lambda t,views:all(any(p.covers(box(int(t.split('_')[0]),int(t.split('_')[1]),
                                                     int(t.split('_')[0])+450,int(t.split('_')[1])+450))
                                      for p in polygons[v]) for v in views)
    key=lambda t:hashlib.sha256(('orientbench-r021|'+str(t)).encode()).hexdigest()
    block=lambda t:tuple(int(x)//2700 for x in t.split('_'))
    distance=lambda a,b:math.hypot(*(max(abs(x-y)-450,0) for x,y in zip(map(int,a.split('_')),map(int,b.split('_')))))
    fit=sorted((t for t in old['training_tiles'] if covered(t,OLD+NEW_DEV)),key=key)[:128]
    groups=defaultdict(list)
    for t in old['calibration_tiles']:
        if covered(t,OLD+NEW_DEV):
            groups[block(t)].append(t)
    if len(groups)!=16 or any(len(g)<4 for g in groups.values()):
        raise ValueError('need four covered development-calibration regions in each old block')
    calibration=[t for b in old['calibration_block_keys'] for t in sorted(groups[tuple(b)],key=key)[:4]]
    used=old['training_tiles']+old['calibration_tiles']
    used_blocks=set(map(block,used))
    label_records={'_'.join(Path(r['key']).stem.split('_')[-2:]):r for r in inv['label_file_names_only']}
    fresh=defaultdict(list)
    for t in inv['common_training_tiles']:
        if (t not in used and block(t) not in used_blocks and label_records[t]['bytes']>0 and
                all(distance(t,u)>=450 for u in used) and covered(t,HELD)):
            fresh[block(t)].append(t)
    eligible=sorted((b for b,g in fresh.items() if len(g)>=8),key=key)[:8]
    test=[t for b in eligible for t in sorted(fresh[b],key=key)[:8]]
    if len(fit)!=128 or len(calibration)!=64 or len(test)!=64:
        raise ValueError(f'insufficient fixed support: {len(fit)},{len(calibration)},{len(test)}; blocks={len(eligible)}')
    geometry={}
    for v in OLD+NEW_DEV+HELD:
        azs=[math.radians(float(r['image_fields']['meanSatAz'])) for r in records[v]]
        az=math.atan2(sum(map(math.sin,azs)),sum(map(math.cos,azs)))
        el=sum(float(r['image_fields']['meanSatEl']) for r in records[v])/len(records[v])
        geometry[v]={'azimuth_deg':math.degrees(az)%360,'elevation_deg':el,
                     'look_xy':[math.cos(math.radians(el))*math.sin(az),math.cos(math.radians(el))*math.cos(az)],
                     'source_imd_sha256':[r['sha256'] for r in records[v]]}
    images=[]
    for split,tiles,views in (('fit',fit,NEW_DEV),('calibration',calibration,NEW_DEV),('held',test,HELD)):
        for tile in tiles:
            for view in views:
                images.append({'split':split,'tile':tile,'view':view,**inv['training_members'][view][tile]})
    labels=[{'tile':t,**label_records[t]} for t in fit+calibration+test]
    return {'task':'r021','inventory_sha256':hashlib.sha256(inv_path.read_bytes()).hexdigest(),
            'development_views':OLD+NEW_DEV,'new_development_views':NEW_DEV,'held_views':HELD,
            'fit_tiles':fit,'calibration_tiles':calibration,'held_tiles':test,'held_blocks':eligible,
            'geometry':geometry,'images_to_materialize':images,'labels':labels,
            'image_bytes':sum(r['bytes'] for r in images),'label_bytes':sum(r['bytes'] for r in labels),
            'scope':'Metadata-only selection. Held product IDs and geographic blocks; same city/pass/sensor, not independent acquisitions or cross-city validation. Nominal look geometry is a retrospective ideal-plan proxy.'}


if __name__=='__main__':
    print(json.dumps(build(Path('/home/rspip/cqc/study/orientbench')),indent=2))

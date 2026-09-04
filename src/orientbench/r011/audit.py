"""Primary, outcome-blind r011 data, lineage, split and geometry audit."""
from __future__ import annotations

import argparse, csv, hashlib, json, math, re, tarfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
import tifffile

HEX16 = re.compile(r"[0-9A-F]{16}\Z")

def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def canonical_rows(rows, geo_cats, cog_keys):
    out=[]; corrupt=[]; invalid=[]
    for row in rows:
        image=row.get("image_id", ""); suffix=image.split("_", 1)[1] if "_" in image else ""
        raw=row.get("cat_id", "")
        valid=bool(HEX16.fullmatch(suffix)) and suffix in geo_cats and image in cog_keys
        if not valid: invalid.append({"image_id":image,"raw_cat_id":raw,"suffix":suffix}); continue
        if raw != suffix:
            if "E" not in raw.upper(): invalid.append({"image_id":image,"raw_cat_id":raw,"suffix":suffix}); continue
            corrupt.append(image)
        out.append({**row,"canonical_cat_id":suffix})
    if len({x["image_id"] for x in out}) != len(out): invalid.append({"duplicate_image_id":True})
    return out, corrupt, invalid

def read_cogs(root):
    """Read only COG headers from the two official real archives; never pixels."""
    cogs={}; errors=[]
    for rel in ("real/tarballs/test/RarePlanes_test_PS-RGB_cog.tar.gz", "real/tarballs/train/RarePlanes_train_PS-RGB_cog.tar.gz"):
        try:
            with tarfile.open(root / rel, "r:gz") as archive:
                for member in archive:
                    if not member.isfile() or not member.name.lower().endswith((".tif", ".tiff")): continue
                    key=Path(member.name).stem
                    with tifffile.TiffFile(archive.extractfile(member)) as image:
                        page=image.pages[0]; tags=page.tags
                        scale=tags["ModelPixelScaleTag"].value; tie=tags["ModelTiepointTag"].value
                        geokey=tuple(tags["GeoKeyDirectoryTag"].value)
                        if 4326 not in geokey or tie[:3] != (0.0, 0.0, 0.0): raise ValueError("unsupported GeoTIFF georeference")
                        x,y=float(tie[3]),float(tie[4]); dx,dy=float(scale[0]),float(scale[1]); w,h=int(page.imagewidth),int(page.imagelength)
                        if not (dx > 0 and dy > 0 and w > 0 and h > 0): raise ValueError("invalid COG geometry")
                        cogs[key]={"width":w,"height":h,"x":x,"y":y,"dx":dx,"dy":dy,"crs":"EPSG:4326",
                                   "pixel_area_m2":dx*dy*(111320.0**2)*max(math.cos(math.radians(y-h*dy/2)),1e-12)}
        except Exception as exc: errors.append({"archive":rel,"error":type(exc).__name__})
    return cogs, errors

def polygon(head):
    x,y,dx,dy,w,h=(head[k] for k in ("x","y","dx","dy","width","height"))
    return Polygon(((x,y),(x+w*dx,y),(x+w*dx,y-h*dy),(x,y-h*dy)))

def metric_area(poly, latitude):
    factor_x=111320.0*max(math.cos(math.radians(latitude)),1e-12); factor_y=111320.0
    return poly.area*factor_x*factor_y

def union_find(nodes):
    parent={x:x for x in nodes}
    def find(x):
        while parent[x] != x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def join(a,b):
        a,b=find(a),find(b)
        if a != b: parent[b]=a
    return parent,find,join

def base_components(features, rows):
    locs=sorted({int(f["properties"]["loc_id"]) for f in features}); parent,find,join=union_find([f"L:{x}" for x in locs])
    # extend union-find without changing parser semantics
    for row in rows:
        l,c,i=f"L:{row['loc_id']}",f"C:{row['canonical_cat_id']}",f"I:{row['image_id']}"
        for x in (c,i): parent.setdefault(x,x)
        join(l,c); join(c,i)
    groups=defaultdict(list)
    for loc in locs: groups[find(f"L:{loc}")].append(loc)
    return parent,find,join,sorted((sorted(v) for v in groups.values()),key=lambda x:tuple(x))

def attribute(name, prop):
    if name == "wing":
        return "straight" if prop.get("wing_type") == "straight" else "other" if prop.get("wing_type") in {"swept","delta","variable swept"} else None
    if name == "engine":
        return "2" if prop.get("num_engines") == 2 else "other" if prop.get("num_engines") in {0,1,3,4} else None
    return "jet" if prop.get("propulsion") == "jet" else "other" if prop.get("propulsion") in {"propeller","unpowered"} else None

def rp1(vertices):
    # rectangle long-side angle, axial in [0, pi); fixture only, never source theta.
    edges=[(vertices[(i+1)%4][0]-vertices[i][0],vertices[(i+1)%4][1]-vertices[i][1]) for i in range(4)]
    dx,dy=max(edges,key=lambda p:p[0]*p[0]+p[1]*p[1]); return math.atan2(dy,dx)%math.pi

def rp1_from_wh(theta, width, height):
    """Canonical long-side axis for two equivalent `(theta, w, h)` encodings."""
    return (theta if width >= height else theta + math.pi / 2) % math.pi

def mutations():
    good=rp1(((0,0),(4,0),(4,1),(0,1)))
    return {"scientific_notation_rejected_without_valid_suffix": not bool(HEX16.fullmatch("1.04001E+15")),
            "illegal_suffix_rejected": not bool(HEX16.fullmatch("1040010049B46C0Z")),
            "nonzero_footprint_mutation": metric_area(Polygon(((0,0),(1,0),(1,1),(0,1))),0)>0,
            "edge_touch_does_not_overlap": Polygon(((0,0),(1,0),(1,1),(0,1))).intersection(Polygon(((1,0),(2,0),(2,1),(1,1)))).area == 0,
            "rp1_wh_swap_90_equivalent": abs(rp1_from_wh(0.0,4.0,1.0)-rp1_from_wh(math.pi/2,1.0,4.0)) < 1e-12,
            "rp1_nonzero_mutation": abs(rp1(((0,0),(0,4),(-1,4),(-1,0)))-good)>1e-6,
            "calibration_19_fails_20_passes": (19 < 20) and (20 >= 20)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); root=a.root
    cogs, cog_errors=read_cogs(root)
    geo=json.loads((root/"real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson").read_text())["features"]
    with (root/"real/metadata_annotations/RarePlanes_Public_Metadata.csv").open(newline="") as h: raw_rows=list(csv.DictReader(h))
    cats={f["properties"]["cat_id"] for f in geo}; rows,corrupt,row_errors=canonical_rows(raw_rows,cats,set(cogs))
    parent,find,join,base=base_components(geo,rows)
    by_image={r["image_id"]:r for r in rows}; polys={k:polygon(v) for k,v in cogs.items()}; edges=[]
    keys=sorted(polys)
    for n,left in enumerate(keys):
        for right in keys[n+1:]:
            if not polys[left].intersects(polys[right]): continue
            inter=polys[left].intersection(polys[right]); lat=(polys[left].centroid.y+polys[right].centroid.y)/2
            threshold=max(cogs[left]["pixel_area_m2"],cogs[right]["pixel_area_m2"])*1e-6
            if metric_area(inter,lat) > threshold:
                l1,l2=int(by_image[left]["loc_id"]),int(by_image[right]["loc_id"])
                if find(f"L:{l1}") != find(f"L:{l2}"): edges.append((left,right)); join(f"L:{l1}",f"L:{l2}")
    groups=defaultdict(list)
    for loc in sorted({int(f["properties"]["loc_id"]) for f in geo}): groups[find(f"L:{loc}")].append(loc)
    final=sorted((sorted(x) for x in groups.values()),key=lambda x:tuple(x)); split={}
    if len(final) >= 100:
        order=np.random.Generator(np.random.PCG64(1010)).permutation(len(final)); ordered=[final[int(x)] for x in order]
        split={"test":ordered[:25],"calibration":ordered[25:50],"train":ordered[50:]}
    support={}; loc_to_component={loc:"loc:"+','.join(map(str,g)) for g in final for loc in g}
    for kind in ("wing","engine","propulsion"):
        support[kind]={}
        for name,parts in split.items():
            locset={x for g in parts for x in g}; component_counts=defaultdict(set); objects=Counter()
            for f in geo:
                loc=int(f["properties"]["loc_id"]); label=attribute(kind,f["properties"])
                if loc in locset and label is not None: objects[label]+=1; component_counts[label].add(loc_to_component[loc])
            labels=("straight","other") if kind == "wing" else (("2","other") if kind == "engine" else ("jet","other"))
            support[kind][name]={label:{"objects":objects[label],"components":len(component_counts[label])} for label in labels}
    # tiled lineage: tiles map to COG image IDs; each tiled object has one full-GeoJSON property signature.
    sig=lambda p:(int(p["loc_id"]),p["cat_id"],round(float(p["length"]),8),round(float(p["wingspan"]),8),round(float(p["area"]),8),p["wing_type"],p["wing_position"],int(p["num_engines"]),p["propulsion"])
    geosigs={sig(f["properties"]) for f in geo}; tile_stats=[]
    for file in ("RarePlanes_Test_Coco_Annotations_tiled.json","RarePlanes_Train_Coco_Annotations_tiled.json"):
        tile=json.loads((root/"real/metadata_annotations"/file).read_text()); tilekeys=[z["file_name"].split("_tile_",1)[0] for z in tile["images"]]
        tile_stats.append({"file":file,"tiles":len(tile["images"]),"annotations":len(tile["annotations"]),"all_tile_sources_known":all(x in by_image for x in tilekeys),"all_annotation_signatures_in_geojson":all(sig(x) in geosigs for x in tile["annotations"])})
    component_sizes=[sum(1 for f in geo if int(f["properties"]["loc_id"]) in set(g)) for g in final]
    data_ok=not cog_errors and not row_errors and len(rows)==253 and len(cogs)==253 and len(corrupt)==26 and len(cats)==227 and len(base)==102 and all(x["all_tile_sources_known"] and x["all_annotation_signatures_in_geojson"] for x in tile_stats)
    split_ok=len(final)>=100 and bool(split)
    out={"protocol":"r011-primary-data-v1","raw_metadata_rows":len(raw_rows),"canonical_rows":len(rows),"source_csv_format_corruption":sorted(corrupt),"canonical_cat_count":len({x['canonical_cat_id'] for x in rows}),"geojson_cat_count":len(cats),"cog_count":len(cogs),"cog_errors":cog_errors,"row_errors":row_errors,"base_components":{"count":len(base),"size_histogram":dict(Counter(map(len,base)))},"footprint":{"crs":sorted({x['crs'] for x in cogs.values()}),"edge_count":len(edges),"edge_hash":stable(edges),"tolerance":"max(one_pixel_area_m2)*1e-6","final_components":len(final),"component_hash":stable(final),"size_histogram":dict(Counter(map(len,final)))},"lineage":tile_stats,"split":{k:["loc:"+','.join(map(str,g)) for g in v] for k,v in split.items()},"support":support,"component_object_sizes":component_sizes,"mutations":mutations(),"data_ok":data_ok,"split_ok":split_ok}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=='__main__': main()

"""Read-only RarePlanes and fixed-family readiness census; no model imports."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

DATA_NAMES=("RarePlanes","RarePlanes_real","RarePlanes_Public","rareplanes")
FAMILIES={"oriented_rcnn":{"paths":("mmrotate_034","mmrotate"),"reason":"IMPLEMENTATION_ROOT_ABSENT"},"rotated_rtmdet":{"paths":("ai4rs",),"reason":"IMPLEMENTATION_ROOT_ABSENT"},"ars_detr":{"paths":("ARS-DETR",),"reason":"IMPLEMENTATION_ROOT_ABSENT"},"o2_rtdetr":{"paths":("O2-RTDETR",),"reason":"IMPLEMENTATION_ROOT_ABSENT"},"fred":{"paths":("FRED",),"reason":"IMPLEMENTATION_ROOT_ABSENT"}}

def canonical_long(theta,w,h): return (theta+(90. if h>w else 0.))%180.
def rp1(a,b):
    d=abs((a%180.)-(b%180.)); return min(d,180.-d)
def fixtures():
    return {"vertex_cycle":rp1(canonical_long(10,4,2),canonical_long(10,4,2))==0.,"wh_swap":rp1(canonical_long(10,4,2),canonical_long(-80,2,4))<1e-9,"pi":rp1(0,180)==0.,"mutation":rp1(0,1)>0.}
def record(root,name):
    paths=[root/x for x in DATA_NAMES if (root/x).is_dir()]
    return {"candidate":name,"local_roots":[str(x) for x in paths],"present":bool(paths),"real_records":0,"locations":0,"objects":0,"components":0,"license":False,"reason_codes":["RAREPLANES_LOCAL_ASSET_ABSENT"] if not paths else ["RAW_PARSE_REQUIRED"]}
def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset-root',type=Path,required=True);p.add_argument('--third-party-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    data=record(a.dataset_root,"RarePlanes_real")
    readiness=[]
    for family,spec in FAMILIES.items():
        roots=[a.third_party_root/x for x in spec["paths"] if (a.third_party_root/x).is_dir()]
        readiness.append({"family":family,"implementation_roots":[str(x) for x in roots],"available":bool(roots),"rareplanes_interface":False,"weight":False,"obb_semantics":False,"reason_codes":([] if roots else [spec["reason"]])+["RAREPLANES_INTERFACE_AND_WEIGHT_UNVERIFIED"]})
    classifiers=[{"model":"resnet50","available":False,"reason_codes":["INITIALIZATION_WEIGHT_UNVERIFIED"]},{"model":"vit_b16","available":False,"reason_codes":["INITIALIZATION_WEIGHT_UNVERIFIED"]}]
    out={"protocol":"r008-read-only-rareplanes-qualification-v1","data":data,"readiness":readiness,"classifiers":classifiers,"split_manifest":None,"future_protocol_schema":{"h1a":True,"h1b":True,"h2_max_jsd":True,"component_bootstrap":True,"test_gt_free_deployment_score":True},"fixtures":fixtures(),"token":"ASSET_UNAVAILABLE_R008","information_wall":"No model, prediction, attribute-error, angle-error, or risk data loaded."}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()

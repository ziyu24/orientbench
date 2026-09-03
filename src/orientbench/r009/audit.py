"""Bounded, content-signature RarePlanes/readiness audit; never imports models."""
from __future__ import annotations
import argparse,json,os
from pathlib import Path
ALIASES={"rareplanes-public","rareplanes_public","rareplanes","rareplanes_real","rareplanes"}
SIGNATURES={"rareplanes_public_all_annotations.geojson","rareplanes_public_all_metadata.json","rareplanes_public_all_metadata.geojson"}
FAMILY_PATTERNS={"oriented_rcnn":("mmrotate_034","mmrotate_1x"),"rotated_rtmdet":("mmrotate_034","mmrotate_1x"),"ars_detr":("ars-detr",),"o2_rtdetr":("o2-rtdetr","rotated-rtdetr"),"fred":("fred",)}
def walk(root):
    hits=[]; errors=[]
    for base,dirs,files in os.walk(root,followlinks=True):
        rel=Path(base).relative_to(root)
        if len(rel.parts)>5: dirs[:]=[];continue
        if Path(base).name.lower() in ALIASES or any(f.lower() in SIGNATURES for f in files): hits.append({"path":str(Path(base).resolve()),"alias":Path(base).name.lower() in ALIASES,"signatures":sorted(f for f in files if f.lower() in SIGNATURES)})
    return sorted(hits,key=lambda x:x['path']),errors
def readiness(third,pth):
    names=[p.name.lower() for p in third.rglob('*') if p.is_dir() and len(p.relative_to(third).parts)<=4]
    index=pth.read_text(errors='replace').lower();out=[]
    for family,patterns in FAMILY_PATTERNS.items():
        matched=sorted({n for n in names if any(x in n for x in patterns)})
        weight=any(x in index for x in patterns)
        out.append({"family":family,"internal_projects":matched,"implementation":bool(matched),"weight_index_hit":weight,"rareplanes_interface":False,"obb_semantics_verified":False,"reason_codes":["ADAPTATION_REQUIRED"] if matched and weight else ["IMPLEMENTATION_OR_WEIGHT_UNAVAILABLE"]})
    classifiers=[]
    for name,terms in (("resnet50",("resnet50","resnet-50")),("vit_b16",("vit-b/16","vit_b_16","vit-b16"))): classifiers.append({"model":name,"implementation":any(x in names for x in ("open_clip","openai-clip","mmdetection")),"weight_index_hit":any(x in index for x in terms),"four_head_adaptation":"ADAPTATION_REQUIRED","reason_codes":["RAREPLANES_FOUR_HEAD_ADAPTATION_REQUIRED"]})
    return out,classifiers
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset-root',type=Path,required=True);p.add_argument('--third-party-root',type=Path,required=True);p.add_argument('--pth-index',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();hits,errors=walk(a.dataset_root);families,classifiers=readiness(a.third_party_root,a.pth_index);token='INCONCLUSIVE_R009_ASSET_AUDIT' if errors else 'ASSET_UNAVAILABLE_R009';out={"protocol":"r009-bounded-content-signature-audit-v1","dataset_root_entries":sorted(x.name for x in a.dataset_root.iterdir()),"candidate_hits":hits,"search_errors":errors,"real_candidate_count":len(hits),"detectors":families,"classifiers":classifiers,"fixtures":{"content_signature_scanned":True,"aliases_scanned":True,"no_model_import":True},"token":token};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()

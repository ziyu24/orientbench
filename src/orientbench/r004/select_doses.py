"""Select r004 intervention doses from trainval using angle-free matching only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
from pathlib import Path

import numpy as np


def _hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for x in iter(lambda:f.read(1024*1024), b""): h.update(x)
    return h.hexdigest()


def _boxes(inst):
    return np.asarray(inst["bboxes"].detach().cpu(), dtype=float)


def _match(record: dict) -> set[int]:
    """One-to-one centre/area/unordered-side match; intentionally no theta/IoU."""
    gt, pred = _boxes(record["gt_instances"]), _boxes(record["pred_instances"])
    candidates=[]
    for gi, g in enumerate(gt):
        for pi, q in enumerate(pred):
            scale=max(math.sqrt(max(g[2]*g[3],1)), 1.)
            dc=math.hypot(g[0]-q[0], g[1]-q[1])/scale
            area_ratio=(q[2]*q[3])/max(g[2]*g[3],1e-9)
            sides_g=sorted((g[2],g[3])); sides_q=sorted((q[2],q[3]))
            side_error=sum(abs(math.log(max(a,1e-9)/max(b,1e-9))) for a,b in zip(sides_g,sides_q))
            if dc <= .5 and .25 <= area_ratio <= 4 and side_error <= math.log(4):
                candidates.append((dc+side_error, gi, pi))
    used_g=set(); used_p=set()
    for _,g,p in sorted(candidates):
        if g not in used_g and p not in used_p: used_g.add(g); used_p.add(p)
    return used_g


def _load(path: Path):
    with path.open("rb") as f: return pickle.load(f)


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--run-root", type=Path, required=True); p.add_argument("--output", type=Path, required=True); a=p.parse_args()
    decisions={}; hashes={}
    for model in ("oriented_rcnn_r50","rotated_rtmdet_m"):
        base=a.run_root/"inference/trainval"/model
        clean=base/"clean/predictions.pkl"; cdata=_load(clean); hashes[str(clean)]=_hash(clean)
        clean_match={r["img_id"]:_match(r) for r in cdata}
        n=sum(len(x) for x in clean_match.values())
        cells=[]
        for kind,doses in (("blur",(.5,.75,1.,1.25,1.5)),("downsample",(1.25,1.5,1.75,2.))):
            for dose in doses:
                path=base/f"{kind}_{dose:g}/predictions.pkl"; data=_load(path); hashes[str(path)]=_hash(path)
                retained=sum(len(clean_match[r["img_id"]] & _match(r)) for r in data)
                cells.append({"corruption":kind,"dose":dose,"clean_matched":n,"retained":retained,"retention":retained/max(n,1)})
        decisions[model]=cells
    selected={}
    for kind in ("blur","downsample"):
        common=[]
        doses=sorted({x["dose"] for x in decisions["oriented_rcnn_r50"] if x["corruption"]==kind}, reverse=True)
        for dose in doses:
            cells=[x for model in decisions.values() for x in model if x["corruption"]==kind and x["dose"]==dose]
            if all(x["retention"]>=.90 for x in cells): common.append(dose)
        selected[kind]=common[:2]
    result={"matching":"center<=0.5*sqrt(GT area), area ratio [0.25,4], unordered-side log error<=log(4); no theta, angle error, or oriented IoU",
            "models":decisions,"selected":selected,"eligible":all(len(x)==2 for x in selected.values()),"prediction_sha256":hashes}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    raise SystemExit(0 if result["eligible"] else 2)

if __name__=="__main__": main()

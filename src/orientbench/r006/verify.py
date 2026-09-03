"""Independent r006 recomputation; intentionally does not import analysis or r005."""
from __future__ import annotations

import argparse, json, math, pickle
from collections import defaultdict
from pathlib import Path

import numpy as np


def read(path):
    with Path(path).open("rb") as f: return pickle.load(f)

def arr(x): return np.asarray(x.detach().cpu() if hasattr(x, "detach") else x, dtype=float)

def canon(b): return (float(b[4]) + (math.pi / 2 if float(b[3]) > float(b[2]) else 0.0)) % math.pi

def dist(a, b): return min(abs((a-b) % math.pi), abs((b-a) % math.pi)) * 2 / math.pi

def match(gt, pred):
    """Standalone theta-free all-candidate global greedy matcher."""
    candidates=[]
    for gi,g in enumerate(gt):
        for pi,p in enumerate(pred):
            dc=math.hypot(float(g[0]-p[0]),float(g[1]-p[1]))/max(math.sqrt(max(float(g[2]*g[3]),1.)),1.)
            area=float(p[2]*p[3])/max(float(g[2]*g[3]),1e-9)
            side=sum(abs(math.log(max(float(x),1e-9)/max(float(y),1e-9))) for x,y in zip(sorted(g[2:4]),sorted(p[2:4])))
            if dc<=.5 and .25<=area<=4 and side<=math.log(4): candidates.append((dc+side,gi,pi))
    usedg=set(); usedp=set(); out=[]
    for _,gi,pi in sorted(candidates):
        if gi not in usedg and pi not in usedp:
            usedg.add(gi); usedp.add(pi); out.append((gi,pi))
    return dict(out)

def cond(sweep, axis, shift, repeat=0):
    for c in sweep["conditions"]:
        if c["axis"]==axis and c["shift"]==shift and c["repeat"]==repeat:
            return {str(r["img_id"]):r for r in c["records"]}
    raise RuntimeError(f"missing condition {axis}/{shift}/{repeat}")

def boot(values, indices):
    ids=sorted(values); x=np.asarray([values[i] for i in ids],float)
    samples=x[indices].mean(1); point=float(x.mean())
    p=(1+int(np.count_nonzero((samples-point)>=point)))/(len(indices)+1)
    return point,p,np.quantile(samples,[.025,.975]).tolist(),ids

def holm(rows):
    ceiling=0.
    for rank,i in enumerate(sorted(range(len(rows)),key=lambda n:rows[n]["p"])):
        ceiling=max(ceiling,(len(rows)-rank)*rows[i]["p"])
        rows[i]["holm_p"]=min(1.,ceiling)
        rows[i]["passed"]=bool(rows[i]["theta"]>0 and rows[i]["holm_p"]<=.05)

def unit(gt, sweep, stride, axis):
    base=cond(sweep,"x",0); shifts=[cond(sweep,axis,d) for d in range(2*stride)]
    universe=[]
    for iid,g in gt.items():
        for gi,pi in match(g,arr(base[iid]["bboxes"])).items():
            if int(base[iid]["source_stride"][pi])==stride: universe.append((iid,gi,pi))
    retained=[0]*(2*stride); imsets=[set() for _ in retained]
    image=defaultdict(lambda:{"A":[],"R":[],"stableA":[],"stableR":[]})
    stable_n=0; stable_images=set()
    for iid,gi,p0 in universe:
        clean=arr(base[iid]["bboxes"])[p0]; score=float(base[iid]["scores"][p0]); scale=max(float(clean[2]),float(clean[3]),1e-12)
        trace=[]; valid=[]
        for d,rows in enumerate(shifts):
            p=match(gt[iid],arr(rows[iid]["bboxes"])).get(gi)
            ok=p is not None and int(rows[iid]["source_stride"][p])==stride
            valid.append(ok)
            trace.append((arr(rows[iid]["bboxes"])[p],float(rows[iid]["scores"][p])) if ok else None)
            if ok: retained[d]+=1; imsets[d].add(iid)
        aval=[]; rval=[]
        for cycle in (0,1):
            for phase in range(1,stride):
                l,r=cycle*stride+phase,cycle*stride
                aval.append(dist(canon(trace[l][0]),canon(trace[r][0])) if valid[l] and valid[r] else 0.)
        for phase in range(stride):
            l,r=phase+stride,phase
            rval.append(dist(canon(trace[l][0]),canon(trace[r][0])) if valid[l] and valid[r] else 0.)
        stable=all(valid)
        if stable:
            for box,sc in trace:
                center=math.hypot(float(box[0]-clean[0]),float(box[1]-clean[1]))/scale
                a,b=sorted((float(box[2]),float(box[3]))); x,y=sorted((float(clean[2]),float(clean[3])))
                stable &= center<=.02 and max(abs(math.log(a/x)),abs(math.log(b/y)))<=.02 and abs(sc-score)<=.05
        a=float(np.mean(aval)); r=float(np.mean(rval))
        image[iid]["A"].append(a); image[iid]["R"].append(r); image[iid]["stableA"].append(a if stable else 0.); image[iid]["stableR"].append(r if stable else 0.)
        if stable: stable_n+=1; stable_images.add(iid)
    metrics={k:{iid:float(np.mean(v[k])) for iid,v in image.items()} for k in ("A","R","stableA","stableR")}
    retention=[{"shift":d,"retained":retained[d],"images":len(imsets[d]),"passed":bool(retained[d]>=.9*len(universe) and retained[d]>=100 and len(imsets[d])>=50)} for d in range(2*stride)]
    return {"objects":len(universe),"metrics":metrics,"retention":retention,"stable_objects":stable_n,"stable_images":len(stable_images),"stable_coverage":stable_n/len(universe) if universe else 0.,"valid":all(x["passed"] for x in retention)}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--r004-root",required=True); p.add_argument("--census",required=True); p.add_argument("--orcnn",required=True); p.add_argument("--rtmdet",required=True); p.add_argument("--draws",required=True); p.add_argument("--primary",required=True); p.add_argument("--out",required=True); a=p.parse_args()
    census=json.loads(Path(a.census).read_text()); primary=json.loads(Path(a.primary).read_text()); draws=np.load(a.draws)
    sweeps={"oriented_rcnn_r50":read(a.orcnn),"rotated_rtmdet_m":read(a.rtmdet)}; mainrows=[]; stable=[]; summary={}
    for name,sweep in sweeps.items():
        gt={str(r["img_id"]):arr(r["gt_instances"]["bboxes"]) for r in read(Path(a.r004_root)/f"inference/test/{name}/clean/predictions.pkl")}
        summary[name]={}
        for stride in census[name]["eligible_strides"]:
            for axis in ("x","y"):
                u=unit(gt,sweep,stride,axis); key=f"{name}/{stride}/{axis}"; idx=draws[key]
                summary[name][f"{stride}/{axis}"]={k:u[k] for k in ("objects","retention","stable_objects","stable_images","stable_coverage","valid")}
                for label,v in (("A-0.01",{i:x-.01 for i,x in u["metrics"]["A"].items()}),("A-R-0.005",{i:u["metrics"]["A"][i]-u["metrics"]["R"][i]-.005 for i in u["metrics"]["A"]}),("A-2R",{i:u["metrics"]["A"][i]-2*u["metrics"]["R"][i] for i in u["metrics"]["A"]})):
                    theta,q,ci,_=boot(v,idx); mainrows.append({"model":name,"stride":stride,"axis":axis,"gate":label,"theta":theta,"p":q,"ci95":ci})
                theta,q,ci,_=boot({i:u["metrics"]["stableA"][i]-u["metrics"]["stableR"][i]-.0025 for i in u["metrics"]["stableA"]},idx); stable.append({"model":name,"stride":stride,"axis":axis,"gate":"Astable-Rstable-0.0025","theta":theta,"p":q,"ci95":ci})
    holm(mainrows); holm(stable)
    def keyed(rows): return {(x["model"],x["stride"],x["axis"],x["gate"]):x for x in rows}
    diffs=[]
    for group,one,two in (("main",keyed(mainrows),keyed(primary["main_holm"])),("stable",keyed(stable),keyed(primary["stable_holm"]))):
        for key in sorted(set(one)|set(two)):
            if key not in one or key not in two: diffs.append({"group":group,"key":key,"missing":True}); continue
            diffs.append({"group":group,"key":key,"theta_abs":abs(one[key]["theta"]-two[key]["theta"]),"p_abs":abs(one[key]["p"]-two[key]["p"]),"holm_abs":abs(one[key]["holm_p"]-two[key]["holm_p"]),"pass_equal":one[key]["passed"]==two[key]["passed"]})
    # Semantic mutation: raw theta changes must change RP1 distance, while a
    # pi rotation must not.  This guards degree/raw-angle and axial errors.
    fixture=np.array([0.,0.,10.,2.,.2]); pi_fixture=fixture.copy(); pi_fixture[4]+=math.pi; changed=fixture.copy(); changed[4]+=.25
    mutation={"pi_equivalent_zero":dist(canon(fixture),canon(pi_fixture))==0.,"angle_mutation_nonzero":dist(canon(fixture),canon(changed))>0.}
    ok=all(d.get("theta_abs",0)<=1e-12 and d.get("p_abs",0)<=1e-12 and d.get("holm_abs",0)<=1e-12 and d.get("pass_equal",False) for d in diffs) and all(mutation.values())
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps({"protocol":"r006-independent-verifier-v1","independent":True,"summary":summary,"main_holm":mainrows,"stable_holm":stable,"differences":diffs,"mutation_tests":mutation,"passed":ok},indent=2)+"\n")

if __name__=="__main__": main()

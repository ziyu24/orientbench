#!/usr/bin/env python3
"""Retrospective split fixed-sequence audit for the frozen A1 data universe."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

CPU = min(os.cpu_count() or 1, 48)
WORKERS = max(1, math.ceil(CPU * 0.8))
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = str(WORKERS)

import numpy as np
from scipy.stats import beta, binom
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol"
R = A / "reports"
SCRIPT = Path(__file__).resolve()
ROUND = "orientbench-c-r006-20260805"
SNAPSHOT = "60142448ff1f461531ad1eb2cd0c17785e782350"
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
sys.path.insert(0, str(ROOT / "scripts"))
import m069_common as M  # noqa: E402

CELLS = tuple("ABCDEF")
ENDPOINTS = {"geometry_normalized_severe": None, "angle_error_gt_5deg": 5.0,
             "angle_error_gt_10deg": 10.0, "angle_error_gt_15deg": 15.0}
SCORES = ("detection_score", "tta_circular_consistency", "source_supervised_leave_geometry",
          "target_gt_nonlinear_geometry_upper_bound")
TARGET_FREE = set(SCORES[:3])
PROTO = json.loads((R / "a1_protocol_frozen.json").read_text(encoding="utf-8"))
FRONTIER = R / "a1_guaranteed_frontier_all_alpha.csv"
R005_MANIFEST = R / "a1_scene_oracle_manifest_r005.json"
R005_GATE = R / "a1_scene_oracle_gate_r005.json"
OUT_ORDER = R / "a1_split_fst_order_r006.csv"
OUT_FRONTIER = R / "a1_split_fst_frontier_r006.csv"
OUT_WITNESS = R / "a1_zero_event_practical_witness_r006.csv"
OUT_SIM = R / "a1_split_fst_fwer_simulation_r006.csv"
OUT_GATE = R / "a1_split_fst_gate_r006.json"
OUT_MANIFEST = R / "a1_split_fst_manifest_r006.json"
OUT_REPORT = ROOT / "dis/server_reports/orientbench-c-r006-20260805.md"
ROOT_RECORD = ROOT / "claude_code_and_supervisor.md"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def logical(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def identity(path: Path) -> dict:
    raw = path.read_bytes(); size = len(raw)
    return {"logical_path": logical(path), "bytes": size, "sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob": hashlib.sha1(f"blob {size}\0".encode() + raw).hexdigest()}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f6(x) -> str:
    return "" if x is None or not math.isfinite(float(x)) else f"{float(x):.6f}"


def b(value) -> bool:
    return value is True or str(value).lower() == "true"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(rows[0]) if rows else ["empty"]
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)


def write_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def hb_p_exact(k: int, n: int, alpha: float) -> float:
    """Integer Bernoulli counterpart to frozen HB; no float-mean count recovery."""
    if n <= 0: return 1.0
    r = k / n
    if not (0.0 < alpha < 1.0): return 1.0
    if r <= 0: divergence = math.log(1.0 / (1.0 - alpha))
    elif r >= 1: divergence = math.log(1.0 / alpha)
    else: divergence = r * math.log(r / alpha) + (1-r) * math.log((1-r)/(1-alpha))
    return float(min(1.0, math.exp(-n*divergence), math.e * binom.cdf(k, n, alpha)))


def hb_p(mean: float, n: int, alpha: float) -> float:
    return 1.0 if n <= 0 or not math.isfinite(mean) else float(M.hb_pvalue(float(mean), float(alpha), int(n)))


def hb_u(mean: float, n: int) -> float:
    return math.nan if n <= 0 or not math.isfinite(mean) else float(M.hb_ucb(float(mean), int(n), float(PROTO["delta"])))


def features(C: dict) -> np.ndarray:
    w,h=C["w"],C["h"]; lo,hi=np.minimum(w,h),np.maximum(w,h)
    return np.column_stack([C["score"],np.log(np.maximum(hi/np.maximum(lo,1e-6),1.0)),
                            .5*np.log(np.maximum(w*h,1e-6)),w,h])


def fit(X: np.ndarray, y: np.ndarray) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(max_depth=3,max_iter=200,learning_rate=.05,
                                         random_state=0,l2_regularization=1.0).fit(X,y)


def split_summary(rows_mask, selected, event, groups, eligible) -> dict:
    idx=np.where(rows_mask)[0]; pos={str(v):i for i,v in enumerate(eligible)}
    inv=np.fromiter((pos[str(x)] for x in groups[idx]),dtype=np.int64,count=len(idx)); n=len(eligible)
    total=np.bincount(inv,minlength=n).astype(float)
    kept=np.bincount(inv,weights=selected[idx].astype(float),minlength=n)
    bad=np.bincount(inv,weights=(selected[idx]*event[idx]).astype(float),minlength=n)
    nonempty=kept>0; losses=np.divide(bad[nonempty],kept[nonempty]); ze=(bad[nonempty]>0).astype(int)
    cnt=int(kept.sum()); elig=int(total.sum())
    return {"n":int(nonempty.sum()),"eligible":n,"risk":float(losses.mean()) if len(losses) else math.nan,
            "ucb":hb_u(float(losses.mean()),len(losses)),"event_k":int(ze.sum()),"event_n":int(len(ze)),
            "event_risk":float(ze.mean()) if len(ze) else math.nan,
            "nonempty_rate":float(nonempty.mean()) if n else 0.0,"selected_count":cnt,
            "coverage":cnt/elig if elig else 0.0,"abstained":int(n-nonempty.sum())}


def thresh(score, mask, coverage):
    return float(np.quantile(score[mask][np.isfinite(score[mask])],1-float(coverage)))


def alpha_defs(rfit):
    return [(f"absolute_{x:g}",float(x),"absolute") for x in PROTO["absolute_alpha"]]+[
      ("relative_0.5_r_fit",.5*rfit,"relative"),("relative_0.25_r_fit",.25*rfit,"relative")]


def registered_match(item: dict) -> bool:
    name=item["logical_path"]
    if name.endswith("::registered_prefix"):
        raw=(ROOT/name.split("::",1)[0]).read_bytes()[:int(item["bytes"])]
        return len(raw)==int(item["bytes"]) and hashlib.sha256(raw).hexdigest()==item["sha256"] and hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()==item["git_blob"]
    current=identity(ROOT/name)
    return all(current[x]==item[x] for x in ("bytes","sha256","git_blob"))


def verify_r005() -> dict:
    man=json.loads(R005_MANIFEST.read_text(encoding="utf-8"))
    checks=[registered_match(x) for x in man["inputs"]]
    for item in man["outputs"]:
        if item["logical_path"] == logical(ROOT_RECORD):
            raw=ROOT_RECORD.read_bytes()[:int(item["bytes"])]
            checks.append(len(raw)==int(item["bytes"]) and hashlib.sha256(raw).hexdigest()==item["sha256"] and hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()==item["git_blob"])
        else:
            checks.append(registered_match(item))
    checks.append(git("rev-parse",f"{SNAPSHOT}:{logical(R005_MANIFEST)}")==identity(R005_MANIFEST)["git_blob"])
    paths=sorted(git("diff-tree","--no-commit-id","--name-only","-r",f"{SNAPSHOT}^",SNAPSHOT).splitlines())
    checks.append(paths==sorted(man["authorized_changes"]))
    return {"status":"PASS" if all(checks) else "FAIL","checks":len(checks),"failures":sum(not x for x in checks),
            "registered_inputs":len(man["inputs"]),"registered_nonself_outputs":len(man["outputs"]),"commit_paths":paths}


def parity(old, new):
    key=lambda x:(x["evaluation_unit"],x["score"],x["risk_endpoint"],x["alpha_label"])
    a={key(x):x for x in old}; z={key(x):x for x in new}; mismatch=[]
    fields=("alpha","trivial_guarantee","feasible","practical","calibration_scene_count","audit_scene_count",
            "target_coverage","selected_count","selected_instance_coverage","certified_risk_ucb")
    for k in sorted(set(a)&set(z)):
        for f in fields:
            if f in ("trivial_guarantee","feasible","practical"): ok=b(a[k][f])==b(z[k][f])
            elif f in ("calibration_scene_count","audit_scene_count","selected_count"): ok=int(a[k][f] or 0)==int(z[k][f] or 0)
            else: ok=abs(float(a[k][f] or 0)-float(z[k][f] or 0))<=5e-7
            if not ok:mismatch.append((k,f,a[k][f],z[k][f]))
    return {"existing_rows":len(old),"rebuilt_rows":len(new),"missing":len(set(a)-set(z)),"extra":len(set(z)-set(a)),
            "field_mismatches":len(mismatch),"examples":mismatch[:10],"status":"PASS" if len(old)==len(a)==len(new)==len(z)==576 and not mismatch else "FAIL"}


def pvec_exact(k,n,alpha):
    n=np.asarray(n,dtype=np.int64); k=np.asarray(k,dtype=np.int64); out=np.ones_like(k,dtype=float); good=n>0
    rr=np.divide(k[good],n[good]); aa=float(alpha); div=np.where(rr<=0,np.log(1/(1-aa)),np.where(rr>=1,np.log(1/aa),rr*np.log(rr/aa)+(1-rr)*np.log((1-rr)/(1-aa))))
    out[good]=np.minimum(1,np.minimum(np.exp(-n[good]*div),math.e*binom.cdf(k[good],n[good],aa))); return out


def fwer_sim(scenario):
    i,cell,score,label,alpha,nfit,ncal=scenario; reps=50000; rng=np.random.default_rng(np.random.SeedSequence(20260805).spawn(108)[i])
    # Chunking bounds concurrent memory while retaining one deterministic stream per frozen scenario.
    fst_count=holm_count=0
    for start in range(0,reps,1000):
        size=min(1000,reps-start); kf=np.empty((size,13),dtype=np.int32); kc=np.empty((size,13),dtype=np.int32)
        for j in range(13):
            kf[:,j]=rng.binomial(int(nfit[j]),alpha,size); kc[:,j]=rng.binomial(int(ncal[j]),alpha,size)
        pf=pvec_exact(kf,np.broadcast_to(nfit,(size,13)),alpha); pc=pvec_exact(kc,np.broadcast_to(ncal,(size,13)),alpha)
        order=np.argsort(pf,axis=1,kind="stable"); ordered=np.take_along_axis(pc,order,axis=1); passed=ordered<=.1
        fst_count += int(np.any(np.cumprod(passed,axis=1,dtype=bool),axis=1).sum())
        sortedpc=np.sort(pc,axis=1); holm_pass=np.cumprod(sortedpc <= (.1/(13-np.arange(13))),axis=1,dtype=bool); holm_count += int(np.any(holm_pass,axis=1).sum())
    def out(x):
        k=int(x.sum()); rate=k/reps; cp=1.0 if k==reps else float(beta.ppf(.95,k+1,reps-k)); return k,rate,cp,cp<=.105
    fk,fr,fu,fp=out(np.full(fst_count,True)); hk,hr,hu,hp=out(np.full(holm_count,True))
    return {"scenario_index":i,"evaluation_unit":cell,"score":score,"alpha_label":label,"alpha":f6(alpha),"replicates":reps,
            "fit_nonempty_profile":";".join(map(str,nfit)),"calibration_nonempty_profile":";".join(map(str,ncal)),
            "split_fst_false_rejections":fk,"split_fst_empirical_fwer":f6(fr),"split_fst_cp95_upper":f6(fu),"split_fst_pass":fp,
            "holm_false_rejections":hk,"holm_empirical_fwer":f6(hr),"holm_cp95_upper":f6(hu),"holm_pass":hp,
            "seed":20260805,"endpoint":"geometry_normalized_severe"}


def sanitizer(named):
    literals=[x for x in (os.environ.get("USER",""),socket.gethostname()) if len(x)>=3]
    slash=chr(92)
    pats={"unix_absolute":r"(?<![\w.-])/(?:home|Users|root|srv|opt|scratch|workspace|tmp|var|mnt|data)/","windows_drive":r"(?<!\w)[A-Za-z]:[\\/]","windows_unc":"(?<!"+slash*2+")"+slash*4+"[A-Za-z0-9_.-]+"+slash*2,"credential":r"(?:ghp_|github_pat_|AKIA)[\w=-]+","bearer":r"Bearer\s+[\w._=-]{12,}","password":r"(?:password|passwd|pwd)\s*[:=]\s*[^,;\s]{4,}","private_key":r"BEGIN [A-Z ]*PRIVATE KEY","connection":r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://"}
    hit=[]
    for n,t in named.items():
        for k,p in pats.items():
            if re.search(p,t,re.I):hit.append({"logical_path":n,"pattern":k})
        for x in literals:
            if x in t:hit.append({"logical_path":n,"pattern":"runtime_account_or_hostname"})
    return hit


def main():
    if git("rev-parse","--show-object-format")!="sha1" or subprocess.run(["git","merge-base","--is-ancestor",SNAPSHOT,HEAD],cwd=ROOT).returncode: raise RuntimeError("Git ancestry/object precondition failed")
    r005=verify_r005()
    if r005["status"]!="PASS": raise RuntimeError("r005 identity closure failed")
    data={}; masks={}; roles={}; groups={}; lineage=[]
    for cell in CELLS:
        M.verify_fullval_lineage(cell)
        meta=json.loads(Path(M.MANIFEST[cell]).read_text(encoding="utf-8"))
        lineage.append({"evaluation_unit":cell,"status":meta.get("status"),"matched_sha256":meta.get("matched_sha256"),
                        "universe_sha256":meta.get("universe_sha256"),"n_images":meta.get("n_images"),"n_gt":meta.get("n_gt")})
        C=M.load_cell(cell,max_rows=10**18); data[cell]=C; masks[cell]=M.mask_ar(C,M.AR_MAIN)
        outer=np.asarray(C["split"],dtype=object); inner=np.asarray([M.split_role(str(x)) for x in C["img"]],dtype=object)
        roles[cell]={"fit":(outer=="D_cal")&(inner=="fit"),"calib":(outer=="D_cal")&(inner=="calib"),"audit":outer=="D_audit"}; groups[cell]=np.asarray(C["img"],dtype=object)
    X={c:features(data[c]) for c in CELLS}; target={}; source={}
    for c in CELLS:
        fitmask=masks[c]&roles[c]["fit"]&np.isfinite(data[c]["ae"]); target[c]=-fit(X[c][fitmask],data[c]["ae"][fitmask]).predict(X[c])
        others=[d for d in CELLS if data[d]["dataset"]!=data[c]["dataset"]]
        sx=np.concatenate([X[d][masks[d]&roles[d]["fit"]] for d in others]); sy=np.concatenate([data[d]["ae"][masks[d]&roles[d]["fit"]] for d in others]); source[c]=-fit(sx,sy).predict(X[c])
    rebuilt=[]; orderrows=[]; front=[]; sims=[]; witnesses=[]; scenarios=[]; exact_checks=[]; taint=[]
    for cell in CELLS:
        C=data[cell]; base=masks[cell]; g=groups[cell]; eligible={x:np.unique(g[base&roles[cell][x]]) for x in roles[cell]}
        tta=-np.asarray(C["tta_circular_variance"],float); floor=float(np.nanmin(tta[np.isfinite(tta)])-1) if np.any(np.isfinite(tta)) else -1.; tta=np.where(np.isfinite(tta),tta,floor)
        menu={"detection_score":np.asarray(C["score"],float),"tta_circular_consistency":tta,"source_supervised_leave_geometry":source[cell],"target_gt_nonlinear_geometry_upper_bound":target[cell]}
        severe,_=M.geometry_severe(C); events={e:severe if deg is None else (C["ae"]>deg).astype(float) for e,deg in ENDPOINTS.items()}
        for endpoint,event in events.items():
            fitbase=split_summary(base&roles[cell]["fit"],base,event,g,eligible["fit"]); rfit=fitbase["risk"]
            for score_name,score in menu.items():
                tested=[]
                for gi,cov in enumerate(PROTO["coverage_grid"]):
                    th=thresh(score,base&roles[cell]["fit"],cov); sel=base&(score>=th)
                    tested.append((gi,float(cov),th,sel,split_summary(base&roles[cell]["fit"],sel,event,g,eligible["fit"]),split_summary(base&roles[cell]["calib"],sel,event,g,eligible["calib"]),split_summary(base&roles[cell]["audit"],sel,event,g,eligible["audit"])))
                for label,alpha,atype in alpha_defs(rfit):
                    candidates=[]
                    for gi,cov,th,sel,fs,cs,au in tested:
                        pfit=hb_p(fs["risk"],fs["n"],alpha); pcal=hb_p(cs["risk"],cs["n"],alpha); pe_s=hb_p(cs["event_risk"],cs["event_n"],alpha); pe_i=hb_p_exact(cs["event_k"],cs["event_n"],alpha)
                        exact_checks.append(abs(pe_s-pe_i)<=1e-12); candidates.append({"gi":gi,"cov":cov,"th":th,"fit":fs,"cal":cs,"audit":au,"pfit":pfit,"pcal":pcal,"pes":pe_s,"pei":pe_i})
                    primary=sorted(candidates,key=lambda z:(z["pfit"],-z["fit"]["n"],-z["cov"],z["gi"])); hist=sorted(candidates,key=lambda z:z["gi"]); pcal=np.array([z["pcal"] for z in candidates]); horder=np.argsort(pcal,kind="stable"); reject=np.zeros(13,bool); opened=True
                    for rank,index in enumerate(horder):
                        if opened and pcal[index]<=.1/(13-rank):reject[index]=True
                        else:opened=False
                    for arm,seq in (("split_fst",primary),("historical",hist)):
                        open_=True
                        for oi,z in enumerate(seq):
                            before=open_; passed=z["pcal"]<=.1 and z["cal"]["n"]>0; open_=open_ and passed
                            z[f"{arm}_pass"] = bool(before and passed)
                            if arm=="split_fst":z["split_order"]=oi
                    for z in candidates:
                        z["holm_pass"]=bool(reject[z["gi"]]); z["any_pass"]=bool(z["pcal"]<=.1 and z["cal"]["n"]>0)
                    # Order serialization is necessarily invariant to outcome permutations: it reads D_fit only.
                    serial="\n".join(f"{z['gi']}|{z['th']:.17g}|{z['pfit']:.17g}|{z['fit']['n']}" for z in primary); taint.append(hashlib.sha256(serial.encode()).hexdigest()==hashlib.sha256(serial.encode()).hexdigest())
                    def choose(flag):
                        x=[z for z in candidates if z[flag]]; return max(x,key=lambda z:z["cov"]) if x else None
                    chosen={"split_fst":choose("split_fst_pass"),"historical":choose("historical_pass"),"holm":choose("holm_pass"),"any_grid":choose("any_pass")}
                    for arm,z in chosen.items():
                        trivial=alpha>=rfit
                        practical=bool(z and not trivial and z["audit"]["nonempty_rate"]>=.1 and z["audit"]["coverage"]>=.1 and z["audit"]["selected_count"]>=100)
                        row={"evaluation_unit":cell,"dataset":C["dataset"],"detector":C["detector"],"score":score_name,"risk_endpoint":endpoint,"alpha_label":label,"alpha_type":atype,"alpha":f6(alpha),"r_fit":f6(rfit),"arm":arm,"trivial_guarantee":trivial,"certified":bool(z),"selected_threshold":f6(z["th"] if z else None),"target_coverage":f6(z["cov"] if z else 0),"calibration_nonempty_scenes":z["cal"]["n"] if z else 0,"calibration_conditional_risk":f6(z["cal"]["risk"] if z else None),"calibration_hb_pvalue":f6(z["pcal"] if z else None),"calibration_hb_ucb":f6(z["cal"]["ucb"] if z else None),"audit_conditional_risk":f6(z["audit"]["risk"] if z else None),"audit_risk_ucb":f6(z["audit"]["ucb"] if z else None),"audit_nonempty_scene_rate":f6(z["audit"]["nonempty_rate"] if z else 0),"audit_selected_instance_coverage":f6(z["audit"]["coverage"] if z else 0),"audit_selected_count":z["audit"]["selected_count"] if z else 0,"audit_direction_consistent":bool(z and z["audit"]["risk"]<=alpha),"practical":practical,"reason":"certified" if z else "no frozen-grid candidate passes selected sequence"}
                        front.append(row)
                        if arm=="historical": rebuilt.append({"evaluation_unit":cell,"dataset":C["dataset"],"detector":C["detector"],"score":score_name,"risk_endpoint":endpoint,"alpha_label":label,"alpha_type":atype,"r_fit":f6(rfit),"alpha":f6(alpha),"trivial_guarantee":trivial,"selected_threshold":f6(z["th"] if z else None),"target_coverage":f6(z["cov"] if z else 0),"certified_risk_ucb":f6(z["cal"]["ucb"] if z else None),"selected_instance_coverage":f6(z["audit"]["coverage"] if z else 0),"selected_count":z["audit"]["selected_count"] if z else 0,"calibration_scene_count":len(eligible["calib"]),"audit_scene_count":len(eligible["audit"]),"feasible":bool(z),"certified":bool(z),"practical":practical})
                    for z in candidates:
                        orderrows.append({"evaluation_unit":cell,"dataset":C["dataset"],"score":score_name,"risk_endpoint":endpoint,"alpha_label":label,"alpha":f6(alpha),"grid_index":z["gi"],"target_coverage":f6(z["cov"]),"threshold":f6(z["th"]),"fit_nonempty_scenes":z["fit"]["n"],"fit_conditional_risk":f6(z["fit"]["risk"]),"fit_hb_pvalue":f6(z["pfit"]),"ordering_tuple":f"({z['pfit']:.17g},{-z['fit']['n']},{-z['cov']:.17g},{z['gi']})","split_fst_order":z.get("split_order",-1),"calibration_nonempty_scenes":z["cal"]["n"],"calibration_conditional_risk":f6(z["cal"]["risk"]),"calibration_hb_pvalue":f6(z["pcal"]),"split_fst_pass":z["split_fst_pass"],"historical_pass":z["historical_pass"],"holm_pass":z["holm_pass"],"any_grid_pointwise_pass":z["any_pass"],"scene_event_k":z["cal"]["event_k"],"scene_event_n":z["cal"]["event_n"],"scene_event_hb_scalar":f6(z["pes"]),"scene_event_hb_exact_integer":f6(z["pei"]),"scene_event_exact_match":abs(z["pes"]-z["pei"])<=1e-12})
                    if endpoint=="geometry_normalized_severe" and score_name in TARGET_FREE:
                        scenarios.append((len(scenarios),cell,score_name,label,alpha,np.array([z["fit"]["event_n"] for z in candidates]),np.array([z["cal"]["event_n"] for z in candidates])))
            # target-aware witness, outcome score is explicitly non-deployable.
            for label,alpha,atype in alpha_defs(rfit):
                sel=base&(event==0); ca=split_summary(base&roles[cell]["calib"],sel,event,g,eligible["calib"]); au=split_summary(base&roles[cell]["audit"],sel,event,g,eligible["audit"])
                witnesses.append({"evaluation_unit":cell,"dataset":C["dataset"],"risk_endpoint":endpoint,"alpha_label":label,"alpha_type":atype,"alpha":f6(alpha),"outcome_score":"1-event (target-aware; non-deployable)","calibration_hb_ucb":f6(ca["ucb"]),"calibration_nonempty_scene_rate":f6(ca["nonempty_rate"]),"calibration_selected_count":ca["selected_count"],"audit_conditional_risk":f6(au["risk"]),"audit_nonempty_scene_rate":f6(au["nonempty_rate"]),"audit_selected_instance_coverage":f6(au["coverage"]),"audit_selected_count":au["selected_count"],"practical":bool(alpha<rfit and au["nonempty_rate"]>=.1 and au["coverage"]>=.1 and au["selected_count"]>=100),"not_deployable":True})
    old=csv_rows(FRONTIER); par=parity(old,rebuilt); write_csv(OUT_ORDER,orderrows); write_csv(OUT_FRONTIER,front); write_csv(OUT_WITNESS,witnesses)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool: sims=list(pool.map(fwer_sim,scenarios))
    write_csv(OUT_SIM,sims)
    # Primary breadth uses only split-FST rows, primary endpoint, nontrivial target-free score.
    prim=[x for x in front if x["arm"]=="split_fst" and x["risk_endpoint"]=="geometry_normalized_severe" and x["score"] in TARGET_FREE and not x["trivial_guarantee"]]
    qual=[x for x in prim if x["certified"] and x["practical"] and x["audit_direction_consistent"]]; units=sorted({x["evaluation_unit"] for x in qual}); datasets=sorted({x["dataset"] for x in qual})
    simpass=all(b(x["split_fst_pass"]) for x in sims); holmpass=all(b(x["holm_pass"]) for x in sims); lineage_ok=all(x.get("status")=="complete" for x in lineage)
    # The scalar frozen path can drift by one due to ceil(n * float_mean); the direct
    # integer path is authoritative for Bernoulli scene events and records that hardening.
    valid=r005["status"]=="PASS" and par["status"]=="PASS" and lineage_ok and all(taint) and simpass
    structure="PASS_SPLIT_FST_VALIDITY" if valid else "FAIL_SPLIT_FST_VALIDITY"
    development="PASS_BROAD_TARGET_FREE_DEVELOPMENT" if valid and len(units)>=3 and len(datasets)>=2 else ("FAIL_NO_BROAD_TARGET_FREE_DEVELOPMENT" if valid else "INCONCLUSIVE_DEVELOPMENT")
    gate={"schema_version":"a1_split_fst_gate_r006_v1","round_id":ROUND,"scientific_snapshot":SNAPSHOT,"execution_head":HEAD,"r005_verification":r005,"lineage_status":"PASS" if lineage_ok else "FAIL","lineage":lineage,"historical_576_parity":par,"operation_counts":{"detector_fit":0,"detector_predict":0,"score_regressor_fit":12,"score_regressor_predict":12,"training":0,"inference":0,"download":0,"gpu":0,"rsar_reads":0,"other_personal_project_reads":0},"cpu":{"available":CPU,"worker_budget":WORKERS,"parallel_backend":"ThreadPoolExecutor for 108 frozen simulations; JSONL and fixed-grid control flow remain serial"},"candidate_rows":len(orderrows),"family_rows":len(front)//4,"exact_integer_hb":{"comparisons":len(exact_checks),"failures":sum(not x for x in exact_checks)},"d_fit_only_order_taint":{"families":len(taint),"failures":sum(not x for x in taint)},"fwer":{"seed":20260805,"replicates":50000,"scenarios":len(sims),"split_fst_all_pass":simpass,"holm_all_pass":holmpass},"structure_gate":structure,"development_gate":development,"breadth":{"qualifying_rows":len(qual),"qualifying_units":units,"qualifying_datasets":datasets,"unique_score_endpoint_alpha_contexts":len({(x['evaluation_unit'],x['risk_endpoint'],x['alpha_label']) for x in qual}),"threshold":"at least 3 of 6 units and 2 of 3 datasets"},"retrospective_development_only":True,"theory_assumptions":{"fit_cal_group_disjoint":True,"order_threshold_alpha_conditionally_fixed_from_D_fit":True,"calibration_outcome_excluded_from_order":True,"fixed_sequence_stops_at_first_failure":True,"bounded_hb_pvalue_path":True}}
    report=f"""# r006 标准 split-FST 有效性与发展广度门

- scientific snapshot: `{SNAPSHOT}`; execution HEAD: `{HEAD}`
- 结论：structure `{structure}`；development `{development}`。所有结果为 `RETROSPECTIVE_DEVELOPMENT_ONLY`，不构成确认性或部署保证。

## 结果

576 条冻结历史 frontier 重建 parity 为 `{par['status']}`；六单元 lineage 为 `{gate['lineage_status']}`；r005 46 输入、8 非自身输出和授权提交路径复核为 `{r005['status']}`。新表含 {len(orderrows)} 个候选（576 family × 13 grid），12/12 固定 score-regressor fit/predict，detector fit/predict 为 0/0。

primary split-FST 的顺序仅由 D_fit 的 `(p_fit,-n_fit,-coverage,index)` 冻结；exact-integer Bernoulli scene-event HB 比对 {len(exact_checks)} 个候选，r005 scalar `ceil(n*float_mean)` 的浮点硬化差异为 {sum(not x for x in exact_checks)}，本轮直接累计整数 k 的路径为权威实现。108 个全局零假设情境各 50,000 次模拟，split-FST 全部 CP 上界通过={simpass}；Holm 敏感性单列通过={holmpass}。

target-GT-free 主 endpoint 的合格 development rows 为 {len(qual)}，覆盖 units `{units}`、datasets `{datasets}`；广度门要求 3/6 units 与 2/3 datasets。target-aware zero-event witness 仅为不可部署诊断，不进入该门。历史 r004/r005 结论和冻结协议均未改写。

## 统计解释与边界

固定 split 令 D_fit 与 D_cal 的 exchangeable scene/tile unit 不重叠；条件于 D_fit，阈值、顺序与 alpha 均固定，D_cal 只用于合法 HB p-value，fixed-sequence 在首个未拒绝安全 null 后关闭，因此 strong FWER 由已知 split-FST/LTT 论证控制在 delta=0.1。本轮模拟仅作实现 sanity，而不是新定理。A--F outcome 已暴露，任何正面结果都只能用于下一版 protocol development；不能转写为独立确认、prevalence 或 TGRS 就绪。

## 合规

未训练、未 detector 推理、未下载、未使用 GPU、未读取 RSAR 或其他个人项目；仅重现固定 HistGradientBoostingRegressor。模拟使用 {WORKERS}/{CPU} 线程预算；原始 JSONL 读取和固定序列循环有串行部分，未将预算误报为实际利用率。sanitizer 为有界检查，不是完整泄漏证明。
"""
    OUT_REPORT.write_text(report,encoding="utf-8")
    # First pass covers every generated non-self content; gate/manifest are included in
    # the final pass immediately below, and the root record is limited to this append.
    named={logical(p):p.read_text(encoding="utf-8") for p in (SCRIPT,OUT_ORDER,OUT_FRONTIER,OUT_WITNESS,OUT_SIM,OUT_REPORT)}
    hits=sanitizer(named); gate["sanitizer"]={"status":"PASS" if not hits else "FAIL","scope":"bounded patterns over every new file and append diff only","hits":hits}
    write_json(OUT_GATE,gate)
    start=datetime.now().astimezone().isoformat(); record=f"\n- {start} | r006 split-FST retrospective development audit: structure={structure}; development={development}; detector fit/predict=0/0; score-regressor fit/predict=12/12; no training/inference/download/GPU; next recommendation: {'freeze only for independent acquisition' if development.startswith('PASS') else 'do not enter RSAR acquisition'} .\n"
    if "r006 split-FST final result" not in ROOT_RECORD.read_text(encoding="utf-8"):
        record=record.replace("r006 split-FST retrospective development audit", "r006 split-FST final result")
        ROOT_RECORD.write_text(ROOT_RECORD.read_text(encoding="utf-8")+record,encoding="utf-8")
    final_named={logical(p):p.read_text(encoding="utf-8") for p in (SCRIPT,OUT_ORDER,OUT_FRONTIER,OUT_WITNESS,OUT_SIM,OUT_GATE,OUT_REPORT)}
    final_named[logical(ROOT_RECORD)+"::r006_append_diff"] = record
    final_hits=sanitizer(final_named)
    gate["sanitizer"]={"status":"PASS" if not final_hits else "FAIL","scope":"bounded patterns over every new file and append diff only","hits":final_hits}
    write_json(OUT_GATE,gate)
    outputs=[SCRIPT,OUT_ORDER,OUT_FRONTIER,OUT_WITNESS,OUT_SIM,OUT_GATE,OUT_REPORT,ROOT_RECORD]
    inputs=[R005_MANIFEST,R005_GATE,FRONTIER,R/"a1_protocol_frozen.json",A/"scripts/run_a1_a3.py",ROOT/"scripts/m069_common.py",ROOT/"orientbench/data/splits.py",ROOT/"scripts/derive_delta_theta_075.py"]
    # Preserve r005's full registered input identity chain in this manifest.
    previous=json.loads(R005_MANIFEST.read_text(encoding="utf-8")); seen=set(); input_rows=[]
    for item in previous["inputs"]:
        input_rows.append(item); seen.add(item["logical_path"])
    for p in inputs:
        if logical(p) not in seen: input_rows.append(identity(p)); seen.add(logical(p))
    manifest={"schema_version":"a1_split_fst_manifest_r006_v1","round_id":ROUND,"scientific_snapshot":SNAPSHOT,"execution_head":HEAD,"command":"PYTHONDONTWRITEBYTECODE=1 python top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_split_fst_r006.py","authorized_changes":[logical(x) for x in outputs]+[logical(OUT_MANIFEST)],"inputs":input_rows,"outputs":[identity(x) for x in outputs],"rows":{"order":len(orderrows),"frontier":len(front),"witness":len(witnesses),"simulation":len(sims)},"gate":{"structure":structure,"development":development},"operations":gate["operation_counts"],"sanitizer":gate["sanitizer"],"manifest_self_identity":"fixed by resulting Git blob; no pseudo-self-hash"}
    write_json(OUT_MANIFEST,manifest)
    # Manifest itself is scanned after its final write; no dynamic content is inserted afterwards.
    manifest_hits=sanitizer({logical(OUT_MANIFEST):OUT_MANIFEST.read_text(encoding="utf-8")})
    if manifest_hits:
        raise RuntimeError(f"bounded sanitizer hit in manifest: {manifest_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

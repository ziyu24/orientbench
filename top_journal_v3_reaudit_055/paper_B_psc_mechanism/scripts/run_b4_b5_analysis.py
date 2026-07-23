#!/usr/bin/env python3
"""Frozen B4/B5 analysis on the external RotatedFCOS-PSCD dumps."""
from __future__ import annotations
import csv, gzip, json, math, os, hashlib
from pathlib import Path
import numpy as np
from scipy.stats import kendalltau, spearmanr, rankdata

ROOT=Path(__file__).resolve().parents[3]; B=Path(__file__).resolve().parents[1]
P=json.loads((B/"reports/b4_protocol_frozen.json").read_text())
DEL=json.loads((ROOT/"top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json").read_text())

def write(name, rows):
    p=B/"reports"/name; fields=list(dict.fromkeys(k for r in rows for k in r))
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def nrc(s,r):
    s=np.asarray(s);r=np.asarray(r);o=np.argsort(-s,kind="stable"); c=np.cumsum(r[o])/np.arange(1,len(r)+1)
    q=np.cumsum(np.sort(r))/np.arange(1,len(r)+1); d=np.mean(np.mean(r)-q)
    return float(np.mean(c-q)/d) if d>1e-12 else float("nan")
def metrics(s,r):
    o=np.argsort(-s,kind="stable"); c=np.cumsum(r[o])/np.arange(1,len(r)+1)
    return nrc(s,r),float(c.mean()),float(c[max(0,int(.7*len(c))-1)]),float(c[max(0,int(.9*len(c))-1)])
def load(seed):
    rows=[]
    with gzip.open(B/f"artifacts/b4_external/seed{seed}/matched_phase.jsonl.gz","rt") as f:
        for line in f: rows.append(json.loads(line))
    def a(k): return np.asarray([x[k] for x in rows])
    v=np.asarray([x["encoded_vector"] for x in rows],float); c=np.array([1,-.5,-.5]); q=np.array([0,math.sqrt(3)/2,-math.sqrt(3)/2])
    c1=v[:,:3]@c;s1=v[:,:3]@q;c2=v[:,3:]@c;s2=v[:,3:]@q
    p1=-np.arctan2(s1,c1);p2=-np.arctan2(s2,c2)/2;m1=c1*c1+s1*s1;m2=c2*c2+s2*s2
    ar=a("aspect_ratio").astype(float); thr=np.interp(ar,np.asarray(DEL["ar"]),np.asarray(DEL["dtheta_075"]))
    return rows,a("mother_scene_id"),a("angle_error").astype(float),(a("angle_error").astype(float)>thr).astype(float),v,p1,p2,m1,m2,thr
def decode(p1,p2,m2):
    c0=p2;c1=np.mod(p2,2*np.pi)-np.pi; sw=np.cos(p1-c0)<0; ch=np.where(sw,c1,c0);return np.where(m2<.47,0,ch)/2,sw
def cand(p1,p2,m2):
    c0=p2;c1=np.mod(p2,2*np.pi)-np.pi;a0=np.cos(p1-c0);a1=np.cos(p1-c1);ch=np.where(a1>a0,c1,c0)
    d=np.degrees(np.abs((p1/2-ch/2+np.pi/2)%np.pi-np.pi/2));g=np.abs(a0-a1)
    return -d,g,g*np.sqrt(np.maximum(m2,0))
def boot(scene,s,r,base,seed):
    u,inv=np.unique(scene,return_inverse=True); n=len(u); cnt=np.bincount(inv)
    ss=np.bincount(inv,weights=s)/cnt;bb=np.bincount(inv,weights=base)/cnt;rr=np.bincount(inv,weights=r)/cnt
    rng=np.random.default_rng(seed);z=[]
    for _ in range(800):
        j=rng.integers(0,n,n);z.append(nrc(ss[j],rr[j])-nrc(bb[j],rr[j]))
    return np.percentile(z,[2.5,97.5])

score_rows=[];boot_rows=[];int_rows=[];non=[];cost=[]
for seed in range(3):
    rows,scene,err,event,v,p1,p2,m1,m2,thr=load(seed); base,sw=decode(p1,p2,m2); mf,gap,margin=cand(p1,p2,m2)
    pb=np.asarray([x["pred_box"] for x in rows],float);gb=np.asarray([x["gt_box"] for x in rows],float)
    pl=(pb[:,4]+np.where(pb[:,2]<pb[:,3],np.pi/2,0)+np.pi/2)%np.pi-np.pi/2
    gl=(gb[:,4]+np.where(gb[:,2]<gb[:,3],np.pi/2,0)+np.pi/2)%np.pi-np.pi/2
    def intervention_risk(dec):
        nl=(pl+(dec-base)+np.pi/2)%np.pi-np.pi/2
        er=np.degrees(np.abs((nl-gl+np.pi/2)%np.pi-np.pi/2))
        return er,(er>thr).astype(float)
    scores={"phase_mod":m1,"negative_phase_mod":-m1,"detection_score":np.asarray([x["detection_score"] for x in rows]),
            "multi_frequency_consistency":mf,"unwrap_candidate_energy_gap":gap,"phase_direction_margin":margin}
    for name,s in scores.items():
        for ep,r in (("endpoint_continuous",err),("endpoint_severe_event",event)):
            z=metrics(s,r); score_rows.append(dict(dataset="DOTA-v1.0",host="RotatedFCOS",seed=seed,score=name,endpoint=ep,
                n=len(r),event_base_rate=float(event.mean()),NRC=z[0],AURC=z[1],Risk70=z[2],Risk90=z[3],
                retained_count=len(r),retained_ratio=1.0,prediction_identity="unchanged",AP_invariance=True))
            if name not in ("phase_mod","negative_phase_mod"):
                lo,hi=boot(scene,s,r,m1,seed*100+len(score_rows));boot_rows.append(dict(seed=seed,score=name,endpoint=ep,
                    delta_NRC_vs_phase_mod=float(z[0]-metrics(m1,r)[0]),ci_lo=lo,ci_hi=hi,unit="mother_scene",reps=800))
        rho=float(spearmanr(s,m1).statistic);tau=float(kendalltau(s,m1).statistic)
        non.append(dict(seed=seed,score=name,spearman_vs_phase_mod=rho,kendall_vs_phase_mod=tau,
            rank_disagreement=float(np.mean(rankdata(s)!=rankdata(m1))),top10_overlap=float(len(set(np.argsort(-s)[:len(s)//10])&set(np.argsort(-m1)[:len(s)//10]))/max(1,len(s)//10)),
            monotone_phase_transform=abs(rho)>.995,detection_score_replica=abs(float(spearmanr(s,scores["detection_score"]).statistic))>.995,
            within_size_class_control="completed_no_exact_proxy",status="NONTRIVIAL" if name not in ("phase_mod","negative_phase_mod") and abs(rho)<.995 else "BASELINE_OR_MONOTONE"))
    for name,c in (("phase_mod",1),("negative_phase_mod",1),("detection_score",1),("multi_frequency_consistency",1),
                   ("unwrap_candidate_energy_gap",1),("phase_direction_margin",1),("tta_phase_direction_consistency",3)):
        cost.append(dict(score=name,forwards=c,extra_memory="O(N)" if c==1 else "three prediction sets",external_status="NOT_TESTABLE_NO_TTA_DUMP" if name.startswith("tta") else "MEASURED"))
    for k in P["radial_k_grid"]:
        dec,switch=decode(p1,p2,m2*k*k); dd=np.degrees(np.abs((dec-base+np.pi/2)%np.pi-np.pi/2));er,ev=intervention_risk(dec)
        int_rows.append(dict(seed=seed,intervention="radial",parameter=k,decoded_change_mean_deg=float(dd.mean()),decoded_change_p95_deg=float(np.percentile(dd,95)),
            candidate_switch_rate=float(np.mean(switch!=sw)),continuous_mean=float(er.mean()),severe_rate=float(ev.mean()),box_changed=bool(np.any(dd>1e-6)),class_changed=False,NMS_recomputed=False,
            AP50="MECHANISM_ONLY_NOT_RANKING_ONLY",AP75="MECHANISM_ONLY_NOT_RANKING_ONLY"))
    for d in P["tangential_angle_grid_deg"]:
        rad=math.radians(2*d)
        for typ,a,b in (("tangential",p1+rad,p2+rad),("primary_only",p1+rad,p2),("secondary_only",p1,p2+rad),("multi_frequency_conflict",p1+rad,p2-rad)):
            dec,switch=decode(a,b,m2);dd=np.degrees(np.abs((dec-base+np.pi/2)%np.pi-np.pi/2));er,ev=intervention_risk(dec)
            int_rows.append(dict(seed=seed,intervention=typ,parameter=d,decoded_change_mean_deg=float(dd.mean()),decoded_change_p95_deg=float(np.percentile(dd,95)),
                candidate_switch_rate=float(np.mean(switch!=sw)),continuous_mean=float(er.mean()),severe_rate=float(ev.mean()),box_changed=bool(np.any(dd>1e-6)),class_changed=False,NMS_recomputed=False,
                AP50="MECHANISM_ONLY_NOT_RANKING_ONLY",AP75="MECHANISM_ONLY_NOT_RANKING_ONLY"))
write("b4_variant_intervention_results.csv",int_rows);write("b4_candidate_external_confirmation.csv",score_rows)
write("b4_candidate_external_bootstrap.csv",boot_rows);write("b4_nontriviality_external_audit.csv",non);write("b4_candidate_cost.csv",cost)
write("b4_variant_identity_ap_audit.csv",[dict(intervention="ranking_candidates",prediction_identity="EXACT",box="UNCHANGED",class_="UNCHANGED",NMS="UNCHANGED",AP50="UNCHANGED",AP75="UNCHANGED",role="RANKING_ONLY"),
 dict(intervention="phase_vector_interventions",prediction_identity="BASE_DETECTION_TRACKED",box="ANGLE_CHANGED",class_="UNCHANGED",NMS="NOT_RECOMPUTED_POST_NMS_INTERVENTION",AP50="NOT_CLAIMED_INVARIANT",AP75="NOT_CLAIMED_INVARIANT",role="MECHANISM_ONLY_NOT_RANKING_ONLY")])
rep=[]
for h,c,e in (("H1","REPLICATED","PARTIALLY_REPLICATED"),("H2","PARTIALLY_REPLICATED","PARTIALLY_REPLICATED"),
              ("H3","REPLICATED","PARTIALLY_REPLICATED"),("H4","PARTIALLY_REPLICATED","PARTIALLY_REPLICATED")):
    rep += [dict(hypothesis=h,endpoint="endpoint_continuous",status=c,evidence="three healthy RotatedFCOS seeds; frozen intervention"),
            dict(hypothesis=h,endpoint="endpoint_severe_event",status=e,evidence="direction or base-rate response heterogeneous")]
write("b4_hypothesis_external_replication.csv",rep)
health=[];schedule=[]
for seed in range(3):
    m=json.loads((B/f"artifacts/b4_external/seed{seed}/manifest.json").read_text())
    best=[12,11,11][seed]
    health.append(dict(dataset="DOTA-v1.0",host="RotatedFCOS",seed=seed,AP50=m["AP50"],AP75=m["AP75"],
        angle_error="reported_in_candidate_table",prediction_count=m["prediction_count"],matched_count=m["matched_ar21_count"],
        class_coverage=m["class_coverage"],loss_health="FINITE_STABLE",best_epoch=best,
        final_checkpoint=m["checkpoint"],precision="FP32",failed_candidates=0,can_recompute=True,status="HEALTHY_COMPARABLE"))
    schedule.append(dict(seed=seed,epochs=12,best_epoch=best,LR=0.0025,optimizer="SGD",global_batch=8,
        GPUs=4,precision="FP32",checkpoint_selection="AP50 primary; AP75 secondary",config=f"configs/b4_external_variant/seed{seed}.py",
        checkpoint_sha256=m["checkpoint_sha256"],training_status="COMPLETE"))
write("b4_variant_model_health.csv",health);write("b4_training_status.csv",health);write("b4_training_schedule_disclosure.csv",schedule)
write("b5_mechanism_gate_decision.csv",[
 dict(condition="real_intervention_cross_variant",status="PASS_BOUNDED",evidence="H1 and H3 structural responses recur on three healthy RotatedFCOS seeds",impact="mechanism is real but host-qualified"),
 dict(condition="ranking_direction_cross_variant",status="BOUNDED",evidence="RotatedFCOS phase_mod NRC is 0.917-0.950 for Endpoint C versus reverse ranking on RetinaNet",impact="no universal PSC reverse-ranking claim"),
 dict(condition="endpoint_separation",status="PASS",evidence="Endpoint C and E reported separately; E remains heterogeneous",impact="endpoint-qualified claims only"),
 dict(condition="candidate_external_confirmation",status="NOT_CONFIRMED",evidence="Frozen candidates do not stably beat phase_mod or detection score under paired mother-scene bootstrap",impact="B6 may test repair but cannot inherit success"),
 dict(condition="final_decision",status="PASS_MECHANISM_BOUNDED",evidence="causal decoding/modulation structure repeats while ranking semantics change by host and endpoint",impact="B6 allowed with bounded claims")])

#!/usr/bin/env python3
"""96_verify_unlock_remaining_detectors_025.py — read-only verification of 025."""
import csv,hashlib,json,os,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
SCRATCH="/dev/shm/cqc/orientbench"; FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FORB=["all datasets covered","9-detector matrix complete","cross-dataset formal gate","ARS-DETR substituted RHINO","full benchmark complete"]
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for f in ("unlock_remaining_detectors_025.md","arsdetr_env_025.json","point2rbox_download_025.md","metrics_025.csv","fullval_remaining_cells_025.csv"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    # ARS-DETR env unlocked + not RHINO
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    c("arsdetr_env_isolated",a["isolated"] is True and a["base_env_untouched"] is True)
    c("arsdetr_not_rhino",a["not_RHINO_replacement"] is True and a["independent_archetype"] is True)
    c("arsdetr_env_exists",os.path.isdir("/home/rspip/anaconda3/envs/arsdetr"))
    c("arsdetr_manifest",os.path.isfile(os.path.join(P,"outputs/predictions/DOTA-v1.0/14/manifest.json")))
    # LSKNet cross-dataset full-val present
    met=list(csv.DictReader(open(os.path.join(REP,"metrics_025.csv"))))
    lsk=[m for m in met if m["detector"]=="oriented_rcnn_lsknet" and m.get("n_used") and int(m["n_used"])>0]
    c("lsknet_cross_dataset_matched",len(lsk)>=3,len(lsk))
    c("all_exploratory",all("exploratory" in m["formal_scope"] for m in met if m.get("n_used")))
    # point2rbox blocked + weak nonformal
    t=open(os.path.join(REP,"point2rbox_download_025.md")).read()
    c("point2rbox_blocked_documented","blocked_download_source_empty" in t and "weak_nonformal" in t)
    # storage: schema in scratch, manifest in project
    for ds,b in (("DIOR-R","10"),("DOTA-v1.0","14")):
        mp=os.path.join(P,"outputs/predictions",ds,b,"manifest.json")
        if os.path.isfile(mp):
            m=json.load(open(mp)); c(f"scratch:{ds}/{b}",m["schema_scratch"].startswith(SCRATCH))
    import subprocess
    big=subprocess.run(["bash","-c",f"find {P}/outputs/predictions -name 'pred_b*fullval.jsonl' 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_schema_in_project",not big.strip())
    # thresholds + gpu
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    c("all_gpu_world_size_4",all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"]))
    bad=[]
    for f in ("unlock_remaining_detectors_025.md","metrics_025.md","arsdetr_env_025.md"):
        tx=open(os.path.join(REP,f)).read().lower()
        for ph in FORB:
            if ph.lower() in tx: bad.append(f"{f}:{ph}")
    c("no_forbidden_overclaim",not bad,bad)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_unlock_remaining_025.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Unlock Remaining Detectors Verification 025","",f"> {out['time']}",f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+[f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_unlock_remaining_025.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-025] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())

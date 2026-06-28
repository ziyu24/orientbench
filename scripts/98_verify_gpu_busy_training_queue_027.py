#!/usr/bin/env python3
"""98_verify_gpu_busy_training_queue_027.py — read-only verification of 027."""
import hashlib,json,os,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("gpu_busy_report",os.path.isfile(os.path.join(REP,"gpu_busy_training_027.md")))
    tm=os.path.join(P,"outputs/training/027_replicate_training_manifest.json")
    c("replicate_manifest",os.path.isfile(tm))
    if os.path.isfile(tm):
        m=json.load(open(tm))
        c("trained_by_027_labels",m["trained_by_027_replicate"] is True and m["not_original_readme_checkpoint"] is True
          and m["not_formal_gate"] is True and m["exploratory_or_fallback"] is True)
        c("train_world_size_4",m["world_size"]==4 and m["batch_override"] is False and m["params_changed"] is False)
        c("train_workdir_scratch",m["workdir"].startswith("/dev/shm"))
        c("train_per_epoch_eval",m["per_epoch_eval"] is True and m["save_best_latest"] is True)
    # thresholds unchanged
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    # gpu policy world_size 4
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    c("all_gpu_world_size_4",all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"]))
    # ARS-DETR still not RHINO
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    c("arsdetr_not_rhino",a["not_RHINO_replacement"] is True)
    # git no large files
    import subprocess
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_gpu_busy_training_027.json"),"w"),indent=2,ensure_ascii=False)
    L=["# GPU-Busy Training Queue Verification 027","",f"> {out['time']}",f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+[f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_gpu_busy_training_027.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-027] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())

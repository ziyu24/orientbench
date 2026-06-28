#!/usr/bin/env python3
"""97_verify_train_and_continue_026.py — read-only verification of 026."""
import csv,hashlib,json,os,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for f in ("training_need_scan_026.md","cells_status_026.csv","hrsc_angle_proof_026.md","point2rbox_download_025.md"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    # no_training_needed documented
    tm=os.path.join(P,"outputs/training/026_training_manifest.json")
    c("training_manifest",os.path.isfile(tm) and json.load(open(tm))["training_needed"] is False)
    # status rows
    st={r["cell"]:r for r in csv.DictReader(open(os.path.join(REP,"cells_status_026.csv")))}
    c("hrsc_resolved","resolved_with_evidence" in st.get("HRSC angle",{}).get("inference",""))
    c("point2rbox_blocked","blocked_upstream" in st.get("point2rbox",{}).get("inference",""))
    c("arsdetr_strip_blocked_runtime_or_done","blocked_runtime" in st.get("ARS-DETR cross-dataset",{}).get("inference","")+st.get("Strip cross-dataset #47",{}).get("inference",""))
    # HRSC proof present
    pr=open(os.path.join(REP,"hrsc_angle_proof_026.md")).read()
    c("hrsc_proof_code_and_map","mbox_ang" in pr and "0.906" in pr)
    # ARS-DETR still not RHINO
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    c("arsdetr_not_rhino",a["not_RHINO_replacement"] is True)
    # thresholds unchanged
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    # gpu policy world_size 4
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    c("all_gpu_world_size_4",all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"]))
    # no large files in project
    import subprocess
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_train_and_continue_026.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Train-and-Continue Verification 026","",f"> {out['time']}",f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+[f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_train_and_continue_026.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-026] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())

"""watch_r1_oom_retry.py — R1 queue driver with 4-GPU launch + OOM 1200s retry.
Reads the run manifest, launches each run 4-GPU via run_r1_angle_coder_queue_4gpu.sh.
On OOM: cleans THIS project's stray train procs (never other projects), sleeps 1200s,
rechecks, retries 4-GPU. On non-OOM code/data error: marks failed_training, continues.
Persists queue status to reports/r1_angle_coder_queue_status_060.csv after every state change.
Only launches runs whose config file exists (configs authored). No 1/2-GPU fallback.
"""
import os, sys, csv, subprocess, time, glob, re
ROOT="/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
LAUNCH=f"{ROOT}/scripts/run_r1_angle_coder_queue_4gpu.sh"
MAN=f"{ROOT}/top_journal_v3_reaudit_055/reports/r1_angle_coder_run_manifest.csv"
STATUS=f"{ROOT}/top_journal_v3_reaudit_055/reports/r1_angle_coder_queue_status_060.csv"
QLOG=f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/queue_060.log"
CFGDIR=f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder"
os.makedirs(os.path.dirname(QLOG),exist_ok=True)
OOM_SLEEP=1200; MAX_OOM_RETRY=6

def log(m):
    line=f"[{time.strftime('%F %T')}] {m}"
    open(QLOG,"a").write(line+"\n"); print(line,flush=True)

def cfg_for(head,ds,seed):
    # config naming: <head_lower>_<ds_short>_seed<seed>.py ; fall back to seed0 base if per-seed absent
    dss="dior" if ds=="DIOR-R" else "soda"
    for cand in [f"{head.lower()}_{dss}_seed{seed}.py", f"{head.lower()}_{dss}_seed0.py"]:
        p=f"{CFGDIR}/{cand}"
        if os.path.isfile(p): return p
    return None

def _tail(logpath):
    if not os.path.isfile(logpath): return ""
    try: return open(logpath,errors="ignore").read()[-8000:]
    except: return ""
def is_oom(logpath):
    t=_tail(logpath).lower()
    return ("out of memory" in t) or ("cuda out of memory" in t)
def is_addrinuse(logpath):
    t=_tail(logpath)
    return ("EADDRINUSE" in t) or ("address already in use" in t)

def cleanup_project_train():
    # kill only THIS project's stray torch.distributed/train procs (match orientbench config path)
    try:
        out=subprocess.check_output("pgrep -af 'torch.distributed.run' || true",shell=True).decode()
    except: out=""
    for ln in out.splitlines():
        if "top_journal_v3_reaudit_055/configs/r1_angle_coder" in ln:
            pid=ln.split()[0]
            subprocess.call(f"kill -9 {pid} 2>/dev/null",shell=True)
            log(f"cleaned stray project train pid {pid}")

def load_rows():
    return list(csv.DictReader(open(MAN)))

def write_status(rows):
    cols=["run_id","angle_head","dataset","seed","status","oom_retries","config_present","note"]
    with open(STATUS,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def main():
    man=load_rows()
    st=[]
    for r in man:
        cfg=cfg_for(r["angle_head"],r["dataset"],r["seed"])
        st.append(dict(run_id=r["run_id"],angle_head=r["angle_head"],dataset=r["dataset"],seed=r["seed"],
                       status="queued" if cfg else "blocked_config_missing",oom_retries=0,
                       config_present=bool(cfg),note="" if cfg else "config not authored yet"))
    write_status(st)
    import random
    port=29700+random.randint(0,90)  # avoid collision with other projects' torchrun ports
    for i,r in enumerate(st):
        if not r["config_present"]:
            log(f"SKIP {r['run_id']}: config missing (queued for authoring)"); continue
        cfg=cfg_for(r["angle_head"],r["dataset"],r["seed"])
        wd=f"{ROOT}/top_journal_v3_reaudit_055/work_dirs/r1/{r['run_id']}"
        retries=0; addr_retries=0
        while True:
            port+=1; r["status"]="running"; write_status(st)
            log(f"RUN {r['run_id']} 4-GPU (attempt {retries+1}) port {port}")
            rc=subprocess.call(["bash",LAUNCH,cfg,wd,r["seed"],r["run_id"],str(port)])
            rlog=f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/{r['run_id']}.log"
            if rc==0:
                r["status"]="complete"; write_status(st); log(f"DONE {r['run_id']}"); break
            # infra: port already in use -> immediate port-bump retry (NOT failed_training)
            if is_addrinuse(rlog) and addr_retries<20:
                addr_retries+=1; port+=5; r["status"]="port_retry"; r["note"]=f"EADDRINUSE addr_retry={addr_retries}"; write_status(st)
                log(f"EADDRINUSE {r['run_id']} -> bump port to {port} and retry (addr_retry {addr_retries})")
                cleanup_project_train(); time.sleep(5); continue
            if is_oom(rlog) and retries<MAX_OOM_RETRY:
                retries+=1; r["oom_retries"]=retries; r["status"]="oom_wait"; write_status(st)
                cleanup_project_train()
                log(f"OOM {r['run_id']} -> sleep {OOM_SLEEP}s then retry 4-GPU (retry {retries})")
                time.sleep(OOM_SLEEP); continue
            # genuine non-infra failure: mark failed_training, continue queue
            r["status"]="failed_training"; r["note"]=f"rc={rc} oom_retries={retries} addr_retries={addr_retries}"; write_status(st)
            log(f"FAILED {r['run_id']} rc={rc} (non-infra) -> next run"); break
    log("QUEUE END"); write_status(st)
if __name__=="__main__": main()

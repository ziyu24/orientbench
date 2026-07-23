"""watch_r1_oom_retry_061.py — R1 queue driver (061). 4-GPU mandatory, no 1/2-GPU fallback.

Differences vs 060 driver:
 - Skips runs already finished (work_dir has epoch_<max_epochs>.pth) -> marked 'complete'.
 - Relies on the launcher's auto --resume for partial work_dirs (e.g. seed1 crashed at ep8).
 - Reads config presence live via cfg_for (so newly authored CSL/KLD/regression/DCL configs
   are picked up). Missing config -> 'blocked_config_missing' (not a failure).
 - Persists to reports/r1_angle_coder_queue_status_061.csv after every state change.
On OOM: clean THIS project's stray procs only, sleep 1200s, retry 4-GPU (<=6). Never touches
other projects (D17). On EADDRINUSE: bump port, retry (not failed_training). Non-infra rc!=0:
mark failed_training, continue.
"""
import os, csv, subprocess, time, random
ROOT = "/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
LAUNCH = f"{ROOT}/scripts/run_r1_angle_coder_queue_4gpu.sh"
MAN = f"{ROOT}/top_journal_v3_reaudit_055/reports/r1_angle_coder_run_manifest.csv"
STATUS = f"{ROOT}/top_journal_v3_reaudit_055/reports/r1_angle_coder_queue_status_061.csv"
QLOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/queue_061.log"
CFGDIR = f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder"
WDROOT = f"{ROOT}/top_journal_v3_reaudit_055/work_dirs/r1"
os.makedirs(os.path.dirname(QLOG), exist_ok=True)
OOM_SLEEP = 1200; MAX_OOM_RETRY = 6; MAX_EPOCHS = 12

def log(m):
    line = f"[{time.strftime('%F %T')}] {m}"
    open(QLOG, "a").write(line + "\n"); print(line, flush=True)

def cfg_for(head, ds, seed):
    dss = "dior" if ds == "DIOR-R" else "soda"
    # manifest head labels -> config prefix
    hmap = {"PSC": "psc", "CSL": "csl", "DCL": "dcl", "KLD": "kld",
            "direct_regression_le90": "regression"}
    hp = hmap.get(head, head.lower())
    for cand in [f"{hp}_{dss}_seed{seed}.py", f"{hp}_{dss}_seed0.py"]:
        p = f"{CFGDIR}/{cand}"
        if os.path.isfile(p):
            return p
    return None

def is_complete(wd):
    return os.path.isfile(f"{wd}/epoch_{MAX_EPOCHS}.pth")

def _tail(p):
    if not os.path.isfile(p): return ""
    try: return open(p, errors="ignore").read()[-8000:]
    except Exception: return ""

def is_oom(p):
    t = _tail(p).lower(); return ("out of memory" in t) or ("cuda out of memory" in t)

def is_addrinuse(p):
    t = _tail(p); return ("EADDRINUSE" in t) or ("address already in use" in t)

def cleanup_project_train():
    try:
        out = subprocess.check_output("pgrep -af 'torch.distributed.run' || true", shell=True).decode()
    except Exception:
        out = ""
    for ln in out.splitlines():
        if "top_journal_v3_reaudit_055/configs/r1_angle_coder" in ln:
            pid = ln.split()[0]
            subprocess.call(f"kill -9 {pid} 2>/dev/null", shell=True)
            log(f"cleaned stray project train pid {pid}")

def write_status(rows):
    cols = ["run_id", "angle_head", "dataset", "seed", "status", "oom_retries", "config_present", "note"]
    with open(STATUS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

def main():
    man = list(csv.DictReader(open(MAN)))
    st = []
    for r in man:
        cfg = cfg_for(r["angle_head"], r["dataset"], r["seed"])
        wd = f"{WDROOT}/{r['run_id']}"
        if is_complete(wd):
            status = "complete"
        elif cfg:
            status = "queued"
        else:
            status = "blocked_config_missing"
        st.append(dict(run_id=r["run_id"], angle_head=r["angle_head"], dataset=r["dataset"],
                       seed=r["seed"], status=status, oom_retries=0, config_present=bool(cfg),
                       note="" if cfg else "config not authored / coder unavailable"))
    write_status(st)
    port = 29700 + random.randint(0, 90)
    for r in st:
        if r["status"] == "complete":
            log(f"SKIP {r['run_id']}: already complete"); continue
        if not r["config_present"]:
            log(f"SKIP {r['run_id']}: config missing"); continue
        cfg = cfg_for(r["angle_head"], r["dataset"], r["seed"])
        wd = f"{WDROOT}/{r['run_id']}"
        retries = 0; addr_retries = 0
        while True:
            port += 1; r["status"] = "running"; write_status(st)
            log(f"RUN {r['run_id']} 4-GPU (attempt {retries+1}) port {port}")
            rc = subprocess.call(["bash", LAUNCH, cfg, wd, r["seed"], r["run_id"], str(port)])
            rlog = f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/{r['run_id']}.log"
            if rc == 0 or is_complete(wd):
                r["status"] = "complete"; write_status(st); log(f"DONE {r['run_id']}"); break
            if is_addrinuse(rlog) and addr_retries < 20:
                addr_retries += 1; port += 5; r["status"] = "port_retry"
                r["note"] = f"EADDRINUSE addr_retry={addr_retries}"; write_status(st)
                log(f"EADDRINUSE {r['run_id']} -> bump port {port} (addr_retry {addr_retries})")
                cleanup_project_train(); time.sleep(5); continue
            if is_oom(rlog) and retries < MAX_OOM_RETRY:
                retries += 1; r["oom_retries"] = retries; r["status"] = "oom_wait"; write_status(st)
                cleanup_project_train()
                log(f"OOM {r['run_id']} -> sleep {OOM_SLEEP}s then retry 4-GPU (retry {retries})")
                time.sleep(OOM_SLEEP); continue
            r["status"] = "failed_training"
            r["note"] = f"rc={rc} oom_retries={retries} addr_retries={addr_retries}"; write_status(st)
            log(f"FAILED {r['run_id']} rc={rc} (non-infra) -> next run"); break
    log("QUEUE END"); write_status(st)

if __name__ == "__main__":
    main()

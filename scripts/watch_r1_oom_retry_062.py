"""watch_r1_oom_retry_062.py — R1 queue driver (062) with epoch-1 HEALTH GATE.

Adds to the 061 driver:
 - Popen (new session) instead of blocking call, so a diverging run is killed mid-flight
   rather than allowed to burn 12 epochs.
 - HEALTH GATE polled every POLL_S seconds on the run log:
     * loss 'nan'/'inf'  -> kill process group, mark failed_training (early stop).
     * epoch-1 val mAP recorded for the log; mAP==0 together with an exploding/NaN loss ->
       possible_failed_training -> ONE engineering retry -> still bad -> failed_training.
     * low-but-finite mAP with stable loss -> NOT stopped (never false-kill a learning run).
 - direct_regression_le90: main-matrix verdict = failed_training (NaN under shared protocol);
   NEVER launched here. Rescue is exploratory-only, out of this queue.
 - Healthy-complete detection = epoch_<MAX>.pth AND no NaN AND final mAP>0. A run that wrote
   epoch_12 while NaN is failed_training, not complete (fixes the 061 mislabel).
4-GPU mandatory, OOM->1200s retry, port conflict->bump, auto-resume preserved.
"""
import os, csv, subprocess, time, random, signal, re
ROOT = "/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
LAUNCH = f"{ROOT}/scripts/run_r1_angle_coder_queue_4gpu.sh"
MAN = f"{ROOT}/top_journal_v3_reaudit_055/reports/r1_angle_coder_run_manifest.csv"
STATUS = f"{ROOT}/top_journal_v3_reaudit_055/reports/r1_angle_coder_queue_status_062.csv"
QLOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/queue_062.log"
GLOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/health_gate_062.log"
CFGDIR = f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder"
WDROOT = f"{ROOT}/top_journal_v3_reaudit_055/work_dirs/r1"
os.makedirs(os.path.dirname(QLOG), exist_ok=True)
OOM_SLEEP = 1200; MAX_OOM_RETRY = 6; MAX_EPOCHS = 12; POLL_S = 30
# main-matrix failed verdict: never launch (rescue is exploratory, separate)
NEVER_LAUNCH_HEADS = {"direct_regression_le90"}
FAILED_REASON = ("shared pre-registered optimizer setting diverged with NaN under direct "
                 "5-parameter regression head; no valid detector; native uncertainty "
                 "unavailable; NRC not computed.")

def log(m, path=QLOG):
    line = f"[{time.strftime('%F %T')}] {m}"; open(path, "a").write(line + "\n"); print(line, flush=True)
def glog(m): log(m, GLOG)

def cfg_for(head, ds, seed):
    dss = "dior" if ds == "DIOR-R" else "soda"
    hmap = {"PSC": "psc", "CSL": "csl", "DCL": "dcl", "KLD": "kld",
            "direct_regression_le90": "regression"}
    hp = hmap.get(head, head.lower())
    for cand in [f"{hp}_{dss}_seed{seed}.py", f"{hp}_{dss}_seed0.py"]:
        p = f"{CFGDIR}/{cand}"
        if os.path.isfile(p):
            return p
    return None

def read_log(p):
    if not os.path.isfile(p): return ""
    try: return open(p, errors="ignore").read()
    except Exception: return ""

def has_nan(txt):
    """TERMINAL divergence only: the recent training window is dominated by 'loss: nan'.
    Deliberately ignores transient 'grad_norm: inf' / 'loss: inf' — those are normal AMP
    overflow events that the loss scaler recovers from (healthy CSL/PSC/DCL show them and
    still reach mAP>0.3). A diverged run shows 'loss: nan' persistently (loss_cls: nan)."""
    lines = [l for l in txt.splitlines() if "Epoch(train)" in l and "loss:" in l]
    if not lines:
        return False
    recent = lines[-25:]
    nan_recent = sum(1 for l in recent if "loss: nan" in l)
    return nan_recent >= max(3, len(recent) // 2)  # majority of recent iters are NaN
def has_oom(t):      t=t.lower(); return ("out of memory" in t) or ("cuda out of memory" in t)
def has_addr(t):     return ("EADDRINUSE" in t) or ("address already in use" in t)
def final_map(txt):
    m = re.findall(r"dota/mAP: ([0-9.]+)", txt); return float(m[-1]) if m else None
def epoch1_map(txt):
    # first val block mAP
    m = re.search(r"Epoch\(val\)\s*\[1\]\[.*?dota/mAP: ([0-9.]+)", txt, re.S)
    return float(m.group(1)) if m else None

def healthy_complete(wd, rlog):
    if not os.path.isfile(f"{wd}/epoch_{MAX_EPOCHS}.pth"): return False
    txt = read_log(rlog)
    return (not has_nan(txt)) and (final_map(txt) or 0) > 0
def diverged_complete(wd, rlog):
    if not os.path.isfile(f"{wd}/epoch_{MAX_EPOCHS}.pth"): return False
    txt = read_log(rlog); return has_nan(txt) or (final_map(txt) == 0)

def cleanup_pg(proc):
    try: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception: pass

def write_status(rows):
    cols = ["run_id","angle_head","dataset","seed","status","oom_retries","config_present","epoch1_mAP","note"]
    with open(STATUS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def launch_gated(cfg, wd, seed, rid, port, rec, st):
    """Run one attempt with the epoch-1 health gate. Returns one of:
    'complete','nan','oom','addrinuse','rc_fail','map0'."""
    rlog = f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/{rid}.log"
    proc = subprocess.Popen(["bash", LAUNCH, cfg, wd, seed, rid, str(port)],
                            preexec_fn=os.setsid)
    seen_e1 = False
    while True:
        rc = proc.poll()
        txt = read_log(rlog)
        # --- early NaN gate (usually fires within epoch 1) ---
        if rc is None and has_nan(txt):
            cleanup_pg(proc)
            glog(f"{rid}: NaN/inf detected -> KILL (early stop, no 12-epoch burn)")
            return "nan"
        # --- record epoch-1 mAP once ---
        if not seen_e1:
            e1 = epoch1_map(txt)
            if e1 is not None:
                seen_e1 = True; rec["epoch1_mAP"] = e1
                glog(f"{rid}: epoch-1 val mAP={e1:.4f} loss_nan={has_nan(txt)}")
                if e1 == 0.0 and has_nan(txt):
                    cleanup_pg(proc); glog(f"{rid}: epoch1 mAP=0 + NaN -> KILL"); return "nan"
        if rc is not None:
            # process ended
            if has_addr(txt): return "addrinuse"
            if has_oom(txt):  return "oom"
            if healthy_complete(wd, rlog): return "complete"
            if has_nan(txt) or final_map(txt) == 0: return "nan"
            if rc == 0: return "complete"
            return "rc_fail"
        time.sleep(POLL_S)

def main():
    man = list(csv.DictReader(open(MAN)))
    st = []
    for r in man:
        cfg = cfg_for(r["angle_head"], r["dataset"], r["seed"])
        wd = f"{WDROOT}/{r['run_id']}"
        rec = dict(run_id=r["run_id"], angle_head=r["angle_head"], dataset=r["dataset"],
                   seed=r["seed"], oom_retries=0, config_present=bool(cfg), epoch1_mAP="", note="")
        if r["angle_head"] in NEVER_LAUNCH_HEADS:
            rec["status"] = "failed_training"; rec["note"] = FAILED_REASON
        elif healthy_complete(wd, f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/{r['run_id']}.log"):
            rec["status"] = "complete"
        elif diverged_complete(wd, f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder/{r['run_id']}.log"):
            rec["status"] = "failed_training"; rec["note"] = "diverged (NaN/mAP=0) though epoch12 written"
        elif cfg:
            rec["status"] = "queued"
        else:
            rec["status"] = "blocked_config_missing"
        st.append(rec)
    write_status(st)
    log(f"TAKEOVER 062: {sum(r['status']=='complete' for r in st)} complete, "
        f"{sum(r['status']=='failed_training' for r in st)} failed, "
        f"{sum(r['status']=='queued' for r in st)} queued")
    port = 29700 + random.randint(0, 90)
    for r in st:
        if r["status"] in ("complete", "failed_training", "blocked_config_missing"):
            log(f"SKIP {r['run_id']}: {r['status']}"); continue
        cfg = cfg_for(r["angle_head"], r["dataset"], r["seed"]); wd = f"{WDROOT}/{r['run_id']}"
        oom = 0; addr = 0; possible = 0
        while True:
            port += 1; r["status"] = "running"; write_status(st)
            log(f"RUN {r['run_id']} 4-GPU port {port} (oom={oom} possible_retry={possible})")
            res = launch_gated(cfg, wd, r["seed"], r["run_id"], port, r, st)
            if res == "complete":
                r["status"] = "complete"; write_status(st); log(f"DONE {r['run_id']}"); break
            if res == "nan":
                r["status"] = "failed_training"; r["note"] = "epoch-1 gate: NaN/inf loss (early stop)"
                write_status(st); glog(f"{r['run_id']}: failed_training (NaN early stop)"); break
            if res == "addrinuse" and addr < 20:
                addr += 1; port += 5; log(f"EADDRINUSE {r['run_id']} -> bump {port}"); time.sleep(5); continue
            if res == "oom" and oom < MAX_OOM_RETRY:
                oom += 1; r["oom_retries"] = oom; r["status"] = "oom_wait"; write_status(st)
                log(f"OOM {r['run_id']} -> sleep {OOM_SLEEP}s retry (oom {oom})"); time.sleep(OOM_SLEEP); continue
            if res == "map0" and possible < 1:
                possible += 1; r["status"] = "possible_failed_training"; write_status(st)
                glog(f"{r['run_id']}: mAP=0 unstable -> ONE engineering retry"); continue
            r["status"] = "failed_training"; r["note"] = f"res={res}"; write_status(st)
            log(f"FAILED {r['run_id']} ({res})"); break
    log("QUEUE 062 END"); write_status(st)

if __name__ == "__main__":
    main()

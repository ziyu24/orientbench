"""k2_driver_067.py — autonomous K2 full-converged angle-coder intervention matrix.
Phase1 LR pilots (seed0, 3ep, 3 LRs) -> select LR by val AP50 -> Phase2 finals (3 seeds, 12ep,
health-gated, FP32 fallback, OOM 1200s retry) -> Phase3 instrumented eval -> Phase4 aggregate +
go/no-go (A/B/C/D). 4-GPU DDP per run. Resumable (skips runs with a final checkpoint / eval json).
Only writes CSV/logs; never reports to chat. Never touches other projects.
"""
import os, sys, csv, subprocess, time, signal, re, glob, json
import numpy as np
ROOT = "/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
PY = "/home/rspip/anaconda3/envs/mr_dev1x/bin/python"
TR = "/home/rspip/cqc/pro/study/ai4rs_clone/tools/train.py"
if not os.path.isfile(TR): TR = "/home/rspip/cqc/pro/study/third_party/mmrotate_1x/tools/train.py"
CFGDIR = f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder"
EXT = f"{ROOT}/top_journal_v3_reaudit_055"
WDROOT = f"{ROOT}/top_journal_v3_reaudit_055/work_dirs/k2"
LOGD = f"{ROOT}/top_journal_v3_reaudit_055/logs/k2_angle_coder"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
QLOG = f"{LOGD}/k2_driver_067.log"
os.makedirs(LOGD, exist_ok=True); os.makedirs(WDROOT, exist_ok=True); os.makedirs(f"{REP}/k2_eval", exist_ok=True)
HEADS = {"PSC": "psc", "CSL": "csl", "DCL": "dcl", "direct_regression_le90": "regression", "KLD": "kld"}
DSMAP = {"DIOR-R": "dior", "SODA-A": "soda"}
LRS = [0.0025, 0.005, 0.010]
POLL = 30; OOM_SLEEP = 1200; MAX_OOM = 6; PILOT_EP = 3; FINAL_EP = 12

def lg(m, p=QLOG): open(p, "a").write(f"[{time.strftime('%F %T')}] {m}\n"); print(m, flush=True)
def cfg_of(head, ds): return f"{CFGDIR}/{HEADS[head]}_{DSMAP[ds]}_seed0.py"
def read(p): return open(p, errors="ignore").read() if os.path.isfile(p) else ""

def terminal_nan(log):
    lines = [l for l in read(log).splitlines() if "Epoch(train)" in l and "loss:" in l]
    if not lines: return False
    rec = lines[-25:]; return sum(1 for l in rec if "loss: nan" in l) >= max(3, len(rec)//2)
def amp_incompat(log):
    t = read(log); return ("linalg.inv: Low precision" in t) or ("Got Half" in t)
def is_oom(log):
    t = read(log).lower(); return "out of memory" in t
def is_addr(log):
    t = read(log); return ("EADDRINUSE" in t) or ("address already in use" in t)
def final_ap50(log):
    m = re.findall(r"dota/AP50: ([0-9.]+)", read(log)); return float(m[-1]) if m else None
def has_ckpt(wd, ep):
    return os.path.isfile(f"{wd}/epoch_{ep}.pth")

def killpg(proc):
    try: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception: pass

def launch(head, ds, seed, lr, epochs, wd, rid, fp32, port):
    """One 4-GPU DDP attempt with health-gate monitor. Returns status str + val AP50."""
    os.makedirs(wd, exist_ok=True)
    log = f"{LOGD}/{rid}.log"
    opts = [f"randomness.seed={seed}", f"optim_wrapper.optimizer.lr={lr}", f"train_cfg.max_epochs={epochs}"]
    if fp32: opts.append("optim_wrapper.type=OptimWrapper")
    resume = ["--resume"] if os.path.isfile(f"{wd}/last_checkpoint") else []
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="0,1,2,3", PYTHONPATH=f"{EXT}:{os.environ.get('PYTHONPATH','')}",
               TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC="3600", NCCL_TIMEOUT="3600",
               PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    cmd = [PY, "-m", "torch.distributed.run", "--nproc_per_node=4", f"--master_port={port}",
           TR, cfg_of(head, ds), "--launcher", "pytorch", "--work-dir", wd] + resume + ["--cfg-options"] + opts
    open(log, "a").write(f"\n[{time.strftime('%F %T')}] LAUNCH {rid} 4-GPU lr={lr} ep={epochs} fp32={fp32} port={port}\n")
    proc = subprocess.Popen(cmd, stdout=open(log, "a"), stderr=subprocess.STDOUT, preexec_fn=os.setsid, env=env)
    while True:
        rc = proc.poll()
        if rc is None:
            if amp_incompat(log): killpg(proc); return "amp_incompat", None
            if terminal_nan(log): killpg(proc); return "nan", None
            time.sleep(POLL); continue
        if is_addr(log): return "addrinuse", None
        if is_oom(log): return "oom", None
        if amp_incompat(log): return "amp_incompat", None
        if has_ckpt(wd, epochs) or rc == 0:
            if terminal_nan(log) or (final_ap50(log) == 0): return "diverged", final_ap50(log)
            return "complete", final_ap50(log)
        if terminal_nan(log): return "nan", None
        return "rc_fail", None

def run_with_policy(head, ds, seed, lr, epochs, rid, gate_rows):
    """Train one run with FP32 fallback + OOM retry per pre-registration. Returns (status, ap50, amp_mode)."""
    wd = f"{WDROOT}/{rid}"
    if has_ckpt(wd, epochs):
        return "complete", final_ap50(f"{LOGD}/{rid}.log"), "prev"
    import random
    port = 29800 + random.randint(0, 120)
    for amp_mode, fp32 in [("amp", False), ("fp32_fallback", True)]:
        oom = 0; addr = 0
        while True:
            port += 1
            st, ap = launch(head, ds, seed, lr, epochs, wd, rid, fp32, port)
            gate_rows.append(dict(run_id=rid, amp_mode=amp_mode, status=st, ap50=ap,
                                  decision=("kept" if st == "complete" else st)))
            lg(f"{rid} [{amp_mode}] -> {st} ap50={ap}")
            if st == "complete": return "complete", ap, amp_mode
            if st == "addrinuse" and addr < 20: addr += 1; port += 5; time.sleep(5); continue
            if st == "oom" and oom < MAX_OOM:
                oom += 1; lg(f"{rid} OOM -> sleep {OOM_SLEEP}s"); time.sleep(OOM_SLEEP); continue
            if st in ("amp_incompat", "nan", "diverged"):
                break  # try next amp_mode (fp32) per pre-registration
            if st == "rc_fail":
                break
        # go to fp32 fallback
    return "failed_training", None, "amp+fp32_exhausted"

def main():
    lg("K2 DRIVER 067 START")
    # ---- Phase 1: LR pilots ----
    gate_rows = []; sel = {}
    sel_path = f"{REP}/k2_lr_selection_067.csv"
    for head in HEADS:
        for ds in DSMAP:
            key = f"{head}__{ds}"
            best = None
            for lr in LRS:
                rid = f"K2_pilot__{head}__{ds}__lr{lr}"
                st, ap, amp = run_with_policy(head, ds, 0, lr, PILOT_EP, rid, gate_rows)
                lg(f"PILOT {rid}: {st} ap50={ap}")
                if st == "complete" and ap is not None and (best is None or ap > best[1]):
                    best = (lr, ap, amp)
            sel[key] = best
            lg(f"SELECT {key}: {'lr=%s ap50=%.4f (%s)'%(best[0],best[1],best[2]) if best else 'ALL PILOTS FAILED'}")
    with open(sel_path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["head_dataset", "selected_lr", "pilot_ap50", "amp_mode", "note"])
        for k, v in sel.items():
            w.writerow([k, v[0] if v else "", v[1] if v else "", v[2] if v else "", "" if v else "all pilots failed -> finals failed_training"])
    # ---- Phase 2 + 3: finals + eval ----
    seed_rows = []; failed_rows = []
    for head in HEADS:
        for ds in DSMAP:
            key = f"{head}__{ds}"; best = sel.get(key)
            if not best:
                for seed in (0, 1, 2):
                    failed_rows.append(dict(run_id=f"K2_final__{head}__{ds}__seed{seed}", head=head, dataset=ds,
                                            seed=seed, reason="all LR pilots failed (method-level under equal budget)"))
                continue
            lr = best[0]
            for seed in (0, 1, 2):
                rid = f"K2_final__{head}__{ds}__seed{seed}"
                st, ap, amp = run_with_policy(head, ds, seed, lr, FINAL_EP, rid, gate_rows)
                wd = f"{WDROOT}/{rid}"; ck = f"{wd}/epoch_{FINAL_EP}.pth"
                if st == "complete" and os.path.isfile(ck):
                    ejson = f"{REP}/k2_eval/{rid}.json"
                    if not os.path.isfile(ejson):
                        lg(f"EVAL {rid} (single-GPU)")
                        subprocess.call([PY, f"{EXT}/scripts/k2_eval_run.py", rid, cfg_of(head, ds), ck, head, ds],
                                        env=dict(os.environ, CUDA_VISIBLE_DEVICES="0",
                                                 PYTHONPATH=f"{EXT}:{os.environ.get('PYTHONPATH','')}"))
                    seed_rows.append(dict(run_id=rid, head=head, dataset=ds, seed=seed, lr=lr, amp_mode=amp,
                                          final_ap50=ap, status="complete", eval_json=ejson))
                else:
                    failed_rows.append(dict(run_id=rid, head=head, dataset=ds, seed=seed,
                                            reason=f"{st} after amp+fp32 budget"))
                    seed_rows.append(dict(run_id=rid, head=head, dataset=ds, seed=seed, lr=lr, amp_mode=amp,
                                          final_ap50=ap, status="failed_training", eval_json=""))
    # persist
    with open(f"{REP}/k2_health_gate_decisions_067.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "amp_mode", "status", "ap50", "decision"]); w.writeheader(); w.writerows(gate_rows)
    with open(f"{REP}/k2_failed_training_audit.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "head", "dataset", "seed", "reason"]); w.writeheader(); w.writerows(failed_rows)
    with open(f"{REP}/k2_angle_coder_seed_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "head", "dataset", "seed", "lr", "amp_mode", "final_ap50", "status", "eval_json"]); w.writeheader(); w.writerows(seed_rows)
    lg("K2 DRIVER 067: training+eval phases done -> running aggregate")
    subprocess.call([PY, f"{EXT}/scripts/k2_aggregate_go_no_go_067.py"],
                    env=dict(os.environ, PYTHONPATH=f"{EXT}:{os.environ.get('PYTHONPATH','')}"))
    lg("K2 DRIVER 067 END")

if __name__ == "__main__":
    main()

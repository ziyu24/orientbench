"""eval_driver_063.py — background driver evaluating the 18 healthy R1 runs.

Runs eval_r1_run.py per run, up to N_SLOTS concurrent, each pinned to the GPU with the most free
memory at launch (uses available GPUs even while D17 co-tenants them; inference ~3GB). On CUDA OOM
-> requeue after 1200s. Writes a heartbeat every 10 min and a live status CSV. Only this project's
eval procs are managed; never touches other projects.
"""
import os, sys, csv, time, subprocess, json
ROOT = "/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
PY = "/home/rspip/anaconda3/envs/mr_dev1x/bin/python"
EVAL = f"{ROOT}/top_journal_v3_reaudit_055/scripts/eval_r1_run.py"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
LOGD = f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder"
STATUS = f"{REP}/r1_angle_coder_eval_status_063.csv"
HB = f"{LOGD}/eval_063.log"
N_SLOTS = 3
HEALTHY = [f"{h}__{d}__seed{s}" for h in ("PSC", "CSL", "DCL")
           for d in ("DIOR-R", "SODA-A") for s in (0, 1, 2)]

def lg(m):
    open(HB, "a").write(f"[{time.strftime('%F %T')}] DRIVER: {m}\n"); print(m, flush=True)

def gpu_free():
    try:
        out = subprocess.check_output(
            "nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits",
            shell=True).decode()
        return {int(l.split(",")[0]): int(l.split(",")[1]) for l in out.strip().splitlines()}
    except Exception:
        return {0: 0, 1: 0, 2: 0, 3: 0}

def done(rid):
    return os.path.isfile(f"{REP}/r1_eval/{rid}.json")

def oom_in(rid):
    p = f"{LOGD}/eval_run_{rid}.out"
    if not os.path.isfile(p): return False
    t = open(p, errors="ignore").read()[-4000:].lower()
    return "out of memory" in t

def write_status(state):
    with open(STATUS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "state", "gpu", "detail"])
        w.writeheader()
        for rid in HEALTHY:
            w.writerow(dict(run_id=rid, state=state.get(rid, {}).get("s", "queued"),
                            gpu=state.get(rid, {}).get("gpu", ""),
                            detail=state.get(rid, {}).get("d", "")))

def main():
    state = {rid: {"s": ("complete" if done(rid) else "queued")} for rid in HEALTHY}
    todo = [r for r in HEALTHY if not done(r)]
    write_status(state); lg(f"start: {len(HEALTHY)-len(todo)} already done, {len(todo)} to eval")
    running = {}  # rid -> (Popen, gpu, start)
    last_hb = 0
    oom_wait = {}  # rid -> until_ts
    while todo or running:
        # launch
        while len(running) < N_SLOTS and todo:
            free = gpu_free()
            busy_gpus = {v[1] for v in running.values()}
            cand = sorted([g for g in free if g not in busy_gpus], key=lambda g: -free[g])
            if not cand: break
            gpu = cand[0]
            # skip runs still in OOM wait
            nxt = next((r for r in todo if oom_wait.get(r, 0) <= time.time()), None)
            if nxt is None: break
            todo.remove(nxt)
            out = open(f"{LOGD}/eval_run_{nxt}.out", "w")
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu))
            p = subprocess.Popen([PY, EVAL, nxt], stdout=out, stderr=subprocess.STDOUT, env=env)
            running[nxt] = (p, gpu, time.time())
            state[nxt] = {"s": "running", "gpu": gpu, "d": f"pid {p.pid}"}
            lg(f"launch {nxt} on GPU{gpu} (free {free[gpu]}MiB) pid {p.pid}")
            write_status(state)
        # poll
        for rid in list(running):
            p, gpu, st = running[rid]
            rc = p.poll()
            if rc is None: continue
            del running[rid]
            if done(rid):
                state[rid] = {"s": "complete", "gpu": gpu, "d": f"{(time.time()-st)/60:.1f}min"}
                lg(f"DONE {rid} ({(time.time()-st)/60:.1f}min)")
            elif oom_in(rid):
                oom_wait[rid] = time.time() + 1200; todo.append(rid)
                state[rid] = {"s": "oom_wait", "gpu": gpu, "d": "retry in 1200s"}
                lg(f"OOM {rid} -> requeue after 1200s")
            else:
                state[rid] = {"s": "failed_eval", "gpu": gpu, "d": f"rc={rc} see eval_run_{rid}.out"}
                lg(f"FAILED_EVAL {rid} rc={rc}")
            write_status(state)
        # heartbeat
        if time.time() - last_hb > 600:
            last_hb = time.time()
            nd = sum(1 for r in HEALTHY if done(r))
            lg(f"HEARTBEAT {nd}/18 done; running={list(running)}; queued={len(todo)}")
        time.sleep(20)
    lg("EVAL DRIVER 063 END")
    write_status(state)

if __name__ == "__main__":
    main()

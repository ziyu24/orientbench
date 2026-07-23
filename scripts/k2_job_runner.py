"""k2_job_runner.py <run_id> <head> <ds> <seed> <lr> <epochs> <stage> — run ONE K2 job.
4-GPU DDP train-with-policy (health gate + FP32 fallback + OOM 1200s retry + port bump), then if
stage=='final' and complete, run the instrumented eval. Writes per-run status json + gate csv.
Two of these run concurrently (both 4-GPU on CUDA_VISIBLE_DEVICES=0,1,2,3). No chat output.
"""
import os, sys, csv, json, time, subprocess
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/scripts")
import k2_driver_067 as K  # reuse launch(), terminal_nan(), final_ap50(), has_ckpt(), cfg_of(), etc.
ROOT = "/home/rspip/cqc/pro/study/orientbench"
EXT = f"{ROOT}/top_journal_v3_reaudit_055"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
JST = f"{REP}/k2_jobstatus"; os.makedirs(JST, exist_ok=True)
PY = K.PY; WDROOT = K.WDROOT; LOGD = K.LOGD; MAX_OOM = K.MAX_OOM; OOM_SLEEP = K.OOM_SLEEP

def run_policy(head, ds, seed, lr, epochs, rid):
    wd = f"{WDROOT}/{rid}"; log = f"{LOGD}/{rid}.log"
    gate = []
    if K.has_ckpt(wd, epochs):
        return "complete", K.final_ap50(log), "prev", gate
    import random
    port = 29800 + random.randint(0, 200)
    for amp_mode, fp32 in [("amp", False), ("fp32_fallback", True)]:
        oom = 0; addr = 0
        while True:
            port += 1
            st, ap = K.launch(head, ds, seed, lr, epochs, wd, rid, fp32, port)
            gate.append(dict(run_id=rid, amp_mode=amp_mode, status=st, ap50=ap,
                             decision=("kept" if st == "complete" else st)))
            if st == "complete":
                return "complete", ap, amp_mode, gate
            if st == "addrinuse" and addr < 20:
                addr += 1; port += 5; time.sleep(5); continue
            if st == "oom" and oom < MAX_OOM:
                oom += 1; time.sleep(OOM_SLEEP); continue
            break  # amp_incompat/nan/diverged/rc_fail -> next amp_mode (fp32)
    return "failed_training", None, "amp+fp32_exhausted", gate

def main():
    rid, head, ds, seed, lr, epochs, stage = sys.argv[1:8]
    seed = int(seed); lr = float(lr); epochs = int(epochs)
    st, ap, amp, gate = run_policy(head, ds, seed, lr, epochs, rid)
    wd = f"{WDROOT}/{rid}"; ck = f"{wd}/epoch_{epochs}.pth"
    eval_json = ""
    if stage == "final" and st == "complete" and os.path.isfile(ck):
        eval_json = f"{REP}/k2_eval/{rid}.json"
        if not os.path.isfile(eval_json):
            subprocess.call([PY, f"{EXT}/scripts/k2_eval_run.py", rid, K.cfg_of(head, ds), ck, head, ds],
                            env=dict(os.environ, CUDA_VISIBLE_DEVICES="0,1,2,3",
                                     PYTHONPATH=f"{EXT}:{os.environ.get('PYTHONPATH','')}"))
    rec = dict(run_id=rid, head=head, dataset=ds, seed=seed, lr=lr, epochs=epochs, stage=stage,
               status=st, final_ap50=ap, amp_mode=amp, checkpoint=(ck if os.path.isfile(ck) else ""),
               eval_json=(eval_json if eval_json and os.path.isfile(eval_json) else ""))
    with open(f"{JST}/{rid}.json", "w") as f:
        json.dump(rec, f, indent=2); f.flush()
    with open(f"{JST}/{rid}_gate.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "amp_mode", "status", "ap50", "decision"]); w.writeheader(); w.writerows(gate)

if __name__ == "__main__":
    main()

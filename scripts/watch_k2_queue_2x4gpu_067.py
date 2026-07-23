"""watch_k2_queue_2x4gpu_067.py — K2 scheduler: 2 concurrent jobs, each 4-GPU DDP (shared 0,1,2,3).
Dependency order: pilots(30) -> select LR -> final seed0(10)+eval -> seed0 gate -> seed1/2(20)+eval
-> aggregate + go/no-go. Each job = a k2_job_runner subprocess (internally 4-GPU torchrun with
health-gate/FP32-fallback/OOM retry). Resumable (skips jobs with a jobstatus json). No chat output.
"""
import os, sys, csv, json, time, subprocess, glob, hashlib
import numpy as np
ROOT = "/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
PY = "/home/rspip/anaconda3/envs/mr_dev1x/bin/python"
EXT = f"{ROOT}/top_journal_v3_reaudit_055"
REP = f"{EXT}/reports"; JST = f"{REP}/k2_jobstatus"; LOGD = f"{EXT}/logs/k2_angle_coder"
QLOG = f"{LOGD}/queue_067.log"; JOB = f"{ROOT}/scripts/k2_job_runner.py"
os.makedirs(JST, exist_ok=True); os.makedirs(f"{LOGD}/pilot", exist_ok=True)
HEADS = ["PSC", "CSL", "DCL", "direct_regression_le90", "KLD"]
DSS = ["DIOR-R", "SODA-A"]
LRS = [0.0025, 0.005, 0.010]
MAXC = 2; PILOT_EP = 3; FINAL_EP = 12; PILOT_LR = None

def lg(m): open(QLOG, "a").write(f"[{time.strftime('%F %T')}] {m}\n")
def jstatus(rid):
    p = f"{JST}/{rid}.json"
    if os.path.isfile(p):
        try: return json.load(open(p))
        except Exception: return None
    return None
def status_row(jobs, extra=""):
    rows = []
    for (rid, head, ds, seed, lr, ep, stage) in jobs:
        j = jstatus(rid)
        rows.append(dict(run_id=rid, head=head, dataset=ds, seed=seed, lr=lr, stage=stage,
                         status=(j["status"] if j else "queued"), final_ap50=(j["final_ap50"] if j else "")))
    with open(f"{REP}/k2_queue_status_067.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "head", "dataset", "seed", "lr", "stage", "status", "final_ap50"])
        w.writeheader(); w.writerows(rows)

def run_phase(jobs):
    """Run jobs with 2-concurrency; skip completed (jobstatus json exists)."""
    queue = [j for j in jobs if not jstatus(j[0])]
    running = {}
    while queue or running:
        while len(running) < MAXC and queue:
            rid, head, ds, seed, lr, ep, stage = queue.pop(0)
            p = subprocess.Popen([PY, JOB, rid, head, ds, str(seed), str(lr), str(ep), stage],
                                 stdout=open(f"{LOGD}/jobrunner_{rid}.out", "a"), stderr=subprocess.STDOUT)
            running[rid] = p; lg(f"LAUNCH job {rid} (concurrent={len(running)})")
        for rid, p in list(running.items()):
            if p.poll() is not None:
                del running[rid]; j = jstatus(rid)
                lg(f"DONE job {rid} -> {j['status'] if j else 'no-status'}")
        status_row(jobs); time.sleep(30)

def main():
    lg("K2 QUEUE 2x4gpu START")
    # ---- Phase 1: pilots ----
    pilots = [(f"K2_pilot__{h}__{d}__lr{lr}", h, d, 0, lr, PILOT_EP, "pilot")
              for h in HEADS for d in DSS for lr in LRS]
    run_phase(pilots)
    # pilot results + LR selection
    prows = []; sel = {}
    for h in HEADS:
        for d in DSS:
            cands = []
            for lr in LRS:
                j = jstatus(f"K2_pilot__{h}__{d}__lr{lr}")
                ap = j["final_ap50"] if (j and j["status"] == "complete") else None
                prows.append(dict(head=h, dataset=d, lr=lr, status=(j["status"] if j else "missing"),
                                  ap50=ap, amp_mode=(j["amp_mode"] if j else "")))
                if ap is not None: cands.append((lr, ap, j["amp_mode"]))
            sel[(h, d)] = max(cands, key=lambda x: x[1]) if cands else None
    with open(f"{REP}/k2_pilot_results_067.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["head", "dataset", "lr", "status", "ap50", "amp_mode"]); w.writeheader(); w.writerows(prows)
    with open(f"{REP}/k2_lr_selection_067.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["head", "dataset", "selected_lr", "pilot_ap50", "amp_mode", "note"])
        for (h, d), v in sel.items():
            w.writerow([h, d, v[0] if v else "", v[1] if v else "", v[2] if v else "", "" if v else "all pilots failed"])
    lg("PILOTS done; LR selected")
    # ---- Phase 2: final seed0 ----
    seed0 = []
    for h in HEADS:
        for d in DSS:
            if sel[(h, d)]:
                seed0.append((f"K2_final__{h}__{d}__seed0", h, d, 0, sel[(h, d)][0], FINAL_EP, "final"))
    run_phase(seed0)
    # seed0 gate
    grows = []; usable = {}
    for (rid, h, d, s, lr, ep, st) in seed0:
        j = jstatus(rid)
        ok = bool(j and j["status"] == "complete" and (j["final_ap50"] or 0) > 0)
        usable[(h, d)] = ok
        grows.append(dict(run_id=rid, head=h, dataset=d, seed0_status=(j["status"] if j else "missing"),
                          seed0_ap50=(j["final_ap50"] if j else ""), usable_convergence=ok))
    for h in HEADS:
        for d in DSS:
            if not sel[(h, d)]: usable[(h, d)] = False
    with open(f"{REP}/k2_seed0_gate_results_067.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "head", "dataset", "seed0_status", "seed0_ap50", "usable_convergence"])
        w.writeheader(); w.writerows(grows)
    lg("SEED0 done + gated")
    # ---- Phase 3: seed1/2 for usable heads ----
    s12 = []
    for h in HEADS:
        for d in DSS:
            if usable.get((h, d)) and sel[(h, d)]:
                for seed in (1, 2):
                    s12.append((f"K2_final__{h}__{d}__seed{seed}", h, d, seed, sel[(h, d)][0], FINAL_EP, "final"))
    run_phase(s12)
    lg("SEED1/2 done")
    # ---- persist seed_results + failed audit ----
    seed_rows = []; failed_rows = []
    for h in HEADS:
        for d in DSS:
            for seed in (0, 1, 2):
                rid = f"K2_final__{h}__{d}__seed{seed}"; j = jstatus(rid)
                if j is None:
                    if not sel[(h, d)]:
                        failed_rows.append(dict(run_id=rid, head=h, dataset=d, seed=seed, reason="all LR pilots failed"))
                    elif seed > 0 and not usable.get((h, d)):
                        failed_rows.append(dict(run_id=rid, head=h, dataset=d, seed=seed, reason="seed0 not usable -> seed1/2 skipped"))
                    continue
                seed_rows.append(dict(run_id=rid, head=h, dataset=d, seed=seed, lr=j["lr"], amp_mode=j["amp_mode"],
                                      final_ap50=j["final_ap50"], status=j["status"], eval_json=j.get("eval_json", "")))
                if j["status"] != "complete":
                    failed_rows.append(dict(run_id=rid, head=h, dataset=d, seed=seed, reason=f"{j['status']} after amp+fp32 budget"))
    with open(f"{REP}/k2_angle_coder_seed_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "head", "dataset", "seed", "lr", "amp_mode", "final_ap50", "status", "eval_json"]); w.writeheader(); w.writerows(seed_rows)
    with open(f"{REP}/k2_failed_training_audit.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "head", "dataset", "seed", "reason"]); w.writeheader(); w.writerows(failed_rows)
    # merged health-gate decisions
    allg = []
    for g in glob.glob(f"{JST}/*_gate.csv"):
        allg += list(csv.DictReader(open(g)))
    if allg:
        with open(f"{REP}/k2_health_gate_decisions_067.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["run_id", "amp_mode", "status", "ap50", "decision"]); w.writeheader(); w.writerows(allg)
    # ---- artifact manifest (sha) ----
    def sha(p):
        if not os.path.isfile(p): return ""
        h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()[:16]
    am = []
    for r in seed_rows:
        rid = r["run_id"]; wd = f"{EXT}/work_dirs/k2/{rid}"
        am.append(dict(run_id=rid, checkpoint=f"{wd}/epoch_{FINAL_EP}.pth", ckpt_sha=sha(f"{wd}/epoch_{FINAL_EP}.pth"),
                       log=f"{LOGD}/{rid}.log", log_sha=sha(f"{LOGD}/{rid}.log"),
                       eval_json=r["eval_json"], eval_sha=sha(r["eval_json"]) if r["eval_json"] else "",
                       evaluator="torch VOC-AP==DOTAMetric + instrumented native", can_recompute="yes"))
    with open(f"{REP}/k2_artifact_manifest_067.csv", "w", newline="") as f:
        if am:
            w = csv.DictWriter(f, fieldnames=list(am[0].keys())); w.writeheader(); w.writerows(am)
    # ---- aggregate + go/no-go ----
    subprocess.call([PY, f"{EXT}/scripts/k2_aggregate_go_no_go_067.py"],
                    env=dict(os.environ, PYTHONPATH=f"{EXT}:{os.environ.get('PYTHONPATH','')}"))
    lg("K2 QUEUE 2x4gpu END (go/no-go written)")

if __name__ == "__main__":
    main()

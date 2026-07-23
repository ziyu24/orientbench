"""m069_master.py — deterministic orchestrator for command 069. Runs tracks in dependency order,
each resumable (skip if sentinel output exists), heartbeat + status json. GPU steps are inference only.
No chat. Machine tasks only; human labeling remains external. Frozen thresholds/splits untouched.
"""
import os, sys, json, time, subprocess
ROOT = "/home/rspip/cqc/pro/study/orientbench"
PY = "/home/rspip/anaconda3/envs/mr_dev1x/bin/python"
SC = f"{ROOT}/scripts"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
LOGD = f"{ROOT}/top_journal_v3_reaudit_055/logs/m069"
os.makedirs(LOGD, exist_ok=True)
STATUS = f"{REP}/m069_master_status.json"
ENV = dict(os.environ, PYTHONPATH=f"{ROOT}/top_journal_v3_reaudit_055:{os.environ.get('PYTHONPATH','')}",
           OMP_NUM_THREADS="8")


def lg(m):
    open(f"{LOGD}/master.log", "a").write(f"[{time.strftime('%F %T')}] {m}\n"); print(m, flush=True)


def set_status(step, state, extra=None):
    d = {}
    if os.path.isfile(STATUS):
        try:
            d = json.load(open(STATUS))
        except Exception:
            d = {}
    d[step] = dict(state=state, t=time.strftime('%F %T'), **(extra or {}))
    json.dump(d, open(STATUS, "w"), indent=2)


def run(step, cmd, sentinel, gpu=False, best_effort=False):
    if sentinel and os.path.isfile(sentinel) and os.path.getsize(sentinel) > 0:
        lg(f"SKIP {step} (sentinel exists)"); set_status(step, "done_cached"); return True
    lg(f"START {step}: {' '.join(cmd)}")
    set_status(step, "running")
    env = dict(ENV)
    if gpu:
        env["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"
    out = open(f"{LOGD}/{step}.out", "a")
    rc = subprocess.call(cmd, stdout=out, stderr=subprocess.STDOUT, env=env, cwd=ROOT)
    ok = (rc == 0) and (not sentinel or os.path.isfile(sentinel))
    set_status(step, "done" if ok else ("failed_best_effort" if best_effort else "failed"), dict(rc=rc))
    lg(f"END {step} rc={rc} ok={ok}")
    return ok or best_effort


def main():
    lg("M069 MASTER START")
    # 1. geometry curve (idempotent)
    run("delta_theta", [PY, f"{SC}/derive_delta_theta_075.py"], f"{REP}/m4_delta_theta_075_frozen.json")
    # 2. human annotation tooling (machine deliverable; labels remain external)
    run("human_tooling", [PY, f"{SC}/build_m4_human_annotation.py"], f"{REP}/m4_human_annotation_sampling_manifest.csv")
    # 3. DOTA clean per-instance dump (GPU inference; best-effort so it never blocks CPU tracks)
    run("dota_dump_orcnn", [PY, f"{SC}/m_dota_dump.py", "orcnn"],
        f"{REP}/m_dota_clean_perinstance/DOTA_orcnn.jsonl", gpu=True, best_effort=True)
    run("dota_dump_rtmdet", [PY, f"{SC}/m_dota_dump.py", "rtmdet"],
        f"{REP}/m_dota_clean_perinstance/DOTA_rtmdet.jsonl", gpu=True, best_effort=True)
    # 4. M1 ar>=2.1 unification (depends on DOTA dumps if present)
    run("m1", [PY, f"{SC}/m1_ar21_unify.py"], f"{REP}/m1_all_main_results_ar21.csv")
    # 5-7. M2, M3, M4 (depend on M1 data availability; independent of each other)
    run("m2", [PY, f"{SC}/m2_g2doubleprime_ar21.py"], f"{REP}/m2_g2doubleprime_decision.csv")
    run("m3", [PY, f"{SC}/m3_image_level_risk.py"], f"{REP}/m3_decision.csv")
    run("m4", [PY, f"{SC}/m4_risk_events.py"], f"{REP}/m4_geometry_normalized_risk.csv")
    # 8. PSC Phase 1 split gate
    run("psc_phase1", [PY, f"{SC}/psc_phase1.py"], f"{REP}/psc_phase1_split_gate_decision.csv")
    # 9. human merge + analyze (pending until labels returned; always run, no sentinel)
    run("human_merge", [PY, f"{SC}/merge_m4_human_annotations.py"], None)
    run("human_analyze", [PY, f"{SC}/analyze_m4_human_disagreement.py"], None)
    # 10. reproduction consistency + freeze gate (always run last)
    run("freeze_repro", [PY, f"{SC}/m069_freeze_and_repro.py"], None)
    set_status("ALL", "complete")
    lg("M069 MASTER END")


if __name__ == "__main__":
    main()

"""020 env audit + unblock tests."""
import os, sys, json, csv
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
REP=os.path.join(_P,"outputs/bench_core/reports")

def test_env_audit_schema():
    rows=list(csv.DictReader(open(os.path.join(REP,"env_audit_020.csv")))); assert rows
    for r in rows:
        for c in ("family","existing_env","import_ok","config_build_ok","checkpoint_compatible","needs_create_env","blocker_reason"):
            assert c in r

def test_env_install_manifest_no_env_created():
    m=json.load(open(os.path.join(REP,"env_install_manifest_020.json")))
    assert m["envs_created"]==[]          # reuse-first satisfied
    assert m["packages_installed"]==[]    # no install
    assert "LSKNet(#7)" in m["unblocked_via_reuse"]

def test_unblocked_families_in_metrics():
    met=list(csv.DictReader(open(os.path.join(REP,"full_matrix_metrics_summary.csv"))))
    archs={m["archetype"] for m in met}
    assert {"lsknet_backbone","strip_rcnn","weakly_supervised_h2rbox"} <= archs

def test_blocked_env_reclassification():
    a={r["family"]:r for r in csv.DictReader(open(os.path.join(REP,"env_audit_020.csv")))}
    # unblocked
    for f in ("LSKNet","Strip_RCNN","h2rbox_v2"):
        assert "UNBLOCKED" in a[f]["blocker_reason"]
    # still blocked with specific reasons
    assert "download" in a["point2rbox_v2"]["blocker_reason"].lower()
    assert "0.1.0" in a["ARS-DETR"]["blocker_reason"]

def test_arsdetr_not_rhino_substitute():
    rows=list(csv.DictReader(open(os.path.join(REP,"full_matrix_execution_plan_020.csv"))))
    ars=[r for r in rows if r["archetype"]=="rotated_detr_arsdetr_distinct"]
    assert ars and all("NOT_rhino_substitute" in r["formal_capability"] for r in ars)
    rh=[r for r in rows if r["archetype"]=="rotated_detr_rhino"]
    assert rh and all(r["detector_family"]=="RHINO_host" for r in rh)

def test_gpu_policy_all_world_size_4_with_new_cells():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert len(gp["tasks"])>=6
    assert all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"])
    assert gp["oom_batch_lowering"] is False

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

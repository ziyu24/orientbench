"""019 full-matrix partial tests."""
import os, sys, json, csv, hashlib, subprocess
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
REP=os.path.join(_P,"outputs/bench_core/reports")

def _csv(f): return list(csv.DictReader(open(os.path.join(REP,f))))

def test_matrix_plan_schema():
    rows=_csv("full_matrix_execution_plan.csv"); assert rows
    valid={"already_available","ready_to_run","blocked_dependency_not_installed","blocked_missing_dataset",
           "weak_nonformal_blocked_dependency","not_applicable","blocked_oom","blocked_config_mismatch","unsupported_format"}
    for r in rows:
        assert r["status"] in valid
        for c in ("archetype","dataset","status","formal_scope"): assert c in r

def test_representative_detector_selection():
    rows=_csv("full_matrix_execution_plan.csv")
    # RHINO archetype must map to RHINO_host, never ARS-DETR
    rh=[r for r in rows if r["archetype"]=="rotated_detr_rhino"]
    assert rh and all(r["detector_family"]=="RHINO_host" for r in rh)
    ars=[r for r in rows if r["archetype"]=="rotated_detr_arsdetr_distinct"]
    assert ars and all("NOT_rhino_substitute" in r["formal_capability"] for r in ars)

def test_blocked_cell_handling():
    rows=_csv("full_matrix_execution_plan.csv")
    assert any(r["status"]=="blocked_dependency_not_installed" for r in rows)
    assert any(r["status"]=="blocked_missing_dataset" for r in rows)

def test_schema_validator_real_cells():
    rows=_csv("full_matrix_schema_validation.csv"); assert rows
    for r in rows:
        assert int(r["n_schema_ok"])>0
        assert r["is_synthetic_false"] in ("True","true")
        assert r["not_detector_output_false"] in ("True","true")

def test_converter_failure_does_not_stop_matrix():
    # failures file exists and is a list (matrix continued); metrics still produced
    assert os.path.isfile(os.path.join(REP,"full_matrix_failures.csv"))
    assert len(_csv("full_matrix_metrics_summary.csv"))>=5

def test_dota_formal_scope_guard():
    met=_csv("full_matrix_metrics_summary.csv")
    for m in met:
        if m["dataset"] in ("DOTA-v1.0","DOTA-v1.5"):
            assert "formal_compatible" in m["formal_scope"]

def test_non_dota_exploratory_guard():
    met=_csv("full_matrix_metrics_summary.csv")
    for m in met:
        if m["dataset"] not in ("DOTA-v1.0","DOTA-v1.5"):
            assert "exploratory" in m["formal_scope"]

def test_hrsc_angle_uncertain_guard():
    cov=json.load(open(os.path.join(REP,"full_project_coverage_report.json")))
    assert "HRSC" in cov["angle_blockers"]

def test_no_threshold_mutation_during_matrix():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"

def test_release_manifest_required_files():
    rel=os.path.join(_P,"outputs/releases/dota_scoped_milestone_v1")
    for f in ("RELEASE_NOTES.md","MANIFEST.json","SHA256SUMS.txt","thresholds.yaml.copy"):
        assert os.path.isfile(os.path.join(rel,f))

def test_gpu_policy_world_size_4():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert gp["tasks"] and all(t["world_size"]==4 and t["nproc_per_node"]==4 for t in gp["tasks"])

def test_batch_override_forbidden():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert gp["batch_override_anywhere"] is False
    assert all(t["batch_override"] is False for t in gp["tasks"])

def test_oom_does_not_lower_batch():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert gp["oom_batch_lowering"] is False

def test_verification_script_read_only():
    before=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    r=subprocess.run([sys.executable,os.path.join(_P,"scripts","91_verify_full_matrix_partial.py")],
                     capture_output=True,text=True)
    after=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert before==after and r.returncode==0

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

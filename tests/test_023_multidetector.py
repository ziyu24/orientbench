"""023 cross-dataset multi-detector tests."""
import os,sys,json,csv,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(_P,"outputs/bench_core/reports")
def _csv(f): return list(csv.DictReader(open(os.path.join(REP,f))))
VALID={"ready_to_run","already_available","blocked_no_checkpoint","blocked_no_config","blocked_dependency","blocked_oom","converter_failed","unsupported_dataset","weak_nonformal","not_applicable","blocked_config_mismatch"}
def test_multidetector_plan_schema():
    rows=_csv("cross_dataset_multidetector_plan_023.csv"); assert rows
    for r in rows: assert r["status"].split()[0] in VALID
def test_ready_or_available_executed():
    met=_csv("cross_dataset_metrics_023.csv")
    assert sum(1 for m in met if m["dataset"]=="DIOR-R")>=3  # multi-detector DIOR
def test_all_gpu_world_size_4():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert all(t["world_size"]==4 and t["nproc_per_node"]==4 for t in gp["tasks"])
def test_batch_override_forbidden():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert all(t["batch_override"] is False for t in gp["tasks"]) and gp["oom_batch_lowering"] is False
def test_schema_validation_new_cells():
    for s in _csv("cross_dataset_schema_validation_023.csv"): assert int(s["n_schema"])>0
def test_non_dota_exploratory_guard():
    for m in _csv("cross_dataset_metrics_023.csv"):
        assert "exploratory" in m["formal_scope"] and "formal_pass" not in m["formal_scope"]
def test_thresholds_unchanged():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_hrsc_angle_status_guard():
    m=[x for x in _csv("cross_dataset_metrics_023.csv") if x["dataset"]=="HRSC2016"]
    assert m and "uncertain" in m[0]["angle_status"]
def test_fullval_no_silent_truncation():
    fv=_csv("cross_dataset_fullval_status_023.csv")
    assert fv and all(r["reason"] and "subset" in r["used"].lower() for r in fv)
def test_no_032_c5_artifacts():
    # guard against the WRONG 032 (C5/source-teacher thread); project's own round-032 report files are legitimate
    assert not any("source_teacher" in f.lower() or "_c5" in f.lower() or "source-teacher" in f.lower() for f in os.listdir(REP))
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

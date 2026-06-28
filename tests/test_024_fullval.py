"""024 full-val + scratch storage tests."""
import os,sys,json,csv,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(_P,"outputs/bench_core/reports")
SCRATCH="/dev/shm/cqc/orientbench"
def _csv(f): return list(csv.DictReader(open(os.path.join(REP,f))))
def test_scratch_storage_policy():
    r=json.load(open(os.path.join(REP,"resource_startup_024.json")))
    assert r["scratch"]==SCRATCH and "SCRATCH" in r["storage_policy"]
def test_no_large_fullval_files_in_project():
    import subprocess
    out=subprocess.run(["bash","-c",f"find {_P}/outputs/predictions -name 'pred_*fullval*.jsonl' 2>/dev/null"],capture_output=True,text=True).stdout
    assert not out.strip()  # full-val schema must be in scratch only
def test_manifest_points_to_scratch():
    for ds,b in (("DIOR-R","3"),("FAIR1M-v1.0","5"),("SODA-A","4")):
        m=json.load(open(os.path.join(_P,"outputs/predictions",ds,b,"manifest.json")))
        assert m["raw_pkl_scratch"].startswith(SCRATCH) and m["schema_scratch"].startswith(SCRATCH)
        assert len(m["raw_pkl_sha256"])==64 and m["fullval"] is True
def test_env_network_unlock_schema():
    e=json.load(open(os.path.join(REP,"env_network_unlock_024.json")))
    assert "arsdetr" in e and "point2rbox" in e and e["new_envs_created"]==[]
def test_arsdetr_not_rhino_guard():
    e=json.load(open(os.path.join(REP,"env_network_unlock_024.json")))
    assert e["arsdetr"]["not_RHINO_replacement"] is True and e["arsdetr"]["independent_archetype"] is True
def test_point2rbox_weak_nonformal_guard():
    e=json.load(open(os.path.join(REP,"env_network_unlock_024.json")))
    assert e["point2rbox"]["weak_nonformal"] is True
def test_adapter_does_not_fake_class_head():
    e=json.load(open(os.path.join(REP,"env_network_unlock_024.json")))
    assert "no fake head" in e["lsknet_strip_cross_dataset"]["note"] or "not run" in e["lsknet_strip_cross_dataset"]["note"]
def test_gpu_world_size_4():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"])
def test_fullval_no_silent_subset():
    for ds in ("DIOR-R","FAIR1M-v1.0","SODA-A"):
        m=json.load(open(os.path.join(_P,"outputs/bench_core/gt_index",f"{ds}_fullval.meta.json")))
        assert m["fullval"] is True and m["not_fullval"] is False and m["n_images"]>500
def test_thresholds_unchanged():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_non_dota_exploratory_guard():
    for m in _csv("metrics_024.csv"):
        if m.get("n_used"): assert "exploratory" in m["formal_scope"]
def test_converter_failure_continues():
    assert os.path.isfile(os.path.join(REP,"failures_024.csv"))
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

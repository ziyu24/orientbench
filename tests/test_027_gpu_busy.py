"""027 GPU-busy replicate training tests."""
import os,sys,json,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(_P,"outputs/bench_core/reports")
def test_replicate_manifest_labels():
    m=json.load(open(os.path.join(_P,"outputs/training/027_replicate_training_manifest.json")))
    assert m["trained_by_027_replicate"] is True and m["not_original_readme_checkpoint"] is True
    assert m["not_formal_gate"] is True and m["exploratory_or_fallback"] is True
def test_replicate_no_param_change():
    m=json.load(open(os.path.join(_P,"outputs/training/027_replicate_training_manifest.json")))
    assert m["params_changed"] is False and m["batch_override"] is False and m["world_size"]==4
def test_replicate_workdir_scratch():
    m=json.load(open(os.path.join(_P,"outputs/training/027_replicate_training_manifest.json")))
    assert m["workdir"].startswith("/dev/shm")
def test_gpu_busy_report():
    t=open(os.path.join(REP,"gpu_busy_training_027.md")).read()
    assert "world_size=4" in t and "trained_by_027_replicate=true" in t
def test_thresholds_unchanged():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_gpu_world_size_4():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"])
def test_runtime_root_cause_documented():
    t=open(os.path.join(REP,"gpu_busy_training_027.md")).read()
    assert "nohup" in t and "bare" in t  # launch-method root cause for blocked_runtime
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

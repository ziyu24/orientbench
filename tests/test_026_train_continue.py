"""026 train-if-needed + continue tests."""
import os,sys,json,csv,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(_P,"outputs/bench_core/reports")
def _csv(f): return list(csv.DictReader(open(os.path.join(REP,f))))
def test_no_training_needed():
    m=json.load(open(os.path.join(_P,"outputs/training/026_training_manifest.json")))
    assert m["training_needed"] is False
def test_hrsc_angle_resolved():
    pr=open(os.path.join(REP,"hrsc_angle_proof_026.md")).read()
    assert "resolved_with_evidence" in pr and "mbox_ang" in pr and "0.906" in pr
def test_point2rbox_blocked_upstream():
    st={r["cell"]:r for r in _csv("cells_status_026.csv")}
    assert "blocked_upstream" in st["point2rbox"]["inference"]
def test_arsdetr_not_rhino():
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    assert a["not_RHINO_replacement"] is True and a["independent_archetype"] is True
def test_cross_dataset_blocked_runtime_documented():
    st={r["cell"]:r for r in _csv("cells_status_026.csv")}
    assert "blocked_runtime" in st["ARS-DETR cross-dataset"]["inference"]
    assert "OK" in st["Strip cross-dataset #47"]["ckpt_load"]  # ckpt-load proven, not fake head
def test_thresholds_unchanged():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_gpu_world_size_4():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"])
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

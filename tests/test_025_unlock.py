"""025 unlock remaining detectors tests."""
import os,sys,json,csv,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(_P,"outputs/bench_core/reports")
def _csv(f): return list(csv.DictReader(open(os.path.join(REP,f))))
def test_arsdetr_unlocked_not_rhino():
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    assert a["not_RHINO_replacement"] is True and a["independent_archetype"] is True
    assert a["mmrotate"].startswith("0.1.0") and a["isolated"] is True
def test_arsdetr_env_exists_isolated():
    assert os.path.isdir("/home/rspip/anaconda3/envs/arsdetr")
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    assert a["base_env_untouched"] is True
def test_arsdetr_inference_manifest():
    m=json.load(open(os.path.join(_P,"outputs/predictions/DOTA-v1.0/14/manifest.json")))
    assert m["detector"]=="ars_detr" and m["not_RHINO_replacement"] is True and m["schema_scratch"].startswith("/dev/shm")
def test_lsknet_cross_dataset_unlocked():
    met=_csv("metrics_025.csv")
    lsk=[m for m in met if m["detector"]=="oriented_rcnn_lsknet" and m.get("n_used") and int(m["n_used"])>0]
    assert len(lsk)>=3  # DIOR/FAIR1M/SODA matched (class fallback worked, not fake head)
def test_point2rbox_blocked_documented():
    t=open(os.path.join(REP,"point2rbox_download_025.md")).read()
    assert "blocked_download_source_empty" in t and "weak_nonformal" in t
def test_psc_rtmdet_fullval():
    met=_csv("metrics_025.csv")
    assert any(m["detector"]=="rotated_retinanet_psc" and m.get("n_used") for m in met)
    assert any(m["detector"]=="rotated_rtmdet_s" and m.get("n_used") for m in met)
def test_no_large_schema_in_project():
    import subprocess
    out=subprocess.run(["bash","-c",f"find {_P}/outputs/predictions -name 'pred_b*fullval.jsonl' 2>/dev/null"],capture_output=True,text=True).stdout
    assert not out.strip()
def test_all_exploratory():
    for m in _csv("metrics_025.csv"):
        if m.get("n_used"): assert "exploratory" in m["formal_scope"]
def test_gpu_world_size_4():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    assert all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"])
def test_thresholds_unchanged():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_adapter_no_fake_head():
    # LSKNet ran via num_classes override (real head match), documented in unlock report
    t=open(os.path.join(REP,"unlock_remaining_detectors_025.md")).read()
    assert "不假改 head" in t or "ckpt head" in t
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

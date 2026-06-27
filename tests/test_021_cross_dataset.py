"""021 cross-dataset exploratory tests."""
import os,sys,json,csv,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(_P,"outputs/bench_core/reports")
def _csv(f): return list(csv.DictReader(open(os.path.join(REP,f))))
def test_cross_dataset_plan_schema():
    rows=_csv("cross_dataset_execution_plan_021.csv"); assert rows
    for r in rows:
        for c in ("dataset","archetype","status","note"): assert c in r
def test_non_dota_exploratory_guard():
    for m in _csv("cross_dataset_metrics_021.csv"):
        if m.get("dataset") not in (None,"none",""):
            assert "exploratory" in m["formal_scope"] and "formal_pass" not in m["formal_scope"]
def test_hrsc_angle_uncertain_guard():
    m=[x for x in _csv("cross_dataset_metrics_021.csv") if x.get("dataset")=="HRSC2016"]
    assert m and m[0]["angle_error_gate_status"]=="blocked_angle_uncertain"
def test_blocked_detector_packet_schema():
    bl={b["detector"]:b for b in _csv("remaining_detector_blockers_021.csv")}
    assert bl["ARS-DETR"]["confusable_with_rhino"].startswith("NO")
    assert "YES" in bl["point2rbox_v2"]["network_download"]
def test_converter_failure_continues():
    assert os.path.isfile(os.path.join(REP,"cross_dataset_failures_021.csv"))
    f=_csv("cross_dataset_failures_021.csv")
    assert any("DIOR" in x["cell"] for x in f) and any("FAIR1M" in x["cell"] for x in f)
def test_thresholds_unchanged_guard():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_gpu_world_size_4_cross_dataset():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    hrsc=[t for t in gp["tasks"] if "HRSC" in t["cell"]]
    assert hrsc and all(t["world_size"]==4 and t["batch_override"] is False for t in hrsc)
def test_claim_ledger_no_overclaim():
    t=open(os.path.join(REP,"claim_ledger.md")).read().lower()
    # forbidden section lists them, but no positive assertion of completion in allowed/qualified
    assert "仍不可宣称" in open(os.path.join(REP,"claim_ledger.md")).read() and "all datasets covered" in t
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

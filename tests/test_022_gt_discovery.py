"""022 cross-dataset GT rediscovery + runs tests."""
import os,sys,json,csv,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP=os.path.join(_P,"outputs/bench_core/reports"); GTIDX=os.path.join(_P,"outputs/bench_core/gt_index")
def _csv(f): return list(csv.DictReader(open(os.path.join(REP,f))))
def test_dior_obb_discovery():
    rd={r["dataset"]:r for r in _csv("dataset_gt_rediscovery_022.csv")}
    assert "FOUND" in rd["DIOR-R"]["status"] and "xml" in rd["DIOR-R"]["format"].lower()
def test_fair1m_obb_discovery():
    rd={r["dataset"]:r for r in _csv("dataset_gt_rediscovery_022.csv")}
    assert "FOUND" in rd["FAIR1M-v1.0"]["status"]
def test_soda_present_inventory():
    rd={r["dataset"]:r for r in _csv("dataset_gt_rediscovery_022.csv")}
    assert "PRESENT" in rd["SODA-A"]["status"]
    s=_csv("soda_a_status_022.csv"); assert s and s[0]["present"] in ("True","true")
def test_empty_split_not_missing_gt():
    # rediscovery must explain WHY 021 was wrong (not just 'missing')
    rd={r["dataset"]:r for r in _csv("dataset_gt_rediscovery_022.csv")}
    for ds in ("DIOR-R","FAIR1M-v1.0","SODA-A"):
        assert rd[ds]["why_021_wrong"] and "missing" not in rd[ds]["status"].lower()
def test_gt_index_nonzero_guard():
    for ds in ("DIOR-R","FAIR1M-v1.0","SODA-A"):
        m=json.load(open(os.path.join(GTIDX,f"{ds}_val.meta.json")))
        assert m["n_obb_objects"]>0
def test_recursive_gt_discovery_schema():
    for r in _csv("gt_index_cross_dataset_022.csv"):
        for c in ("dataset","ann_dir","n_images","n_obb_objects","angle_version"): assert c in r
def test_cross_dataset_exploratory_guard():
    for m in _csv("cross_dataset_metrics_022.csv"):
        assert "exploratory" in m["formal_scope"] and "formal_pass" not in m["formal_scope"]
def test_gpu_world_size_4():
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    xds=[t for t in gp["tasks"] if any(d in t["cell"] for d in ("DIOR","FAIR1M","SODA","HRSC"))]
    assert xds and all(t["world_size"]==4 and t["batch_override"] is False for t in xds)
def test_thresholds_unchanged():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_hrsc_angle_uncertain_isolated():
    # HRSC angle uncertain present but other datasets still ran
    met=_csv("cross_dataset_metrics_022.csv")
    ds={m["dataset"] for m in met}
    assert {"DIOR-R","FAIR1M-v1.0","SODA-A"} <= ds  # others ran despite HRSC uncertainty
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

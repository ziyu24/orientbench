"""013 host training/integration tests (no GPU needed)."""
import os, sys, json, yaml
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
from orientbench.reports.training_readiness import build_training_readiness
from orientbench.data.splits import assign_split

def test_d6_grants_host_scope_training():
    res=build_training_readiness(os.path.join(_P,"outputs","bench_core"), os.path.join(_P,"configs"))
    assert res["training_allowed"]=="true_for_approved_host_scope"
    assert res["formal_gate_allowed"] is False

def test_host_manifests_resumable():
    for k in ("rhino","a4_host"):
        m=os.path.join(_P,"outputs","training",k,"manifest.json")
        if not os.path.isfile(m): continue
        d=json.load(open(m))
        assert "config_sha256" in d and "epochs" in d
        assert d.get("world_size")==4 and d.get("gpu_ids")==[0,1,2,3]
        assert d.get("formal_eligible") is True and d.get("effective_global_batch")

def test_host_routing_no_mix():
    p=os.path.join(_P,"outputs","bench_core","reports","post_training_pipeline_status.json")
    if not os.path.isfile(p): return
    d=json.load(open(p))
    assert "RHINO->C1/B" in d["host_routing"] and "O2-RTDETR->A4" in d["host_routing"]
    for h in d["hosts"]:
        assert (h["host"]=="RHINO")==(h["route"]=="C1/B")

def test_a4_snapshot_rule_no_daudit():
    m=os.path.join(_P,"outputs","training","a4_host","manifest.json")
    if not os.path.isfile(m): return
    d=json.load(open(m))
    assert "D_audit NOT consulted" in d.get("a4_snapshot_rule","")

def test_dcal_daudit_disjoint():
    imgs=[f"i{n:04d}" for n in range(300)]
    cal={i for i in imgs if assign_split(i)=="D_cal"}; aud={i for i in imgs if assign_split(i)=="D_audit"}
    assert cal&aud==set()

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

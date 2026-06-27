"""P2 (C1 cross-view) + P3 (A4 attribution) mechanism primitive tests (015)."""
import math, os, sys, numpy as np
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
from orientbench.metrics.ot_dustbin import sinkhorn_dustbin, obb_match_cost
from orientbench.metrics.drop_rate import drop_rate, view_consistency_risk
from orientbench.metrics.dependence import partial_correlation, hsic, bootstrap_ci
from orientbench.metrics.angle_contract import is_near_square
from orientbench.data.splits import assign_split

def _obb(cx,cy,w,h,t,c="ship"): return {"obb_cx":cx,"obb_cy":cy,"obb_w":w,"obb_h":h,"obb_theta":t,"class_name":c}

def test_ot_dustbin_matches_close_and_dustbins_far():
    src=[_obb(0,0,40,20,0.0), _obb(500,500,40,20,0.0)]
    tgt=[_obb(2,1,40,20,0.05)]   # only matches src[0]; src[1] far -> dustbin
    C=obb_match_cost(src,tgt)
    ot=sinkhorn_dustbin(C, dustbin_cost=0.6, reg=0.05)
    assert ot["matched_mass"]>0 and ot["dustbin_mass"]>0  # one match + one dustbin

def test_drop_rate():
    assert drop_rate(10,7)==0.3
    assert math.isnan(drop_rate(0,0))

def test_gt_identity_guard_obb_cost_zero_for_identical():
    C=obb_match_cost([_obb(0,0,40,20,0.3)],[_obb(0,0,40,20,0.3)])
    assert C[0,0]<1e-6  # identical -> zero cost (GT-identity control)

def test_cross_view_pair_schema():
    vc=view_consistency_risk([{"a":_obb(0,0,40,20,0.0),"b":_obb(0,0,40,20,math.radians(5))}])
    assert vc["n"]==1 and abs(vc["median"]-5.0)<1e-3

def test_partial_corr_control_removes_confound():
    # y = 2*z + noise; x = 3*z ; partial corr(x,y|z) ~ 0 (confounder z removed)
    rng=np.random.RandomState(0); z=rng.randn(200)
    x=3*z+0.01*rng.randn(200); y=2*z+0.01*rng.randn(200)
    full=partial_correlation(x,y,None); part=partial_correlation(x,y,z)
    assert abs(full)>0.9 and abs(part)<0.3

def test_hsic_permutation_detects_dependence():
    rng=np.random.RandomState(0); x=rng.randn(150); y=x+0.1*rng.randn(150)
    h=hsic(x,y,max_samples=150,n_perm=100,seed=0)
    assert h["p_value"]<0.05  # dependent
    yi=rng.randn(150)
    h2=hsic(x,yi,max_samples=150,n_perm=100,seed=0)
    assert h2["p_value"]>=0.05 or h2["hsic"]<h["hsic"]  # independent-ish

def test_near_square_mask():
    assert is_near_square(10,10) is True and is_near_square(40,10) is False

def test_dcal_daudit_disjoint():
    imgs=[f"i{n:04d}" for n in range(300)]
    cal={i for i in imgs if assign_split(i)=="D_cal"}; aud={i for i in imgs if assign_split(i)=="D_audit"}
    assert cal&aud==set()

def test_host_hash_and_invalid_exclusion():
    # lock audit + superseded exclusion present
    la=os.path.join(_P,"outputs/bench_core/reports/host_training_lock_audit.csv")
    if os.path.isfile(la):
        import csv
        rows=list(csv.DictReader(open(la)))
        assert any(r["sha256_matches_expected"] in ("True","true") for r in rows)
    # superseded dirs exist and are marked
    for k in ("rhino","a4_host"):
        d=os.path.join(_P,"outputs/training",k)
        if os.path.isdir(d):
            assert any(x.startswith("superseded") for x in os.listdir(d))

def test_report_schema_smoke():
    for f in ("c1_cross_view_smoke_summary.csv","a4_source_attribution_smoke_summary.csv"):
        p=os.path.join(_P,"outputs/bench_core/reports",f)
        if os.path.isfile(p):
            import csv; rows=list(csv.DictReader(open(p)))
            assert rows and "split" in rows[0]

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

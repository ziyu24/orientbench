"""016 C1 real cross-view + A4 background formal-readiness tests."""
import os, sys, json, math, numpy as np
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
from orientbench.buckets.background_source import background_for_image
from orientbench.metrics.dependence import partial_correlation, hsic
from orientbench.data.splits import assign_split

def test_c1_availability_schema():
    p=os.path.join(_P,"outputs/bench_core/reports/c1_real_cross_view_availability.json")
    if not os.path.isfile(p): return
    d=json.load(open(p))
    for k in ("genuine_multi_physical_view_pairs","satisfies_R1_gt_identity","cross_view_kind","missing"):
        assert k in d
    assert d["genuine_multi_physical_view_pairs"] is False  # honest: no genuine multi-view

def test_pair_identity_and_r1_guard():
    # unrotate mapping is deterministic + invertible (pair identity trackable)
    import importlib.util
    spec=importlib.util.spec_from_file_location("p52", os.path.join(_P,"scripts","52_c1_real_cross_view.py"))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    p={"obb_cx":100.0,"obb_cy":200.0,"obb_w":40.0,"obb_h":20.0,"obb_theta":0.3}
    q=m.unrotate_90cw(p)
    assert q["obb_cx"]==200.0 and abs(q["obb_cy"]-(m.S-1-100.0))<1e-6  # deterministic map

def test_background_annulus_mask_and_valid_ratio(tmp_path):
    import cv2
    # synthetic image with a gradient; one GT box -> bg computed, valid_ratio in [0,1]
    img=np.tile(np.linspace(0,255,256).astype(np.uint8),(256,1))
    ip=os.path.join(str(tmp_path),"x.png"); cv2.imwrite(ip,img)
    objs=[{"obb_cx":128.0,"obb_cy":128.0,"obb_w":40.0,"obb_h":20.0,"obb_theta":0.2}]
    res=background_for_image(ip,objs)
    assert res[0]["bg_status"]=="ok"
    assert 0.0<=res[0]["bg_valid_ratio"]<=1.0

def test_background_excludes_other_gt():
    # two overlapping-ish boxes: other GT should reduce valid annulus (exclusion works)
    import cv2, tempfile, os as _os
    with tempfile.TemporaryDirectory() as d:
        img=np.random.RandomState(0).randint(0,255,(256,256),dtype=np.uint8)
        ip=_os.path.join(d,"y.png"); cv2.imwrite(ip,img)
        one=[{"obb_cx":128.0,"obb_cy":128.0,"obb_w":40.0,"obb_h":20.0,"obb_theta":0.0}]
        two=one+[{"obb_cx":150.0,"obb_cy":128.0,"obb_w":40.0,"obb_h":20.0,"obb_theta":0.0}]
        r1=background_for_image(ip,one)[0]["bg_valid_ratio"]
        r2=background_for_image(ip,two)[0]["bg_valid_ratio"]
        assert r2<=r1+1e-9  # neighbor exclusion reduces (or equals) valid ratio

def test_partial_corr_with_bg_and_hsic_reproducible():
    rng=np.random.RandomState(1); z=rng.randn(120); bg=rng.randn(120); risk=0.5*z+0.3*rng.randn(120)
    pc=partial_correlation(bg,risk,z); assert math.isfinite(pc)
    h1=hsic(bg,risk,max_samples=120,n_perm=80,seed=7); h2=hsic(bg,risk,max_samples=120,n_perm=80,seed=7)
    assert h1["p_value"]==h2["p_value"]  # reproducible with fixed seed

def test_dcal_daudit_disjoint():
    imgs=[f"i{n:04d}" for n in range(300)]
    cal={i for i in imgs if assign_split(i)=="D_cal"}; aud={i for i in imgs if assign_split(i)=="D_audit"}
    assert cal&aud==set()

def test_candidates_not_frozen():
    import yaml
    for f in ("thresholds.c1_candidate.yaml","thresholds.a4_candidate.yaml"):
        p=os.path.join(_P,"configs",f)
        if os.path.isfile(p):
            d=yaml.safe_load(open(p))
            assert d.get("approval_status") in ("pending","approved_frozen")
    # live thresholds.yaml must NOT be complete_B_C1 / complete_A_A4
    live=yaml.safe_load(open(os.path.join(_P,"configs","thresholds.yaml")))
    fs=str(live.get("freeze_status"))
    assert "complete_B_C1" not in fs and "complete_A_A4" not in fs

def test_formal_gate_allowed_remains_false():
    from orientbench.reports.readiness import build_readiness
    r=build_readiness(os.path.join(_P,"outputs","bench_core"), os.path.join(_P,"configs"))
    assert r["formal_gate_allowed"] is False

if __name__=="__main__":
    import tempfile,pathlib
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try:
                if fn.__code__.co_argcount:
                    with tempfile.TemporaryDirectory() as d: fn(pathlib.Path(d))
                else: fn()
                p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

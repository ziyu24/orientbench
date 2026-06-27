"""Regression tests for the OBB angle contract (012 task 1)."""
import math, os, sys, json
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
from orientbench.metrics.angle_contract import (angle_error_contract, orientation_risk_deg,
    is_near_square, normalize_orientation, METRIC_VERSION, NORMALIZATION_VERSION)
HP=math.pi/2

def test_equivalent_polygon_swap_zero():
    # (w,h,theta) vs (h,w,theta+90) = same rectangle -> canonical ~0, raw ~90
    c=angle_error_contract(40,20,0.3, 20,40,0.3+HP)
    assert c["angle_error_canonical_longside"]<1e-3
    assert c["angle_error_raw_le90"]>80

def test_genuine_30deg_not_collapsed():
    # real 30deg orientation difference must NOT be squashed to 0
    c=angle_error_contract(40,20,0.0, 40,20,math.radians(30))
    assert abs(c["angle_error_canonical_longside"]-30.0)<1e-3

def test_rotate_90_of_elongated_is_real_difference():
    # 40x20 at 0deg (long axis horizontal) vs 90deg (vertical) are perpendicular
    # -> canonical error ~90deg (NOT collapsed to 0; proves real diffs preserved).
    c=angle_error_contract(40,20,0.0, 40,20,HP)
    assert abs(c["angle_error_canonical_longside"]-90.0)<1e-3

def test_near_square_flagged():
    assert is_near_square(10,10) is True
    assert is_near_square(40,10) is False
    c=angle_error_contract(10.0,10.0,0.0, 10.0,10.0,1.0)
    assert c["near_square"] is True

def test_boundary_angle_pi_period():
    c=angle_error_contract(40,20,math.radians(89), 40,20,math.radians(-89))
    # 89 and -89 long-side differ by 2deg (pi-periodic), not 178
    assert c["angle_error_canonical_longside"]<3.0

def test_degenerate_nonfinite():
    c=angle_error_contract(0,10,0.0, 40,20,0.0)
    assert math.isnan(c["angle_error_canonical_longside"])

def test_versions_present():
    c=angle_error_contract(40,20,0.1, 40,20,0.1)
    assert c["metric_version"]==METRIC_VERSION
    assert c["normalization_version"]==NORMALIZATION_VERSION

def test_real_sample_sanity():
    # if real b1 schema exists, sample-check that canonical orientation risk is finite & small-ish vs GT not required here
    p="outputs/predictions/DOTA-v1.0/1/schema/pred_b1_dcal.jsonl"
    if not os.path.isfile(p): return
    rec=json.loads(open(p).readline())
    no=normalize_orientation(rec["obb_w"],rec["obb_h"],rec["obb_theta"])
    assert math.isfinite(no["canonical_theta"])

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

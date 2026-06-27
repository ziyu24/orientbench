"""Tests for long-side canonical orientation error (011 angle convention fix)."""
import math, os, sys
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_P)
from orientbench.core.geometry import canonical_longside_theta
from orientbench.metrics.angle import orientation_angle_error_deg, orientation_angle_error_rad

HP=math.pi/2

def test_canonical_longside_swap_invariant():
    # (w,h,theta) and (h,w,theta+90) are the SAME box -> same canonical orientation
    a=canonical_longside_theta(40,20,0.3)
    b=canonical_longside_theta(20,40,0.3+HP)
    assert abs(((a-b+HP)%math.pi)-HP)<1e-6

def test_orientation_error_zero_for_swapped_representation():
    # detector labels long side as w@theta; GT labels it as h@(theta+90) -> error ~0
    e=orientation_angle_error_deg(40,20,0.3, 20,40,0.3+HP)
    assert e<1e-3

def test_orientation_error_real_difference():
    # genuine 30deg orientation difference (both long-side w) -> ~30deg
    e=orientation_angle_error_deg(40,20,0.0, 40,20,math.radians(30))
    assert abs(e-30.0)<1e-3

def test_canonical_nan_safe():
    assert math.isnan(canonical_longside_theta(0,0,float('nan')))

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

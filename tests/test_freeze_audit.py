"""Tests for threshold freeze + D_audit leak guard + host identity (012)."""
import os, sys, yaml, json
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
from orientbench.data.splits import assign_split

CFG=os.path.join(_P,"configs","thresholds.yaml")
REP=os.path.join(_P,"outputs","bench_core","reports")

def test_thresholds_frozen_dota_with_metadata():
    t=yaml.safe_load(open(CFG))
    assert str(t["freeze_status"]).startswith("partial_frozen_dota_d2")
    assert t["freeze_time"]
    assert t["calibration_split"]=="D_cal"
    assert t["D2"]["status"]=="frozen"
    assert t["D2"]["per_detector_nrc_auc_pass_max"]==1.0
    assert t["data_fingerprint"] and t["code_fingerprint"]
    # hosts frozen as orientation gates after 014 training
    assert t["B_C1"]["status"] in ("pending_host","frozen_host_orientation_gate","frozen")
    assert t["A_A4"]["status"] in ("pending_host","frozen_host_orientation_gate","frozen")

def test_dcal_daudit_disjoint_for_audit():
    # the audit split function must be deterministic & partition images
    imgs=[f"img_{i:04d}" for i in range(500)]
    cal={i for i in imgs if assign_split(i)=="D_cal"}
    aud={i for i in imgs if assign_split(i)=="D_audit"}
    assert cal&aud==set()
    assert cal|aud==set(imgs)

def test_audit_report_is_partial_scope():
    p=os.path.join(REP,"dota_formal_audit.md")
    if not os.path.isfile(p): return
    s=open(p).read()
    assert "PARTIAL" in s or "partial" in s
    assert "9-detector" in s  # explicitly disclaims full 9-detector
    # must not claim full-dataset formal pass
    assert "全数据集" not in s.replace("非全数据集","")

def test_host_identity_no_arsdetr_as_rhino():
    p=os.path.join(REP,"host_identity_audit.md")
    if not os.path.isfile(p): return
    s=open(p)
    s=open(p).read()
    assert "RHINO" in s and "rotated_rtdetr" in s
    assert "非 ARS-DETR" in s or "不伪装" in s

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

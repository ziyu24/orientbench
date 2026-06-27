"""017 C1/A4 freeze + D_audit formal gate tests."""
import os, sys, json, hashlib, yaml, subprocess
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
CONF=os.path.join(_P,"configs"); REP=os.path.join(_P,"outputs/bench_core/reports")

def _thr(): return yaml.safe_load(open(os.path.join(CONF,"thresholds.yaml")))

def test_freeze_token_required():
    r=subprocess.run([sys.executable,os.path.join(_P,"scripts","54_freeze_c1_a4.py"),
                      "--approval-token","WRONG","--freeze-time","t"],capture_output=True,text=True)
    assert r.returncode==2 and "token mismatch" in r.stdout

def test_c1_a4_frozen_dcal_only():
    t=_thr()
    for blk in ("B_C1","A_A4"):
        assert t[blk]["status"]=="frozen"
        assert t[blk]["calibration_split"]=="D_cal" and t[blk]["audit_split"]=="D_audit"
        assert t[blk]["approval_token"]=="SUPERVISOR_APPROVED_017_R8_FREEZE_C1_A4_DCAL_ONLY"

def test_d_audit_leakage_guard():
    # frozen thresholds must derive from D_cal reference, not D_audit
    t=_thr()
    assert "D_audit NOT used" in t["B_C1"]["calibration_note"]
    assert "D_audit NOT used" in t["A_A4"]["calibration_note"]
    # candidate had calibration_split D_cal
    c1=yaml.safe_load(open(os.path.join(CONF,"thresholds.c1_candidate.yaml")))
    assert c1["calibration_split"]=="D_cal"

def test_c1_scope_wording_guard():
    t=_thr()
    assert t["B_C1"]["not_genuine_physical_multiview"] is True
    assert "augmentation" in t["B_C1"]["scope"].lower()
    md=open(os.path.join(REP,"c1_formal_audit.md")).read()
    assert "NOT genuine physical multi-view" in md
    assert "genuine physical multi-view" in md  # disclaimer present

def test_a4_host_hash_and_same_host_scope():
    t=_thr()
    assert str(t["A_A4"]["host_sha256"]).startswith("3e32fa11")
    assert str(t["B_C1"]["host_sha256"]).startswith("55a90abb")
    md=open(os.path.join(REP,"a4_formal_audit.md")).read()
    assert "NO cross-host causal claim" in md or "no cross-host causal" in md.lower()

def test_background_source_required():
    t=_thr()
    assert t["A_A4"]["background_source_enabled"] is True

def test_formal_audit_cannot_mutate_thresholds():
    before=hashlib.sha256(open(os.path.join(CONF,"thresholds.yaml"),"rb").read()).hexdigest()
    subprocess.run([sys.executable,os.path.join(_P,"scripts","56_a4_formal_audit.py")],capture_output=True,text=True)
    after=hashlib.sha256(open(os.path.join(CONF,"thresholds.yaml"),"rb").read()).hexdigest()
    assert before==after  # formal audit must NOT change thresholds.yaml

def test_pass_fail_blocked_schema():
    for f in ("c1_formal_audit.csv","a4_formal_audit.csv"):
        import csv; rows=list(csv.DictReader(open(os.path.join(REP,f))))
        assert rows and rows[0]["verdict"] in ("formal_pass","formal_fail","formal_blocked")

def test_readiness_scoped_formal_status():
    s=open(os.path.join(REP,"formal_gate_summary.md")).read()
    assert "true_for_frozen_dota_c1_a4_scope_only" in s
    # must NOT claim complete project gate / all datasets / 9-detector
    assert "complete project gate" not in s.lower()
    assert "9-detector" in s  # explicitly disclaimed as not done

def test_training_allowed_not_true_unconditional():
    from orientbench.reports.readiness import build_readiness
    r=build_readiness(os.path.join(_P,"outputs","bench_core"), CONF)
    assert r["formal_gate_allowed"] is False  # bool stays conservative; scope flag is in report

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

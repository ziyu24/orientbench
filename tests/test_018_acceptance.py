"""018 acceptance package + verification tests."""
import os, sys, json, csv, subprocess
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,_P)
REP=os.path.join(_P,"outputs/bench_core/reports")

def test_project_status_matrix_schema():
    rows=list(csv.DictReader(open(os.path.join(REP,"project_status_matrix.csv"))))
    assert rows
    for r in rows:
        for c in ("module","status","scope","evidence_path","blocking_reason","next_required_action"):
            assert c in r
        assert r["status"] in ("pass","partial_pass","blocked","not_started","out_of_scope_current")

def test_claim_ledger_forbidden_claims():
    rows=list(csv.DictReader(open(os.path.join(REP,"claim_ledger.csv"))))
    classes={r["class"] for r in rows}
    assert {"allowed","qualified","forbidden"} <= classes
    forb=[r["claim"] for r in rows if r["class"]=="forbidden"]
    assert any("full benchmark complete" in c for c in forb)
    assert any("ARS-DETR substituted RHINO" in c for c in forb)

def test_milestone_acceptance_scope_wording():
    md=open(os.path.join(REP,"dota_scoped_milestone_acceptance.md")).read()
    assert "PASS within frozen DOTA scope" in md
    assert "禁止外推" in md or "NO EXTRAPOLATION" in md
    assert "genuine physical multi-view" in md  # disclaimer present

def test_reproducibility_manifest_required_hashes():
    m=json.load(open(os.path.join(REP,"reproducibility_manifest.json")))
    assert m["rhino_ckpt"]["sha256"].startswith("55a90abb")
    assert m["a4_ckpt"]["sha256"].startswith("3e32fa11")
    assert m["thresholds_yaml_sha256"]
    assert m["secrets"]=="none included; paths+hashes only" or "none" in m["secrets"]

def test_verification_script_read_only():
    # running verification must NOT change thresholds.yaml
    import hashlib
    tp=os.path.join(_P,"configs/thresholds.yaml")
    before=hashlib.sha256(open(tp,"rb").read()).hexdigest()
    r=subprocess.run([sys.executable,os.path.join(_P,"scripts","90_verify_dota_scoped_milestone.py")],
                     capture_output=True,text=True)
    after=hashlib.sha256(open(tp,"rb").read()).hexdigest()
    assert before==after and r.returncode==0

def test_scoped_formal_true_overall_false():
    d=json.load(open(os.path.join(REP,"verification_dota_scoped_milestone.json")))
    assert d["scoped_formal_gate_allowed"]=="true_for_frozen_dota_c1_a4_scope_only"
    assert d["overall_project_complete"] is False
    assert d["verdict"]=="VERIFIED"

def test_training_needed_now_false():
    d=json.load(open(os.path.join(REP,"verification_dota_scoped_milestone.json")))
    assert d["training_needed_now"] is False
    rc=open(os.path.join(REP,"readiness_check.md")).read()
    assert "no_new_training_required_for_current_scope" in rc

def test_dota_scope_not_expanded():
    # forbidden assertions must not appear in scanned formal reports
    d=json.load(open(os.path.join(REP,"verification_dota_scoped_milestone.json")))
    nf=[c for c in d["checks"] if c["check"]=="no_forbidden_assertions"]
    assert nf and nf[0]["ok"] is True

if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

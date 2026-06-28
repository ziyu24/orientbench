"""029 full-matrix finish tests."""
import os,sys,json,csv,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(_P,"outputs/bench_core/reports")
def test_final_matrix_multidataset():
    rows=list(csv.DictReader(open(os.path.join(REP,"final_matrix_summary.csv"))))
    ds=set(r["dataset"] for r in rows)
    assert len(rows)>=15 and len(ds)>=5
def test_non_dota_exploratory():
    for r in csv.DictReader(open(os.path.join(REP,"final_matrix_summary.csv"))):
        if r["dataset"] not in ("DOTA-v1.0","DOTA-v1.5"):
            assert "exploratory" in r["scope"]
def test_full_project_not_complete():
    cov=json.load(open(os.path.join(REP,"full_project_coverage_report.json")))
    assert cov["final_matrix"]["full_project_complete"] is False
def test_remaining_blockers_documented():
    bl=list(csv.DictReader(open(os.path.join(REP,"remaining_blockers.csv"))))
    assert any("Strip" in b["item"] for b in bl) and any("point2rbox" in b["item"] for b in bl)
def test_no_large_files_in_project():
    import subprocess
    out=subprocess.run(["bash","-c",f"find {_P}/outputs/predictions -name 'pred_b*.jsonl' -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    assert not out.strip()
def test_arsdetr_not_rhino():
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    assert a["not_RHINO_replacement"] is True
def test_thresholds_unchanged():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_no_forbidden_overclaim():
    t=open(os.path.join(REP,"final_matrix_summary.md")).read().lower()
    for ph in ("full project complete","9-detector matrix complete","all datasets covered"):
        assert ph not in t
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

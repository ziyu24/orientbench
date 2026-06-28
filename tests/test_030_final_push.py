"""030 final push tests."""
import os,sys,json,csv,hashlib
_P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(_P,"outputs/bench_core/reports")
def test_strip_dior_unblocked():
    rows=list(csv.DictReader(open(os.path.join(REP,"final_matrix_summary.csv"))))
    assert any(r["detector"]=="strip_rcnn" and r["dataset"]=="DIOR-R" for r in rows)
    assert os.path.isfile(os.path.join(_P,"outputs/predictions/DIOR-R/47/manifest.json"))
def test_point2rbox_final_blocked():
    t=open(os.path.join(REP,"final_blocker_evidence_030.md")).read()
    assert "blocked_upstream_artifact_unavailable_final" in t
def test_non_dota_exploratory():
    for r in csv.DictReader(open(os.path.join(REP,"final_matrix_summary.csv"))):
        if r["dataset"] not in ("DOTA-v1.0","DOTA-v1.5"): assert "exploratory" in r["scope"]
def test_thresholds_unchanged():
    cur=hashlib.sha256(open(os.path.join(_P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    assert cur=="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def test_docs_report_exists():
    assert os.path.isfile(os.path.join(_P,"docs/cc_latest_report.md"))
def test_no_large_in_project():
    import subprocess
    out=subprocess.run(["bash","-c",f"find {_P}/outputs/predictions -name 'pred_*.jsonl' -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    assert not out.strip()
def test_arsdetr_not_rhino():
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    assert a["not_RHINO_replacement"] is True
if __name__=="__main__":
    p=f=0
    for n,fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            try: fn(); p+=1; print("PASS",n)
            except Exception as e: f+=1; print("FAIL",n,e)
    print(f"{p} passed {f} failed"); raise SystemExit(1 if f else 0)

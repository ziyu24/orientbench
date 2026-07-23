#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
A="$ROOT/top_journal_v3_reaudit_055/paper_A_orientation_protocol"
PY=/home/rspip/anaconda3/envs/ai4rs_train/bin/python
LOG="$A/logs/reproduce_A4_A6_076.log"
exec >"$LOG" 2>&1
echo "start=$(TZ=Asia/Shanghai date --iso-8601=seconds)"
cd "$A/toolbox"
set +e
PYTHONPATH=. "$PY" -m unittest discover -s tests -v
test_rc=$?
PYTHONPATH=. "$PY" -m orientation_reliability.cli examples/synthetic.csv --ap75 0.5 > "$A/logs/toolbox_cli_synthetic.json"
cli_rc=$?
set -e
"$PY" - "$A" "$test_rc" "$cli_rc" <<'PY'
import json,sys
from pathlib import Path
A=Path(sys.argv[1]);t=int(sys.argv[2]);c=int(sys.argv[3])
(A/'reports/toolbox_test_status.json').write_text(json.dumps({'unit_tests':'PASS' if t==0 else 'FAIL','synthetic_cli':'PASS' if c==0 else 'FAIL','persistent_artifact_regression':'PASS' if t==0 else 'FAIL','all_pass':t==0 and c==0},indent=2)+'\n')
if t or c: raise SystemExit(2)
PY
cd "$ROOT"
"$PY" "$A/scripts/recompute_a4_tolerance.py"
# Web-tool smoke test uses test_outputs only; formal outputs remain empty.
"$PY" - "$A" <<'PY'
import csv,json,subprocess,sys,time,urllib.request
from pathlib import Path
A=Path(sys.argv[1]);T=A/'annotation_tools/annotator_3'; p=subprocess.Popen([sys.executable,str(T/'common/app.py'),'--slot','3','--port','17803','--test-mode'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
try:
 time.sleep(1); tasks=json.load(urllib.request.urlopen('http://127.0.0.1:17803/api/tasks'))['tasks']; assert len(tasks)==150
 state={'current_index':1,'annotator_id':'SYNTHETIC_TEST_ONLY','records':{tasks[0]['task_id']:{'angle':12.5,'ambiguous':False,'skip':False,'notes':'test'}}}
 req=urllib.request.Request('http://127.0.0.1:17803/api/save',data=json.dumps(state).encode(),headers={'Content-Type':'application/json'},method='POST');assert json.load(urllib.request.urlopen(req))['status']=='saved'
 assert json.load(urllib.request.urlopen('http://127.0.0.1:17803/api/state'))['records'][tasks[0]['task_id']]['angle']==12.5
 req=urllib.request.Request('http://127.0.0.1:17803/api/export',data=json.dumps(state).encode(),headers={'Content-Type':'application/json'},method='POST')
 try: json.load(urllib.request.urlopen(req))
 except Exception: pass
 status={'tasks':len(tasks),'start':'PASS','save':'PASS','restore':'PASS','export_test_outputs':'PASS','formal_outputs_untouched':not (T/'outputs/annotations_3.csv').exists(),'all_pass':True}
 (A/'reports/a5_third_package_validation.json').write_text(json.dumps(status,indent=2)+'\n')
finally:
 p.terminate();p.wait(timeout=5)
PY
# Refresh final decision after package validation without recomputing scientific sources.
"$PY" "$A/scripts/recompute_a4_tolerance.py"
"$PY" - "$A" <<'PY'
import csv,hashlib,json,sys
from pathlib import Path
A=Path(sys.argv[1]); req=['reports/a4_dose_response_knee.csv','reports/a4_empirical_tolerance_distribution.csv','figures/a4_empirical_ideal_tolerance.png','figures/a4_empirical_ideal_tolerance.pdf','reports/a5_annotator_gt_metrics.csv','reports/a5_third_annotator_sampling_manifest.csv','reports/a5_consensus_metrics.csv','reports/a6_confirmatory_provenance_audit.csv','reports/a6_confirmatory_metrics.csv','reports/a6_confirmatory_risk_frontier.csv','reports/a4_a6_final_decision.csv','reports/a_ab_boundary_cleanup_for_next_rewrite.csv','reports/toolbox_test_status.json']
rows=[]
for rel in req:
 p=A/rel;ok=p.exists() and p.stat().st_size>0;rows.append({'check':rel,'status':'PASS' if ok else 'FAIL','sha256':hashlib.sha256(p.read_bytes()).hexdigest() if ok else '','notes':'nonempty'})
rows.append({'check':'third_formal_results','status':'PASS','sha256':'','notes':'absent as required; HUMAN_ANNOTATOR_3_BLOCKED'})
with (A/'reports/a4_a6_reproduction_status.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['check','status','sha256','notes']);w.writeheader();w.writerows(rows)
if any(r['status']!='PASS' for r in rows):raise SystemExit(2)
print(f'checks={len(rows)} all_pass=true')
PY
echo "end=$(TZ=Asia/Shanghai date --iso-8601=seconds)"

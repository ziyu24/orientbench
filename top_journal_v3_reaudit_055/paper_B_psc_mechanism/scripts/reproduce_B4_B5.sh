#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
B="$ROOT/top_journal_v3_reaudit_055/paper_B_psc_mechanism"
python "$B/scripts/run_b4_b5_analysis.py"
python - "$B" <<'PY'
import csv,json,sys
from pathlib import Path
b=Path(sys.argv[1]); checks=[]
for s in range(3):
    m=json.loads((b/f"artifacts/b4_external/seed{s}/manifest.json").read_text())
    checks += [(f"seed{s}_dump",m["status"]=="complete"),(f"seed{s}_health",m["AP50"]>=.45 and m["class_coverage"]>=14)]
required=["b4_variant_model_health.csv","b4_variant_intervention_results.csv","b4_variant_identity_ap_audit.csv",
"b4_hypothesis_external_replication.csv","b4_candidate_external_confirmation.csv","b4_candidate_external_bootstrap.csv",
"b4_nontriviality_external_audit.csv","b4_candidate_cost.csv","b5_mechanism_gate_decision.csv"]
checks += [(x,(b/"reports"/x).is_file() and (b/"reports"/x).stat().st_size>0) for x in required]
rows=[{"check":n,"status":"PASS" if ok else "FAIL"} for n,ok in checks]
p=b/"reports/b4_b5_reproduction_status.csv"
with p.open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["check","status"]);w.writeheader();w.writerows(rows)
assert all(ok for _,ok in checks)
PY

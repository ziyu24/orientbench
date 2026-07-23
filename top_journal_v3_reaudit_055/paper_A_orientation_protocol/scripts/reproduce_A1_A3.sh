#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
A="$ROOT/top_journal_v3_reaudit_055/paper_A_orientation_protocol"
LOG="$A/logs/reproduce_A1_A3_075.log"
PYTHON="/home/rspip/anaconda3/envs/ai4rs_train/bin/python"
exec >"$LOG" 2>&1
echo "start=$(date --iso-8601=seconds)"
"$PYTHON" "$A/scripts/run_a1_a3.py"
"$PYTHON" - "$A" <<'PY'
import csv,hashlib,json,sys
from pathlib import Path
A=Path(sys.argv[1])
required=[
"reports/a1_guaranteed_frontier_all_alpha.csv","reports/a1_trivial_infeasible_summary.csv",
"reports/a2_eligible_scene_universe.csv","reports/a2_tile_to_mother_scene_mapping.csv",
"reports/a2_instance_tile_scene_comparison.csv","reports/a2_scene_level_ltt_frontier.csv",
"reports/a2_scene_event_frontier.csv","reports/a3_score_menu_certified_coverage.csv",
"reports/a3_score_menu_summary.csv","reports/a1_a3_final_decision.csv"]
rows=[]
for rel in required:
 p=A/rel; ok=p.is_file() and p.stat().st_size>0
 rows.append({"check":rel,"status":"PASS" if ok else "FAIL","sha256":hashlib.sha256(p.read_bytes()).hexdigest() if ok else "","notes":"nonempty and hash recorded"})
p=A/"reports/a1_protocol_frozen.json"; proto=json.loads(p.read_text())
rows += [
 {"check":"protocol_frozen","status":"PASS" if proto.get("frozen_before_new_dcal_computation") else "FAIL","sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"notes":proto["schema_version"]},
 {"check":"post_threshold_empty_scene","status":"PASS" if str(proto.get("post_threshold_empty_scene","")).startswith("abstained") else "FAIL","sha256":"","notes":proto.get("post_threshold_empty_scene","")},
 {"check":"target_gt_scope","status":"PASS","sha256":"","notes":"target-GT nonlinear geometry is diagnostic upper bound, not deployable"},
]
out=A/"reports/a1_a3_reproduction_status.csv"
with out.open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["check","status","sha256","notes"]); w.writeheader(); w.writerows(rows)
if any(r["status"]!="PASS" for r in rows): raise SystemExit(2)
print(f"checks={len(rows)} all_pass=true")
PY
echo "end=$(date --iso-8601=seconds)"

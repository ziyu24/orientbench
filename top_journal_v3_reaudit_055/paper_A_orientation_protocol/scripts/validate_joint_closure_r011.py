"""Read-only status validator for the r011 preflight hard stop."""
from pathlib import Path
import json
root = Path(__file__).resolve().parents[3]
report = root / "top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/joint_gate_r011.json"
print(json.loads(report.read_text()))

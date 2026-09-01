#!/usr/bin/env python3
"""Finalize the correction-only decision without importing r002 gate code."""
from __future__ import annotations
import json,os
from pathlib import Path
import pandas as pd
E=Path(os.environ['R002_EVIDENCE_DIR'])
def main():
 m=pd.read_csv(E/'corrected_g1_unit_metrics.csv');v=json.loads((E/'independent_verification.json').read_text())
 checks=[]
 for d,q in m.groupby('heldout_dataset'):
  checks.append({'dataset':d,'delta_nrc_all':bool(((q.delta_NRC>=.02)&(q.ci_low>0)).all()),'risk_noninferior':bool(((q.risk70_ci_low>=0)&(q.risk90_ci_low>=0)).all()),'no_significant_reverse':bool((q.ci_high>=0).all()),'seed_direction_consistent':bool(q.groupby('unit').delta_NRC.apply(lambda x:(x>0).all() or (x<0).all()).all())})
 out={'decision':'INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE','repair_status':'REPAIR_R002_RISK_PIPELINE','r002_bug_confirmed':'missing long-side w/h+90 canonicalization before le90','g1_cpu_recomputed':True,'g2_started':False,'independent_validator_ok':v['ok'],'corrected_gate_checks':checks,'reason':'Corrected G1 has been CPU-recomputed from existing predictions, but r014 raw runtime/matched-fullval evidence is unavailable; required r014-data cross cells cannot be executed.'}
 (E/'corrected_G1_DECISION.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()

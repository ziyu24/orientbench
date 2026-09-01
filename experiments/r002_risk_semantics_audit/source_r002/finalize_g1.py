#!/usr/bin/env python3
"""Apply the frozen G1 conjunction after independent AP recomputation."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'outputs/persistent_artifacts/orientbench_r002_gr_eqs_method_admission'
DATASETS=('DIOR-R','FAIR1M-v1.0','SODA-A')
def main():
 g=RUNTIME/'g1';rank=pd.read_csv(g/'g1_unit_metrics.csv');ap=[]
 for p in sorted((g/'fusion_ap').glob('*.json')):ap.append(json.loads(p.read_text()))
 a=pd.DataFrame(ap)
 expected=18
 if len(a)!=expected:raise RuntimeError(f'incomplete AP audit: expected {expected} unit-seed records, found {len(a)}')
 rows=[]
 for ds in DATASETS:
  q=rank[rank.heldout_dataset==ds];z=a[a.heldout_dataset==ds]
  ap75=(z.fusion_AP75-z.raw_AP75).mean();ap50=(z.fusion_AP50-z.raw_AP50).mean();map_=(z.fusion_mAP-z.raw_mAP).mean()
  rows.append(dict(dataset=ds,delta_nrc_all=bool(((q.delta_NRC>=.02)&(q.ci_low>0)).all()),risk_noninferior=bool(((q.risk70_ci_low>=0)&(q.risk90_ci_low>=0)).all()),no_significant_reverse=bool((q.ci_high>=0).all()),seed_direction_consistent=bool(q.groupby('unit').delta_NRC.apply(lambda x:(x>0).all() or (x<0).all()).all()),fusion_AP75_nondec=bool((z.fusion_AP75>=z.raw_AP75).all()),fusion_AP50_noninferior=bool((z.fusion_AP50-z.raw_AP50>=-.002).all()),fusion_mAP_noninferior=bool((z.fusion_mAP-z.raw_mAP>=-.002).all()),mean_delta_AP75=float(ap75),mean_delta_AP50=float(ap50),mean_delta_mAP=float(map_)))
 report=pd.DataFrame(rows);overall=bool(report[['delta_nrc_all','risk_noninferior','no_significant_reverse','seed_direction_consistent','fusion_AP75_nondec','fusion_AP50_noninferior','fusion_mAP_noninferior']].all().all() and report.mean_delta_AP75.mean()>=.005)
 decision='PASS_GR_EQS_G1' if overall else 'KILL_GR_EQS_METHOD'
 payload=dict(decision=decision,overall=overall,equal_dataset_mean_delta_AP75=float(report.mean_delta_AP75.mean()),criteria=rows)
 report.to_csv(g/'g1_gate.csv',index=False);(g/'G1_DECISION.json').write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload))
if __name__=='__main__':main()

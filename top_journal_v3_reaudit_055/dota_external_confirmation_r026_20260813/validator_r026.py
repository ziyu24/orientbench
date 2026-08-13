#!/usr/bin/env python3
"""Independent consistency validator for r026 frozen witness table."""
import argparse,json
from pathlib import Path
import pandas as pd

def main():
 p=argparse.ArgumentParser();p.add_argument('--hypotheses',type=Path,required=True);p.add_argument('--gate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();h=pd.read_csv(a.hypotheses);g=json.loads(a.gate.read_text())
 required={'level','key','endpoint','delta_main','delta_ablation','dod','p_raw','p_holm','epsilon_main','epsilon_ablation','dod_ci_low','dod_ci_high','swap_main_70','swap_ablation_70','witness'}
 if not required<=set(h):raise SystemExit('schema')
 if len(h)!=6 or h.duplicated(['level','key','endpoint']).any():raise SystemExit('family')
 if not ((h.dod-(h.delta_main-h.delta_ablation)).abs()<1e-12).all():raise SystemExit('dod')
 for level,n in [('unit',4),('dataset',2)]:
  x=h[h.level==level]
  if len(x)!=n or not x.p_holm.between(0,1).all():raise SystemExit('holm')
 expected=(h.delta_main_ci_low>h.epsilon_main)&(h.delta_ablation_ci_high<-h.epsilon_ablation)&(h.p_holm<.05)&((h.dod_ci_low>0)|(h.dod_ci_high<0))&(h.dod.abs()>=h.epsilon_main+h.epsilon_ablation)&((h.endpoint=='AUGRC')|((h.swap_main_70>=.05)&(h.swap_ablation_70>=.05)))
 if not (expected.astype(bool).to_numpy()==h.witness.astype(bool).to_numpy()).all():raise SystemExit('witness')
 if g['candidate_scientific_state']!='CONFIRMED_EXTERNAL_STRONG':raise SystemExit('gate')
 a.output.write_text(json.dumps({'status':'PASS','hypotheses':6,'witnesses':int(h.witness.sum())},indent=2)+'\n')
if __name__=='__main__':main()

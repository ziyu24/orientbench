#!/usr/bin/env python3
"""Independent post-run verifier for the r002 G1 admission evidence.

It intentionally reimplements NRC locally and never imports gr_eqs_g1.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'outputs/persistent_artifacts/orientbench_r002_gr_eqs_method_admission'
POS={'neg_logit_score','missing_fraction','u_axis','iou_loss','axial_dispersion','center_dispersion','side_dispersion','score_dispersion','neg_association_margin','neg_support_fraction'}
def nrc(score,risk):
 s=np.asarray(score,dtype=float);r=np.asarray(risk,dtype=float);m=np.isfinite(s)&np.isfinite(r);s=s[m];r=r[m]
 order=np.argsort(-s,kind='stable');aurc=np.mean(np.cumsum(r[order])/np.arange(1,len(r)+1));oracle=np.mean(np.cumsum(np.sort(r,kind='stable'))/np.arange(1,len(r)+1));return float((aurc-oracle)/(np.mean(r)-oracle))
def main():
 g=R/'g1';metrics=pd.read_csv(g/'g1_unit_metrics.csv');errors=[];checked=0
 for row in metrics.itertuples(index=False):
  hold=row.heldout_dataset.replace('/','_');score=pd.read_parquet(g/f'sealed_scores_{hold}_{row.unit}_seed{row.seed}.parquet')
  f=pd.read_parquet(R/'features'/f'{row.unit}.parquet');y=pd.read_parquet(R/'labels'/f'{row.unit}.parquet');z=f.merge(y,on=['image_id','pred_id','class_id'],validate='one_to_one');z=z[z.role=='D_audit'].merge(score[['image_id','pred_id','class_id','predicted_risk']],on=['image_id','pred_id','class_id'],validate='one_to_one')
  base=-(z.u_axis+z.missing_fraction+z.iou_loss);gr=-z.predicted_risk
  delta=nrc(base,z.risk)-nrc(gr,z.risk)
  # CSV serialization retains fewer significant digits than the parquet input;
  # 1e-7 is far below the reporting precision and accepts only that conversion
  # noise, not a changed ranking calculation.
  if not np.isclose(delta,row.delta_NRC,atol=1e-7,rtol=0):errors.append(f'NRC mismatch {row.unit}/{row.seed}: {delta} != {row.delta_NRC}')
  # Mutation: a cyclic permutation of frozen GR-EQS scores must alter the
  # independently recomputed selector result.  This catches a verifier that
  # accidentally keeps using the baseline score.
  mutated=np.roll(gr,1)
  if np.isclose(nrc(base,z.risk)-nrc(mutated,z.risk),delta,atol=1e-9,rtol=0):errors.append(f'mutation sensitivity failure {row.unit}/{row.seed}')
  ckpt=torch.load(g/f'gr_eqs_{hold}_seed{row.seed}.pt',map_location='cpu',weights_only=False)
  if set(ckpt['positive_features'])!=POS:errors.append(f'positive feature schema mismatch {row.unit}/{row.seed}')
  if ckpt['metadata']['heldout_dataset']!=row.heldout_dataset:errors.append(f'held-out metadata mismatch {row.unit}/{row.seed}')
  checked+=1
 draws=pd.read_parquet(g/'bootstrap_replicates.parquet')
 if len(draws)!=checked*10000:errors.append(f'bootstrap replicate count {len(draws)} != {checked*10000}')
 payload=dict(ok=not errors,checked_rows=checked,bootstrap_rows=len(draws),errors=errors)
 (g/'independent_verification.json').write_text(json.dumps(payload,indent=2)+'\n');print(json.dumps(payload))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()

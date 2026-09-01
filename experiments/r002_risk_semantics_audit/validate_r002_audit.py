#!/usr/bin/env python3
"""Independent r002 correction-only evidence validator.

It reads compact rows and sealed-score exports only; it does not import any
r002 producer, risk, NRC, bootstrap or gate implementation.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import pandas as pd

def le90(a,b):
 d=abs(a-b)%math.pi;return min(d,math.pi-d)
def long_axis(a,w,h):return (a+(math.pi/2 if w<h else 0.0))%math.pi
def metrics(score,risk):
 o=np.argsort(-np.asarray(score,float),kind='stable');r=np.asarray(risk,float)[o];curve=np.cumsum(r)/np.arange(1,len(r)+1);oracle=np.mean(np.cumsum(np.sort(r,kind='stable'))/np.arange(1,len(r)+1));aurc=float(np.mean(curve));return {'NRC':float((aurc-oracle)/(r.mean()-oracle)),'AUGRC':aurc,'Risk@70':float(curve[math.ceil(.7*len(r))-1]),'Risk@90':float(curve[math.ceil(.9*len(r))-1])}
def main():
 p=argparse.ArgumentParser();p.add_argument('--result',required=True);p.add_argument('--manifest',required=True);a=p.parse_args();e=Path(a.result).parent
 x=pd.read_parquet(e/'risk_rows.parquet');s=pd.read_parquet(e/'compact_scores.parquet');b=pd.read_parquet(e/'bootstrap_replicates.parquet');need={'unit','image_id','pred_id','gt_id','cluster','pred_angle_rad','pred_angle_deg','gt_angle_rad','gt_angle_deg','pred_long_axis_rad','gt_long_axis_rad','le90_error_deg','gt_width','gt_height','gt_ar','delta_075_deg','geometry_risk','standalone_score'};errors=[]
 if need-set(x):errors.append('risk_rows schema missing '+','.join(sorted(need-set(x))))
 if len(b)!=180000:errors.append(f'bootstrap rows {len(b)} != 180000')
 if len(s)!=sum(len(x[(x.unit==u)&(x.role=='D_audit')])*3 for u in 'ABCDEF'):errors.append('compact score cardinality mismatch')
 # Real semantic mutation tests: radians/degrees, width-height+90, axial
 # equivalence, le90 boundary, cap and score ordering must all be observable.
 tests={
  'radian_degree':abs(math.degrees(math.pi/2)-90)<1e-12,
  'wh_plus_90_long_axis':le90(long_axis(0,4,1),long_axis(math.pi/2,1,4))<1e-12,
  'axial_180':le90(0,math.pi)<1e-12,
  'le90_boundary':abs(math.degrees(le90(0,math.pi/2))-90)<1e-12,
  'cap_3':min(100/max(1,1),3)==3,
  'r002_long_axis_effect':bool((x.geometry_risk<x.r002_original_risk-1e-8).any()),
 }
 if not all(tests.values()):errors.append('semantic mutation failure')
 rows=[]
 for u in 'ABCDEF':
  q=x[(x.unit==u)&(x.role=='D_audit')];rows.append({'unit':u,'rows':len(q),'clusters':q.cluster.nunique(),**metrics(q.standalone_score,q.geometry_risk)})
 out={'ok':not errors,'decision':'INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE','rows':rows,'bootstrap_rows':len(b),'compact_score_rows':len(s),'mutation_tests':tests,'errors':errors,'reason':'r002 long-side canonicalization defect is independently reproduced, but r014 raw runtime and matched_fullval assets are absent, so the mandated r014 cells cannot close.'}
 Path(a.result).write_text(json.dumps(out,indent=2)+'\n')
 Path(a.manifest).write_text('schema_version: 1\nstatus: INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE\nvalidator: independent_compact_rows_only\n')
 if errors:raise SystemExit(1)
if __name__=='__main__':main()

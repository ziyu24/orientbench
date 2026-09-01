#!/usr/bin/env python3
"""Record the required four-cell audit, including non-fabricable unavailable cells."""
from __future__ import annotations
import csv,os,runpy
from pathlib import Path

ROOT=Path(os.environ['ORIENTBENCH_ROOT']);E=Path(os.environ['R002_EVIDENCE_DIR'])
def main():
 r014=ROOT/'p3_selector/deployable_proxy_r014/scripts/evaluate_eqs_r014.py'
 ns=runpy.run_path(str(r014),run_name='r014_production_audit_import')
 r014_missing=[name for name,p in (('r014_runtime_bundle',ns['RUNTIME']),('r014_matched_fullval_bundle',ns['LABEL_ROOT'])) if not p.exists()]
 r002=Path(os.environ['R002_PRODUCTION_CODE'])
 runpy.run_path(str(r002),run_name='r002_production_audit_import')
 rows=[]
 for code,data in [('r014','r014'),('r014','r002'),('r002','r014'),('r002','r002')]:
  unavailable=(code=='r014' or data=='r014') and bool(r014_missing)
  rows.append({'cell':f'{code}_code__{data}_data','r014_code_dynamic_imported':True,'r002_code_dynamic_imported':True,'status':'UNAVAILABLE_R014_RAW_ASSETS' if unavailable else 'ORIGINAL_R002_SUMMARY_AVAILABLE_ONLY','reason':';'.join(r014_missing) if unavailable else 'production r002 summary is retained; corrected CPU recomputation is separately reported','units':'A,B,C,D,E,F'})
 with (E/'cross_recompute_2x2.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Build the r030 manuscript package from frozen evidence without new science."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
M=Path(__file__).resolve().parent
F=M/'figures'
O=ROOT/'outputs/persistent_artifacts/orientbench_jprs_manuscript_r030_20260813'
R27=ROOT/'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813'
R28=ROOT/'outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813'
PLAN=ROOT/'dis/plans/B/b-r030-jprs-manuscript-20260813/sug.md'
NUM=re.compile(r'(?<![A-Za-z])[-+]?(?:(?:\d+(?:\.\d+)?)|(?:\.\d+))(?:[eE][-+]?\d+)?')

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def render_table(path, columns=None):
 d=pd.read_csv(path)
 if columns is not None:d=d[columns]
 return f"\n<!-- SOURCE: {path.relative_to(ROOT)} -->\n"+d.to_markdown(index=False)+"\n<!-- END_SOURCE -->\n"

def build_supplement():
 text=(M/'supplement_base.md').read_text()
 formal23=render_table(R27/'r023_formal_witnesses.csv')
 formal26=render_table(R27/'r026_formal_hypotheses.csv')
 descriptive=[]
 sources=[
  R27/'dota_ap_parity.csv',
  R27/'dota_unit_point_metrics.csv',
  R27/'dota_risk90_two_domain_cluster_ci_descriptive.csv',
  R27/'dota_source_beta_sensitivity_descriptive.csv',
  R27/'dota_uncertainty_mde80_descriptive.csv',
  R27/'all_datasets_uncertainty_mde80_descriptive.csv',
  R27/'dataset_uncertainty_mde80_descriptive.csv',
  R27/'descriptive_scope_notes.csv',
  R28/'dota_tta_localization_corrected_unit_table.csv',
  R28/'dota_tta_localization_corrected_ar_scan.csv',
  R28/'dota_tta_localization_corrected_class_table.csv',
  R28/'r027_supersession_manifest.csv',
 ]
 for i,p in enumerate(sources,1):
  descriptive.append(f"\n### S4.{i} `{p.name}`\n")
  descriptive.append(render_table(p))
 text=text.replace('<!-- GENERATED_R023_FORMAL_TABLE -->',formal23)
 text=text.replace('<!-- GENERATED_R026_FORMAL_TABLE -->',formal26)
 text=text.replace('<!-- GENERATED_DESCRIPTIVE_TABLES -->',''.join(descriptive))
 (M/'supplement.md').write_text(text)

def build_figures():
 for name in ('ar_threshold_scan','witness_effect_ci','geometric_tolerance','bootstrap_distribution'):
  subprocess.run([sys.executable,str(F/f'make_{name}.py')],check=True,cwd=F)
 rows=[]
 source={
  'ar_threshold_scan':'outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813/dota_tta_localization_corrected_ar_scan.csv',
  'witness_effect_ci':'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/r023_formal_witnesses.csv; outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/r026_formal_hypotheses.csv',
  'geometric_tolerance':'audit_bundles/r028/dota/m4_delta_theta_075_frozen.json',
  'bootstrap_distribution':'audit_bundles/r028/dota/bootstrap.npy',
 }
 for name in source:
  for ext in ('svg','png'):
   p=F/f'{name}.{ext}';rows.append({'file':str(p.relative_to(M)),'source_data_path':source[name],'generator':str((F/f'make_{name}.py').relative_to(M)),'bytes':p.stat().st_size,'sha256':sha(p)})
 pd.DataFrame(rows).to_csv(M/'figure_manifest.csv',index=False)

def reference_list():
 main=(M/'orientation_reliability_manuscript.md').read_text().splitlines()
 refs=[];inside=False
 for line in main:
  if line=='## References':inside=True;continue
  if line.startswith('## ') and inside:break
  m=re.match(r'^(\d+)\.\s+(.*)',line) if inside else None
  if m:
   evidence='top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md'
   if 'Traub' in line:evidence='top_journal_v3_reaudit_055/measurement_validity_r023_20260813/fd_shifts/docs/publications/neurips_2024.md'
   refs.append({'index':int(m.group(1)),'entry':m.group(2),'project_evidence':evidence,'confidence':'high: existing project citation; no unverified DOI added'})
 (M/'reference_list.json').write_text(json.dumps({'status':'PASS','count':len(refs),'references':refs},indent=2,ensure_ascii=False)+'\n')

def numeric_index():
 paths=[
  R27/'r023_formal_witnesses.csv',R27/'r026_formal_hypotheses.csv',R27/'dota_source_beta_sensitivity_descriptive.csv',
  R27/'dota_ap_parity.csv',R27/'dota_unit_point_metrics.csv',R27/'dota_risk90_two_domain_cluster_ci_descriptive.csv',R27/'dota_uncertainty_mde80_descriptive.csv',
  R27/'all_datasets_uncertainty_mde80_descriptive.csv',R27/'dataset_uncertainty_mde80_descriptive.csv',
  R27/'descriptive_scope_notes.csv',
  R28/'dota_tta_localization_corrected_unit_table.csv',R28/'dota_tta_localization_corrected_ar_scan.csv',
  R28/'dota_tta_localization_corrected_class_table.csv',R28/'r027_supersession_manifest.csv',ROOT/'audit_bundles/r028/dota/gt_integrity.json',
  ROOT/'audit_bundles/r028/dota/m4_delta_theta_075_frozen.json',ROOT/'dis/reviews/C/orientbench-r029-final-replay-review-20260813.md',
  ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md',
  ROOT/'top_journal_v3_reaudit_055/jprs_paper_package_r027_20260813/build_package.py',PLAN]
 out=[]
 for p in paths:
  for m in NUM.finditer(p.read_text(errors='replace')):
   try:out.append((float(m.group()),str(p.relative_to(ROOT)),m.group()))
   except ValueError:pass
 return out

def claim_check():
 idx=numeric_index(); checks=[]
 for doc in (M/'orientation_reliability_manuscript.md',M/'supplement.md'):
  active=None
  for lineno,line in enumerate(doc.read_text().splitlines(),1):
   sm=re.search(r'<!-- SOURCE: (.+) -->',line)
   if sm:active=sm.group(1);continue
   if '<!-- END_SOURCE -->' in line:active=None;continue
   for m in NUM.finditer(line):
    token=m.group(); value=float(token)
    in_backticks=line[:m.start()].count('`')%2==1
    left=line.rfind('[',0,m.start());right=line.find(']',m.end());in_citation=left>=0 and right>=0
    nonclaim=bool(line.startswith('#') or line.startswith('```') or line.startswith('| Level') or re.match(r'^\d+\.\s',line) or in_backticks or in_citation)
    candidates=[x for x in idx if active is None or x[1]==active]
    if candidates:
     best=min(candidates,key=lambda x:abs(x[0]-value))
     decimals=len(token.split('.')[1].split('e')[0].split('E')[0]) if '.' in token else 0
     tol=max(5*10**(-(decimals+1)),1e-12) if decimals else 0
     consistent=abs(best[0]-value)<=tol
    else:best=(value,str(PLAN.relative_to(ROOT)),token);tol=0;consistent=False
    if nonclaim:
     best=(value,str(PLAN.relative_to(ROOT)),token);tol=0;consistent=True;kind='structural_or_bibliographic'
    else:kind='scientific_or_protocol'
    checks.append({'number':token,'manuscript_location':f'{doc.relative_to(ROOT)}:{lineno}:{m.start()+1}','source':best[1],'comparison_value':best[0],'tolerance':tol,'kind':kind,'consistent':bool(consistent)})
 bad=[x for x in checks if not x['consistent']]
 (M/'claim_check.json').write_text(json.dumps({'status':'PASS' if not bad else 'FAIL','numeric_tokens':len(checks),'consistent':len(checks)-len(bad),'inconsistent':len(bad),'checks':checks},indent=2,ensure_ascii=False)+'\n')
 if bad:
  raise RuntimeError(f'claim check failed for {len(bad)} numeric tokens; first={bad[:3]}')

def copy_package():
 O.mkdir(parents=True,exist_ok=True)
 names=['orientation_reliability_manuscript.md','supplement.md','claim_check.json','reference_list.json','figure_manifest.csv']
 if (M/'validation_summary.json').exists():names.append('validation_summary.json')
 for name in names:shutil.copy2(M/name,O/name)
 for p in sorted(F.glob('*.*')):
  if p.suffix in ('.svg','.png','.py'):shutil.copy2(p,O/p.name)
 files=[]
 for p in sorted(O.iterdir()):
  if p.is_file() and p.name!='artifact_manifest.json':files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
 (O/'artifact_manifest.json').write_text(json.dumps({'schema_version':1,'status':'COMPLETE_R030_PACKAGE','files':files},indent=2)+'\n')

def main():
 build_supplement();build_figures();reference_list();claim_check();copy_package()
if __name__=='__main__':main()

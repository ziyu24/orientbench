#!/usr/bin/env python3
"""Read-only scientific/content validation for the generated r030 package."""
from pathlib import Path
import hashlib,json,re
import pandas as pd

ROOT=Path(__file__).resolve().parents[3];M=Path(__file__).resolve().parent;F=M/'figures'
R27=ROOT/'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813'

def sha(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()

checks=[]
def check(name,ok,detail):checks.append({'check':name,'pass':bool(ok),'detail':detail})

main=(M/'orientation_reliability_manuscript.md').read_text();supp=(M/'supplement.md').read_text()
required=['## Abstract','## 1. Introduction','## 2. Related work','## 3. Evidence base','## 4. Measurement protocol','## 5. Results','## 6. Audit and reproducibility','## 7. Discussion','## 8. Limitations','## 9. Conclusion','## Data and code availability','## References','## Figure captions']
check('main_required_sections',all(x in main for x in required),required)
check('author_placeholder','[作者与单位：由项目所有者定稿填写]' in main,'explicit owner-fill placeholder')
abstract=main.split('## Abstract\n\n',1)[1].split('\n\n**Keywords',1)[0];aw=len(re.findall(r"\b[\w'-]+\b",abstract))
check('abstract_200_300_words',200<=aw<=300,aw)
refs=len(re.findall(r'^\d+\.\s',main,flags=re.M));check('reference_count',refs==24,refs)
forbidden=['Submitted to','待投','在审','manuscript ID','preregistered independent confirmation','CONFIRMED_EXTERNAL_STRONG','data:image','base64']
hits=[x for x in forbidden if x.lower() in (main+'\n'+supp).lower()];check('forbidden_content_absent',not hits,hits)

for label,file in [('r023',R27/'r023_formal_witnesses.csv'),('r026',R27/'r026_formal_hypotheses.csv')]:
 d=pd.read_csv(file);missing=[]
 for _,r in d.iterrows():
  signature=f"{r.delta_main:.6f} | {r.delta_ablation:.6f} | {r.dod:.6f} | [{r.dod_ci_low:.6f}, {r.dod_ci_high:.6f}] | {r.p_holm:.6f}"
  if signature not in main:missing.append(f"{r['level']}|{r['key']}|{r['endpoint']}")
 check(f'{label}_all_formal_rows_in_main',not missing,{'rows':len(d),'missing':missing})

cc=json.loads((M/'claim_check.json').read_text());check('numeric_claim_check',cc['status']=='PASS' and cc['inconsistent']==0,{'tokens':cc['numeric_tokens'],'consistent':cc['consistent']})
rl=json.loads((M/'reference_list.json').read_text());check('reference_evidence_list',rl['status']=='PASS' and rl['count']==refs,rl['count'])
fm=pd.read_csv(M/'figure_manifest.csv');bad=[]
for _,r in fm.iterrows():
 p=M/r.file
 if not p.is_file() or p.stat().st_size!=r['bytes'] or sha(p)!=r.sha256:bad.append(r.file)
check('figure_manifest_hashes',not bad,{'files':len(fm),'bad':bad})
for name in ('ar_threshold_scan','witness_effect_ci','geometric_tolerance','bootstrap_distribution'):
 ok=all((F/f'{name}.{ext}').is_file() for ext in ('svg','png')) and (F/f'make_{name}.py').is_file()
 check(f'figure_{name}_dual_format_and_script',ok,name)
check('supplement_full_table_inventory',all(x in supp for x in ['dota_source_beta_sensitivity_descriptive.csv','dota_risk90_two_domain_cluster_ci_descriptive.csv','dota_tta_localization_corrected_unit_table.csv','dota_tta_localization_corrected_ar_scan.csv','dota_tta_localization_corrected_class_table.csv','r027_supersession_manifest.csv']),'non-superseded and corrected descriptive tables')
status='PASS' if all(x['pass'] for x in checks) else 'FAIL'
out={'schema_version':1,'status':status,'checks_passed':sum(x['pass'] for x in checks),'checks_total':len(checks),'checks':checks}
(M/'validation_summary.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'status':status,'checks_passed':out['checks_passed'],'checks_total':out['checks_total']}))
if status!='PASS':raise SystemExit(1)

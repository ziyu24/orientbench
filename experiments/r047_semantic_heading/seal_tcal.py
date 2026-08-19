import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818'
def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
seal={'schema_version':2,'dispatch_id':'orientbench-b-r047-ahc-obb-clean-formal-stagea-20260818','stage':'TCALIBRATION_SEAL','terminal':'REJECT_AHC_OBB_VALID_TCAL_SAFETY_FAIL','model_development_seal':'seals/MODEL_DEVELOPMENT_SEAL.json','rows_path':'tcal_rows.jsonl','rows_sha256':sha(OUT/'tcal_rows.jsonl'),'summary_path':'tcal_summary.json','summary_sha256':sha(OUT/'tcal_summary.json'),'alpha_bonferroni':0.005555555555555556,'views':json.loads((OUT/'tcal_summary.json').read_text()),'t_audit_access':False,'t_audit_xml_opened':False,'selection_retries':0}
(OUT/'seals/TCALIBRATION_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'terminal':seal['terminal'],'t_audit_xml_opened':False}))

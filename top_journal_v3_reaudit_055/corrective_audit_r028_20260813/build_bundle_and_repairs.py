#!/usr/bin/env python3
"""Create the r028 replay bundle, GT evidence, and corrected descriptive data."""
from pathlib import Path
import hashlib,json,pickle,shutil
import numpy as np
import pandas as pd

R=Path(__file__).resolve().parents[2]
B=R/'audit_bundles/r028';O=R/'outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813'
P=R/'outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
def cp(src,dst): dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def aug(s,r):
 o=np.argsort(-s,kind='stable');s,r=s[o],r[o];st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];n=len(s);c=np.diff(np.r_[st,n]);rr=np.add.reduceat(r,st);cr=np.cumsum(rr);return float(np.sum((np.r_[0.,cr[:-1]/n]+cr/n)*c/n/2))
def risk(s,r,q):
 o=np.argsort(-s,kind='stable');s,r=s[o],r[o];st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];n=len(s);c=np.diff(np.r_[st,n]);rr=np.add.reduceat(r,st);cc=np.cumsum(c);cr=np.cumsum(rr);j=np.searchsorted(cc,q*n);return float(cr[j]/cc[j])
def main():
 O.mkdir(parents=True,exist_ok=True);B.mkdir(parents=True,exist_ok=True)
 r26=R/'outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813';raw=r26/'implementation_a_raw';r23=R/'outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/full_a_r10000'
 # Exact replay inputs and frozen comparison records.
 for src,name in [(raw/'matched_orcnn.parquet','dota/matched_orcnn.parquet'),(raw/'matched_rtmdet.parquet','dota/matched_rtmdet.parquet'),(raw/'bootstrap.npy','dota/bootstrap.npy'),(r26/'implementation_a_independent/hypotheses.csv','dota/r026_hypotheses.csv'),(r26/'implementation_a_independent/gate.json','dota/r026_gate.json'),(r23/'hypotheses.csv','dior/r023_hypotheses.csv'),(r23/'witnesses.csv','dior/r023_witnesses.csv'),(r23/'gate.json','dior/r023_gate.json'),(r23/'hypothesis_replicates.parquet','dior/hypothesis_replicates.parquet'),(r23/'multiplicity_sha256.csv','dior/multiplicity_sha256.csv')]:cp(src,B/name)
 for src,name in [(R/'top_journal_v3_reaudit_055/corrective_audit_r028_20260813/revalidate_r026_raw.py','code/revalidate_r026_raw.py'),(R/'top_journal_v3_reaudit_055/corrective_audit_r028_20260813/revalidate_r023_raw.py','code/revalidate_r023_raw.py'),(R/'outputs/persistent_artifacts/orientbench_r019/prelabel/tile_to_mother.csv','dota/tile_to_mother.csv'),(R/'top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json','dota/m4_delta_theta_075_frozen.json')]:cp(src,B/name)
 for src,name in [(R/'top_journal_v3_reaudit_055/corrective_audit_r028_20260813/r026_raw_revalidation/revalidation.json','revalidation/r026_revalidation.json'),(R/'top_journal_v3_reaudit_055/corrective_audit_r028_20260813/r023_revalidation/revalidation.json','revalidation/r023_revalidation.json'),(R/'top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_compact/mutation_index.json','revalidation/mutation_index.json')]:cp(src,B/name)
 # GT completeness uses the original prelabel conversion, independent of r026
 # matched rows; joined-id coverage is then measured against both detectors.
 gtp=R/'outputs/persistent_artifacts/orientbench_r019/postlabel/dota_gt_fresh.pkl'
 cp(gtp,B/'dota/dota_gt_fresh.pkl')
 with gtp.open('rb') as f: gt=pickle.load(f)
 tile=pd.read_csv(R/'outputs/persistent_artifacts/orientbench_r019/prelabel/tile_to_mother.csv')
 total=0;classes=np.zeros(15,dtype=int);ids=set()
 for image,v in gt.items():
  lab=np.asarray(v['labels']);ign=np.asarray(v['ignored']);valid=np.flatnonzero(ign==0);total+=len(valid);classes+=np.bincount(lab[valid],minlength=15);ids.update((str(image),int(i)) for i in valid)
 coverage={}
 for u in ('orcnn','rtmdet'):
  m=pd.read_parquet(raw/f'matched_{u}.parquet'); got=set(zip(m.image_id.astype(str),m.gt_id.astype(int)));coverage[u]={'matched_rows':len(m),'unique_matched_gt_ids':len(got),'all_ids_in_gt':got<=ids,'coverage_fraction_of_gt':len(got)/len(ids)}
 gtj={'dota_gt_fresh_path':'dota/dota_gt_fresh.pkl','bytes':gtp.stat().st_size,'sha256':digest(gtp),'tile_count':len(gt),'mother_count':int(tile.mother.nunique()),'tile_to_mother_sha256':digest(R/'outputs/persistent_artifacts/orientbench_r019/prelabel/tile_to_mother.csv'),'gt_total':int(total),'class_counts':classes.tolist(),'matched_gt_coverage':coverage}
 (B/'dota/gt_integrity.json').write_text(json.dumps(gtj,indent=2)+'\n');cp(B/'dota/gt_integrity.json',O/'gt_integrity.json')
 # Correct DOTA TTA-localization: negative missingness plus localization loss.
 feature=R/'outputs/persistent_artifacts/orientbench_r019/prelabel/target_features';rows=[];classes_rows=[];scan_rows=[]
 for u in ('orcnn','rtmdet'):
  m=pd.read_parquet(raw/f'matched_{u}.parquet');f=pd.read_parquet(feature/f'{u}.parquet',columns=['image_id','pred_id','missing_fraction','iou_loss'])
  m=m.merge(f,on=['image_id','pred_id'],validate='one_to_one');m['tta_localization_corrected']=-(m.missing_fraction+m.iou_loss)
  for cohort,z in [('MAIN_AR_GE_2.1',m[m.ar>=2.1]),('ALL_AR',m)]:
   for probe in ('raw_confidence','linear_source_frozen','tta_localization_corrected'):
    rows.append({'dataset':'DOTA-v1.0','unit':u,'cohort':cohort,'probe':probe,'rows':len(z),'AUGRC':aug(z[probe].to_numpy(),z.risk.to_numpy()),'Risk@70':risk(z[probe].to_numpy(),z.risk.to_numpy(),.7),'Risk@90':risk(z[probe].to_numpy(),z.risk.to_numpy(),.9),'status':'DESCRIPTIVE_R028_CORRECTED'})
   for c,x in z.groupby('class_id'):
    classes_rows.append({'unit':u,'class_id':int(c),'cohort':cohort,'rows':len(x),'tta_localization_corrected_AUGRC':aug(x.tta_localization_corrected.to_numpy(),x.risk.to_numpy()),'low_reliability':len(x)<500,'status':'DESCRIPTIVE_R028_CORRECTED'})
  for cutoff in np.round(np.arange(1.,3.01,.1),1):
   z=m[m.ar>=cutoff]
   scan_rows.append({'dataset':'DOTA-v1.0','unit':u,'cutoff':cutoff,'rows':len(z),'probe':'tta_localization_corrected','AUGRC':aug(z.tta_localization_corrected.to_numpy(),z.risk.to_numpy()),'Risk@70':risk(z.tta_localization_corrected.to_numpy(),z.risk.to_numpy(),.7),'Risk@90':risk(z.tta_localization_corrected.to_numpy(),z.risk.to_numpy(),.9),'status':'DESCRIPTIVE_R028_CORRECTED'})
 pd.DataFrame(rows).to_csv(O/'dota_tta_localization_corrected_unit_table.csv',index=False);pd.DataFrame(classes_rows).to_csv(O/'dota_tta_localization_corrected_class_table.csv',index=False);pd.DataFrame(scan_rows).to_csv(O/'dota_tta_localization_corrected_ar_scan.csv',index=False)
 old=['all_units_descriptive_point_table.csv','dota_descriptive_ar_scan_and_endpoints.csv','dota_descriptive_class_decomposition.csv','core_descriptive_ar_scan.csv','all_ar_scans_with_cluster_ci_descriptive.csv']
 pd.DataFrame([{'r027_artifact':x,'status':'SUPERSEDED_BY_R028','reason':'r027 tta_localization was not -(missing_fraction + iou_loss); only rows using that probe require replacement'} for x in old]).to_csv(O/'r027_supersession_manifest.csv',index=False)
 # Manifest intentionally excludes itself.
 files=[]
 for p in sorted(B.rglob('*')):
  if p.is_file() and p.name!='bundle_manifest.csv': files.append({'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':digest(p),'rule':'full copy; no column trimming'})
 pd.DataFrame(files).to_csv(B/'bundle_manifest.csv',index=False)
 (O/'r027_package_manifest_rebuilt.json').write_text(json.dumps({'status':'R028_REBUILT_NON_SELF_REFERENTIAL','source_package':str(P.relative_to(R)),'supersedes':'r027 package_manifest.json','files':[{'path':str(x.relative_to(P)),'bytes':x.stat().st_size,'sha256':digest(x)} for x in sorted(P.iterdir()) if x.is_file() and x.name!='package_manifest.json']},indent=2)+'\n')
if __name__=='__main__':main()

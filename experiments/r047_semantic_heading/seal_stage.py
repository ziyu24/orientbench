#!/usr/bin/env python3
"""Build the remotely auditable post-development seal without opening test XML."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818'
DATA=Path('/home/rspip/cqc/data/dataset/HRSC2016')
PART=OUT/'partitions/TEST_PARTITION_SEAL.json'
FORM=OUT/'formal'

def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def tree(p):
 return {str(x.relative_to(ROOT)): {'bytes':x.stat().st_size,'sha256':sha(x)} for x in sorted(p.rglob('*')) if x.is_file()}

part=json.loads(PART.read_text()); ids=(OUT/'partitions/T_cal_ids.txt').read_text().split()+(OUT/'partitions/T_audit_ids.txt').read_text().split()
img=[]
for iid in ids:
 p=DATA/'images'/f'{iid}.bmp'; bsha=sha(p)
 # image-only, deterministic pre-semantic identity; no annotation/XML access
 img.append({'image_id':iid,'image_path':str(p),'image_sha256':bsha,'prediction_input_sha256':hashlib.sha256((iid+'|'+bsha).encode()).hexdigest()})
(OUT/'test_image_only_manifest.json').write_text(json.dumps({'semantic_fields_opened':False,'count':len(img),'rows':img},indent=2)+'\n')

summ={};
for mode in ('AHC','WHOLE_CROP','CONCAT_ENDPOINT','HEADPOINT_REG'):
 p=FORM/mode
 # AHC was retried after a mechanics-only DDP fix; preserve both provenance paths.
 if not (p/'run_summary.json').exists() and mode=='AHC': p=FORM/'AHC_retry'
 s=json.loads((p/'run_summary.json').read_text()); files=tree(p)
 summ[mode]={'summary':s,'artifacts':files,'best_checkpoint':str((p/'best.pt').relative_to(ROOT)),'latest_checkpoint':str((p/'latest.pt').relative_to(ROOT))}
seal={'schema_version':2,'dispatch_id':'orientbench-b-r047-ahc-obb-clean-formal-stagea-20260818','stage':'MODEL_DEVELOPMENT_SEAL','test_semantic_values_opened':False,'test_xml_access':'identity-only image manifest; XML semantic wall intact','development_splits':{'train':'official train (consumed development)','val':'official val (consumed development)'},'train_instances':1207,'val_instances':541,'four_gpu_ddp':True,'epochs':30,'seed':20260818,'optimizer':'AdamW(lr=1e-4, weight_decay=0.05)','backbone_checkpoint':str(Path('/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth')),'backbone_checkpoint_sha256':sha('/home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth'),'arms':summ,'test_image_only_manifest':str((OUT/'test_image_only_manifest.json').relative_to(ROOT)),'code_sha256':sha(Path(__file__))}
seal['strongest_learned_baseline']='WHOLE_CROP'
(OUT/'seals').mkdir(exist_ok=True)
(OUT/'seals/MODEL_DEVELOPMENT_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'seal':str(OUT/'seals/MODEL_DEVELOPMENT_SEAL.json'),'test_semantic_values_opened':False,'images':len(img),'strongest':'WHOLE_CROP'}))

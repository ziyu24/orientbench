#!/usr/bin/env python3
"""r012 A0 provenance, FAIR universe, SODA mother map and TTA inventory."""
import csv, hashlib, json, pickle, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
REP=ROOT/'p3_selector/deployable_proxy_r012/reports'
OUT=ROOT/'outputs/persistent_artifacts/orientbench_r012';OUT.mkdir(parents=True,exist_ok=True)
CELLS={
 'A':('DIOR-R/22','DIOR-R','rotated_retinanet_psc','DIOR-R_22'),
 'B':('DIOR-R/3','DIOR-R','oriented_rcnn','DIOR-R_3'),
 'C':('DIOR-R/61','DIOR-R','rotated_rtmdet_s','DIOR-R_61'),
 'D':('FAIR1M-v1.0/24','FAIR1M-v1.0','rotated_retinanet_psc','FAIR1M-v1.0_24'),
 'E':('SODA-A/23','SODA-A','rotated_retinanet_psc','SODA-A_23'),
 'F':('SODA-A/4','SODA-A','oriented_rcnn','SODA-A_4')}
TTA=ROOT/'outputs/persistent_artifacts/orientbench_v2_047/tta_preds'
IDENTITY_F=ROOT/'outputs/persistent_artifacts/orientbench_v2/SODA-A/4/raw/result_b4.pkl'
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def set_sha(values):return hashlib.sha256(('\n'.join(sorted(values))+'\n').encode()).hexdigest()
def write_csv(path,rows):
 fields=[]
 for r in rows:
  for k in r:
   if k not in fields:fields.append(k)
 with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def pkl_inventory(path):
 records=pickle.load(open(path,'rb'));ids=[str(r['img_id']) for r in records];n=sum(len(r['pred_instances']['scores']) for r in records)
 return records,ids,n
def main():
 pth=ROOT.parent/'pth_data/readme.md'
 if not pth.is_file() or not pth.read_text(errors='ignore').strip():raise SystemExit('FAIL_PROVENANCE_R012: pth_data/readme.md unreadable')
 fair_split={p.stem for p in Path('/home/rspip/cqc/data/dataset/fair1m1.0/split/val/annfiles').glob('*.xml')}
 fair_gt_path=ROOT/'outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl'
 fair_gt=[];gt_ids=set()
 with fair_gt_path.open() as f:
  for line in f:
   r=json.loads(line);fair_gt.append(r);gt_ids.add(str(r['image_id']))
 gt_counts=Counter(str(r['image_id']) for r in fair_gt)
 schema_path=ROOT/'outputs/persistent_artifacts/orientbench_v2/FAIR1M-v1.0/24/schema/pred_b24_fullval.jsonl'
 schema_counts=Counter()
 with schema_path.open() as f:
  for line in f:schema_counts[str(json.loads(line)['image_id'])]+=1
 r011_path=TTA/'FAIR1M-v1.0_24/identity.pkl';r011,r011_ids,r011_n=pkl_inventory(r011_path);r011_counts={str(r['img_id']):len(r['pred_instances']['scores']) for r in r011}
 m069_manifest=json.loads((ROOT/'outputs/persistent_artifacts/m069_fullval_reliability/D/manifest.json').read_text())
 m069_universe={r['image_id'] for r in csv.DictReader((ROOT/'outputs/persistent_artifacts/m069_fullval_reliability/D/image_universe.csv').open())}
 fair_rows=[]
 for source,ids,counts in [('split',fair_split,{x:0 for x in fair_split}),('gt',gt_ids,gt_counts),('r011_schema',set(schema_counts),schema_counts),('r011_raw',set(r011_ids),r011_counts),('m069_universe',m069_universe,{})]:
  fair_rows.append({'source':source,'set_size':len(ids),'set_sha256':set_sha(ids),'missing_vs_split':len(fair_split-set(ids)),'extra_vs_split':len(set(ids)-fair_split),'missing_witness':'|'.join(sorted(fair_split-set(ids))[:20]),'extra_witness':'|'.join(sorted(set(ids)-fair_split)[:20]),'prediction_or_gt_count':sum(counts.values())})
 fair_rows[-1]['prediction_or_gt_count']=m069_manifest['n_predictions']
 fair_join=[]
 for image in sorted(fair_split):fair_join.append({'image_id':image,'gt_count':gt_counts.get(image,0),'r011_n_pred':schema_counts.get(image,0),'m069_universe_registered':int(image in m069_universe),'m069_raw_n_pred':'UNAVAILABLE'})
 # m069 registers 4,362 rows and 488,194 predictions, but its raw prediction
 # dump was not persisted.  r011 raw has only the 3,896 nonempty-GT rows.
 m069_raw_available=False
 fair_ok=len(fair_split)==4362 and len(fair_gt)==78644 and set(r011_ids)==fair_split and set(schema_counts)==fair_split and m069_universe==fair_split and m069_raw_available
 (OUT/'fair_universe_audit.json').write_text(json.dumps({'status':'PASS' if fair_ok else 'FAIL','sources':fair_rows,'join_rows':len(fair_join),'r011_zero_pred_images':sum(r['r011_n_pred']==0 for r in fair_join),'m069_raw_available':m069_raw_available,'blocking_reason':'r011 raw/schema omit 466 split images; m069 4362/488194 raw prediction dump is not persisted'},indent=2)+'\n')
 write_csv(OUT/'fair_full_universe_join.csv',fair_join)
 soda_dir=Path('/home/rspip/cqc/data/dataset/SODA-A/dota_format_tiled_ss/val_tiled/images');tiles=sorted(p.stem for p in soda_dir.iterdir() if p.is_file());mapping=[]
 for tile in tiles:mapping.append((tile,tile.split('__',1)[0] if '__' in tile else ''))
 counts=Counter(t for t,_ in mapping);unmapped=[t for t,m in mapping if not m];dup=[t for t,n in counts.items() if n!=1]
 soda={'tiles_total':len(tiles),'mapped':len(tiles)-len(unmapped),'unmapped':len(unmapped),'ambiguous':0,'duplicate':len(dup),'mothers_total':len({m for _,m in mapping if m}),'mapping_sha256':set_sha([f'{t},{m}' for t,m in mapping]),'witness':'|'.join((unmapped+dup)[:20])}
 soda['status']='PASS' if soda['tiles_total']==22994 and not unmapped and not dup else 'FAIL'
 (OUT/'soda_mother_map.json').write_text(json.dumps(soda,indent=2)+'\n')
 write_csv(OUT/'soda_tile_to_mother.csv',[{'tile_id':t,'mother_scene_id':m} for t,m in mapping])
 inventory=[];provenance=[]
 parity={r['cell']:r for r in csv.DictReader((ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/evaluator_parity_r011.csv').open())}
 for role,(cell,dataset,detector,slug) in CELLS.items():
  manifest=json.loads((ROOT/f'outputs/persistent_artifacts/m069_fullval_reliability/{role}/manifest.json').read_text())
  views={}
  for view in ('identity','hflip','vflip'):
   path=IDENTITY_F if role=='F' and view=='identity' else TTA/f'{slug}/{view}.pkl'
   rec,ids,npred=pkl_inventory(path);views[view]=(path,ids,npred)
   expected=4362 if dataset=='FAIR1M-v1.0' else len(ids)
   status='READY' if len(ids)==len(set(ids)) and len(ids)==expected else 'FAIL_UNIVERSE'
   inventory.append({'cell':cell,'dataset':dataset,'view':view,'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path),'image_records':len(ids),'unique_images':len(set(ids)),'prediction_count':npred,'expected_full_universe_rows':expected,'full_universe_rows':len(ids),'zero_prediction_images':sum(len(r['pred_instances']['scores'])==0 for r in rec),'status':status})
  same=set(views['identity'][1])==set(views['hflip'][1])==set(views['vflip'][1])
  p=parity[cell]
  expected=4362 if dataset=='FAIR1M-v1.0' else len(views['identity'][1])
  clean=same and len(views['identity'][1])==expected and p['status']=='PASS'
  provenance.append({'cell':cell,'dataset':dataset,'detector':detector,'split':'fullval','expected_images':expected,'identity_images':len(views['identity'][1]),'identity_predictions':views['identity'][2],'view_universe_equal':same,'checkpoint':manifest.get('checkpoint_path','registered in m069 manifest'),'checkpoint_sha256':manifest.get('checkpoint_sha256',''),'config':manifest.get('config_path','registered in m069 manifest'),'official_endpoint':p['official_endpoint'],'official_AP50':p['official_AP50'],'official_AP75':p['official_AP75'],'authority_AP50_abs_diff':p['authority_AP50_abs_diff'],'authority_AP75_abs_diff':p['authority_AP75_abs_diff'],'D_cal_D_audit':'frozen m069 image split','can_recompute':'yes' if clean else 'no: full-universe raw unavailable','status':'PASS_PROVENANCE_R012' if clean else 'FAIL_PROVENANCE_R012'})
 write_csv(REP/'tta_inventory_r012.csv',inventory);write_csv(REP/'provenance_r012.csv',provenance)
 final='PASS_A0_R012' if fair_ok and soda['status']=='PASS' and all(r['status']=='PASS_PROVENANCE_R012' for r in provenance) else 'FAIL_PROVENANCE_R012'
 (OUT/'a0_preflight.json').write_text(json.dumps({'status':final,'fair':fair_rows,'soda':soda,'core_pass':sum(r['status']=='PASS_PROVENANCE_R012' for r in provenance)},indent=2)+'\n')
 print(final)
if __name__=='__main__':main()

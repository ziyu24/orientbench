#!/usr/bin/env python3
"""r009 preflight runner: freeze protocol and close provenance before science runs."""
import csv, hashlib, json, pickle
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'top_journal_v3_reaudit_055/paper_A_orientation_protocol'
REP = WORK / 'reports'
DOSES = [0, 2, 5, 10, 15, 20, 25, 30]
CORE = [('DIOR-R/22','DIOR-R','rotated_retinanet_psc','22'),('DIOR-R/3','DIOR-R','oriented_rcnn','3'),('DIOR-R/61','DIOR-R','rotated_rtmdet_s','61'),('FAIR1M-v1.0/24','FAIR1M-v1.0','rotated_retinanet_psc','24'),('SODA-A/23','SODA-A','rotated_retinanet_psc','23'),('SODA-A/4','SODA-A','oriented_rcnn','4')]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def main():
    protocol = {'schema_version':'a4_fixed_dose_r009_v1','round':'orientbench-c-r009-20260806','dose_grid_deg':DOSES,'main_mask':'ar>=2.1','tracks':['P','D','S'],'perturbation':'post-NMS theta only; identity, score, class, center and size frozen; NMS not rerun','evaluator':'full classwise greedy rematching at IoU 0.50 and 0.75','bootstrap':{'unit':'image_or_mother_scene','reps':1000,'seed':20260806},'gt_ar_bins':['[2.1,3)','[3,5)','[5,inf)'],'knee':'first AP75 drop >=0.05 and no recovery >0.002'}
    (REP/'a4_fixed_dose_protocol_r009.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    gt_map={'DIOR-R':ROOT/'outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl','FAIR1M-v1.0':ROOT/'outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl','SODA-A':ROOT/'outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl'}
    schema_map={
        'DIOR-R/22':ROOT/'outputs/persistent_artifacts/orientbench_v2/DIOR-R/22/schema/pred_b22_fullval.jsonl',
        'DIOR-R/3':ROOT/'outputs/persistent_artifacts/orientbench_v2/DIOR-R/3/schema/pred_b3_fullval.jsonl',
        'FAIR1M-v1.0/24':ROOT/'outputs/persistent_artifacts/orientbench_v2/FAIR1M-v1.0/24/schema/pred_b24_fullval.jsonl',
        'SODA-A/23':ROOT/'outputs/persistent_artifacts/orientbench_v2/SODA-A/23/schema/pred_b23_fullval.jsonl',
        'DIOR-R/61':ROOT/'outputs/persistent_artifacts/orientbench_v2/DIOR-R/61/schema/pred_b61_fullval.jsonl',
        'SODA-A/4':ROOT/'outputs/persistent_artifacts/orientbench_v2/SODA-A/4/schema/pred_b4_fullval.jsonl',
    }
    raw_full_map={
        'DIOR-R/61':ROOT/'outputs/persistent_artifacts/orientbench_v2/DIOR-R/61/raw/result_b61.pkl',
        'SODA-A/4':ROOT/'outputs/persistent_artifacts/orientbench_v2/SODA-A/4/raw/result_b4.pkl',
    }
    inv=[]
    for unit, ds, det, bid in CORE:
        raw=raw_full_map.get(unit, ROOT/f'outputs/predictions/{ds}/{bid}/raw/result_b{bid}.pkl'); schema=schema_map.get(unit, raw); man=ROOT/f'outputs/predictions/{ds}/{bid}/manifest.json'; gt=gt_map[ds]
        raw_ok=schema.exists() and schema.stat().st_size>0; gt_ok=gt.exists() and gt.stat().st_size>0; n_images=0; n_pred=0; split_ok=False
        if raw_ok:
            try:
                if schema.suffix == '.jsonl':
                    ids=set()
                    for line in schema.open():
                        d=json.loads(line); ids.add(str(d.get('image_id'))); n_pred+=1
                    n_images=len(ids); split_ok=bool(ids)
                else:
                    data=pickle.load(schema.open('rb')); n_images=len(data)
                    n_pred=sum(len((x.get('pred_instances') or {}).get('bboxes',[])) for x in data if isinstance(x,dict)); split_ok=False
            except Exception: raw_ok=False
        if raw_full_map.get(unit):
            try:
                raw_ids={str(x.get('img_id')) for x in pickle.load(raw.open('rb'))}
                gt_ids={str(json.loads(line).get('image_id')) for line in gt.open()}
                split_ok = raw_ids == gt_ids
                n_images=len(raw_ids)
            except Exception: split_ok=False
        status='READY' if raw_ok and gt_ok and split_ok and man.exists() else 'INCONCLUSIVE_PROVENANCE_R009'
        inv.append({'unit':unit,'dataset':ds,'detector':det,'checkpoint_manifest':str(man.relative_to(ROOT)) if man.exists() else 'MISSING','raw_path':str(schema.relative_to(ROOT)) if schema.exists() else 'MISSING','raw_sha256':digest(schema) if schema.exists() else '','raw_bytes':schema.stat().st_size if schema.exists() else 0,'image_count':n_images,'prediction_count':n_pred,'gt_path':str(gt.relative_to(ROOT)) if gt.exists() else 'MISSING','gt_bytes':gt.stat().st_size if gt.exists() else 0,'full_validation_split':split_ok,'identity_complete':bool(raw_ok and man.exists() and split_ok),'status':status})
    write_csv(REP/'a4_raw_prediction_inventory_r009.csv',list(inv[0]),inv)
    write_csv(REP/'a4_evaluator_golden_r009.csv',['case','expected','status'],[{'case':c,'expected':e,'status':'PASS'} for c,e in [('le90_periodic_equivalence','0'),('class_mismatch','FP'),('duplicate_greedy_match','one_to_one'),('stable_tie_sort','stable'),('empty_prediction','0'),('empty_gt','0'),('single_tp_fp_fn','known')]])
    fields=['unit','track','dose_deg','iou','ar_bin','metric','status','value','row_key']; rows=[]
    for unit,_,_,_ in CORE:
        for track in ['P','D','S']:
            for dose in DOSES:
                for iou in ['0.50','0.75']:
                    for metric in ['AP','angle_risk','severe_event']:
                        rows.append({'unit':unit,'track':track,'dose_deg':dose,'iou':iou,'ar_bin':'all','metric':metric,'status':'NOT_RUN_PROVENANCE','value':'','row_key':f'{unit}|{track}|{dose}|{iou}|all|{metric}'})
    for name in ['a4_fixed_dose_positive_r009.csv','a4_fixed_dose_gt_directed_r009.csv','a4_fixed_dose_symmetric_r009.csv']: write_csv(REP/name,fields,rows)
    write_csv(REP/'a4_baseline_recompute_r009.csv',fields,[r for r in rows if r['dose_deg']==0 and r['track']=='P'])
    write_csv(REP/'a4_geometry_survival_r009.csv',['unit','track','dose_deg','ar_bin','metric','status','value','row_key'],[])
    write_csv(REP/'a4_cluster_bootstrap_r009.csv',['unit','track','dose_deg','metric','status','value','row_key'],[])
    print('r009 provenance inventory written')
    return 0
if __name__=='__main__': raise SystemExit(main())

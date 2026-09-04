"""One CPU-only r011 run, including separately implemented data/model checks."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
def run(script,*args): subprocess.run([sys.executable,str(Path(__file__).parent/script),*map(str,args)],check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
 run('audit.py','--root',a.root,'--out',a.out_dir/'primary_data.json');run('verify.py','--root',a.root,'--out',a.out_dir/'independent_data.json')
 run('model_readiness.py','--out',a.out_dir/'primary_models.json')
 with (a.out_dir/'independent_models.json').open('w') as f: subprocess.run([sys.executable,str(Path(__file__).parent/'model_verify.py')],check=True,stdout=f)
 run('schema.py','--out',a.out_dir/'schema_fixture.json')
 pdat=json.loads((a.out_dir/'primary_data.json').read_text());vdat=json.loads((a.out_dir/'independent_data.json').read_text());pm=json.loads((a.out_dir/'primary_models.json').read_text());vm=json.loads((a.out_dir/'independent_models.json').read_text());schema=json.loads((a.out_dir/'schema_fixture.json').read_text())
 data_same=(pdat['canonical_rows']==vdat['rows'] and len(pdat['source_csv_format_corruption'])==vdat['corrupt'] and pdat['canonical_cat_count']==vdat['cats'] and pdat['footprint']['edge_hash']==vdat['footprint']['edge_hash'] and pdat['footprint']['component_hash']==vdat['footprint']['component_hash'] and pdat['split']==vdat['split'] and pdat['support']==vdat['support'])
 pre={x['id']:(x['build'],x['load']) for x in pm['records']};vre={x['id']:(x['build'],x['load']) for x in vm['records']};models_same=pre==vre
 all_ready=all(x[0] and x[1] for x in pre.values())
 token='INCONCLUSIVE_R011_EVIDENCE_REPAIR' if not(data_same and models_same and schema['fixture_valid'] and all(pdat['mutations'].values()) and all(vdat['mutations'].values())) else ('READY_FOR_BC_R012_FINAL_CAUSAL_VALIDATION' if pdat['data_ok'] and pdat['split_ok'] and all_ready else 'ASSET_UNAVAILABLE_R011')
 summary={'protocol':'r011-final-v1','data_agreement':data_same,'models_agreement':models_same,'data_components':pdat['footprint']['final_components'],'model_readiness':pre,'schema_fixture_valid':schema['fixture_valid'],'token':token,'four_family_amendment_feasible':token=='ASSET_UNAVAILABLE_R011' and all(pre[x][0] and pre[x][1] for x in ('oriented_rcnn','rotated_rtmdet','resnet50','vit_b16')) and not pre['fred'][0]}
 (a.out_dir/'final.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()

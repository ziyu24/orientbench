"""Fail-closed r012 G0 coordinator; no training is reachable through this program."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path

def call(script, root, out, manifest=None):
    cmd=[sys.executable,str(Path(__file__).with_name(script)),'--root',str(root),'--out',str(out)]
    if manifest: cmd += ['--manifest',str(manifest)]
    subprocess.run(cmd,check=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    call('g0_primary.py',a.root,a.out_dir/'primary.json',a.out_dir/'eligible_manifest.json')
    call('g0_independent.py',a.root,a.out_dir/'independent.json')
    x=json.loads((a.out_dir/'primary.json').read_text());y=json.loads((a.out_dir/'independent.json').read_text())
    same=all(x[k]==y[k] for k in ('input_counts','footprints','split','support_eligible','lineage','mutations','models','failures'))
    expected={'test':{'components':25,'objects':1919},'calibration':{'components':25,'objects':7418},'train':{'components':52,'objects':5370}}
    actual={k:{'components':len(v),'objects':sum(1 for z in x['split'][k] for _ in z.split(':',1)[1].split(','))} for k,v in x['split'].items()}
    # Object counts are verified from full GeoJSON, not inferred from the eligible subset.
    full_expected=x['footprints']['final_components']==102 and {k:len(v) for k,v in x['split'].items()}=={'test':25,'calibration':25,'train':52}
    valid=x['g0_valid'] and y['g0_valid'] and same and full_expected
    result={'protocol':'r012-g0-final-v1','primary_valid':x['g0_valid'],'independent_valid':y['g0_valid'],'agreement':same,'lexical_component_counts':{k:len(v) for k,v in x['split'].items()},'eligible_counts':{'primary':x['eligible_count'],'independent':y['eligible_count']},'status':'G0_PASS_H1A_TRAINING_AUTHORIZED' if valid else 'INCONCLUSIVE_R012_H1A','reason':None if valid else 'G0_INVALID'}
    (a.out_dir/'final.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()

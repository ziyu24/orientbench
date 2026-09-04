"""One CPU-only r010 execution: lineage, primary audit, independent recheck."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

def invoke(script, *args):
    subprocess.run([sys.executable, script, *map(str, args)], check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--third-party',type=Path,required=True);p.add_argument('--pth-index',type=Path,required=True);p.add_argument('--pth-root',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args()
    here=Path(__file__).parent; a.out_dir.mkdir(parents=True,exist_ok=True)
    invoke(here/'image_lineage.py','--root',a.root,'--out',a.root/'image_archive_index.json')
    invoke(here/'model_inventory.py','--third-party',a.third_party,'--pth',a.pth_root,'--out',a.root/'model_assets.json')
    invoke(here/'audit.py','--root',a.root,'--third-party',a.third_party,'--pth-index',a.pth_index,'--out',a.out_dir/'materialization.json')
    invoke(here/'verify.py','--root',a.root,'--out',a.out_dir/'independent_verify.json')
    primary=json.loads((a.out_dir/'materialization.json').read_text()); independent=json.loads((a.out_dir/'independent_verify.json').read_text())
    verdict=primary['token'] if primary['token']==independent['token'] else 'INCONCLUSIVE_R010_ASSET_MATERIALIZATION'
    (a.out_dir/'final.json').write_text(json.dumps({'protocol':'r010-finalizer-v1','primary_token':primary['token'],'independent_token':independent['token'],'token':verdict,'agreement':primary['token']==independent['token'],'training_or_inference_run':False},indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()

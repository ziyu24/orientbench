"""Independent bounded signature recheck; no primary module/list import."""
from __future__ import annotations
import argparse,json,os
from pathlib import Path
NAMES=('rareplanes-public','rareplanes_public','rareplanes','rareplanes_real'); SIG=('rareplanes_public_all_annotations.geojson','rareplanes_public_all_metadata.json','rareplanes_public_all_metadata.geojson')
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset-root',type=Path,required=True);p.add_argument('--primary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();hits=[]
 for base,dirs,files in os.walk(a.dataset_root,followlinks=True):
  if len(Path(base).relative_to(a.dataset_root).parts)>5:dirs[:]=[];continue
  if Path(base).name.lower() in NAMES or any(x.lower() in SIG for x in files):hits.append(str(Path(base).resolve()))
 primary=json.loads(a.primary.read_text());same=sorted(hits)==sorted(x['path'] for x in primary['candidate_hits']);ok=same and primary['token']=='ASSET_UNAVAILABLE_R009';a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'protocol':'r009-independent-signature-audit-v1','candidate_paths':sorted(hits),'candidate_set_equal':same,'passed':ok,'token':'ASSET_UNAVAILABLE_R009' if ok else 'INCONCLUSIVE_R009_ASSET_AUDIT'},indent=2)+'\n')
if __name__=='__main__':main()

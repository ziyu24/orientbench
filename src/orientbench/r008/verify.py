"""Independent r008 absence/readiness census; no import of primary."""
from __future__ import annotations
import argparse,json
from pathlib import Path
NAMES=("RarePlanes","RarePlanes_real","RarePlanes_Public","rareplanes")
FAMILIES=("oriented_rcnn","rotated_rtmdet","ars_detr","o2_rtdetr","fred")
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset-root',type=Path,required=True);p.add_argument('--primary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();primary=json.loads(a.primary.read_text());found=any((a.dataset_root/x).is_dir() for x in NAMES);ok=(not found and primary['token']=='ASSET_UNAVAILABLE_R008' and len(primary['readiness'])==5 and [x['family'] for x in primary['readiness']]==list(FAMILIES) and all(primary['fixtures'].values()));a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'protocol':'r008-independent-asset-census-v1','rareplanes_present':found,'fixture_passed':all(primary['fixtures'].values()),'passed':ok,'token':'ASSET_UNAVAILABLE_R008' if ok else 'INCONCLUSIVE_R008_ASSET_AUDIT'},indent=2)+'\n')
if __name__=='__main__':main()

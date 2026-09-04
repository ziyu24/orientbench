"""Synthetic-only RarePlanes adapter schema fixture; deliberately no dataset read."""
from __future__ import annotations
import json
from pathlib import Path
def main(out):
 fixture={'image_id':'synthetic_000','image_shape':[64,96,3],'single_class_obb':[48.0,32.0,30.0,10.0,0.25],
          'attributes':{'wing':1,'engine_count':0,'propulsion':1},'rp1_angle_domain':'[0,pi)','no_real_input':True}
 valid=(len(fixture['single_class_obb'])==5 and set(fixture['attributes'])=={'wing','engine_count','propulsion'} and fixture['rp1_angle_domain']=='[0,pi)')
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'protocol':'r011-synthetic-schema-v1','fixture_valid':valid,'fixture':fixture},indent=2,sort_keys=True)+'\n')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.out)

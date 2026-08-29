#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
import yaml
p=argparse.ArgumentParser();p.add_argument('--result');p.add_argument('--rows');p.add_argument('--geometry');p.add_argument('--manifest');a=p.parse_args()
r=yaml.safe_load(Path(a.result).read_text()); rows=json.loads(Path(a.rows).read_text()); geo=json.loads(Path(a.geometry).read_text()); m=yaml.safe_load(Path(a.manifest).read_text())
assert len(rows)==1024==r['count'] and len({x['proposal_uid'] for x in rows})==1024
assert all(x['proposal_uid']!=x['foreign_q_source_uid'] for x in rows)
assert len(geo)==1024 and m['can_recompute'] is True
for name,digest in m['artifacts'].items(): assert hashlib.sha256(Path(a.manifest).parent.joinpath(name).read_bytes()).hexdigest()==digest
assert r['conclusion'] in {'PASS_G1_CORRECTION','KILL_CMR_IMPLEMENTATION_PRINCIPLE','INCONCLUSIVE_GEOMETRY_HARNESS'}
print(json.dumps({'accepted':True,'conclusion':r['conclusion'],'count':len(rows)}))

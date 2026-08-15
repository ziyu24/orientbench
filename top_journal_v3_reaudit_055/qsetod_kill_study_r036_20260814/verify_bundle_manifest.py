#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib
from pathlib import Path
import pandas as pd

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''): h.update(block)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);a=p.parse_args();m=pd.read_csv(a.bundle/'bundle_manifest.csv'); actual={str(x.relative_to(a.bundle)) for x in a.bundle.rglob('*') if x.is_file() and x.name!='bundle_manifest.csv'}
 if actual!=set(m.path): raise SystemExit('bundle file set mismatch')
 for row in m.itertuples(index=False):
  path=a.bundle/row.path
  if path.stat().st_size!=row.bytes or sha(path)!=row.sha256: raise SystemExit('bundle hash mismatch '+row.path)
 print(f'PASS_BUNDLE files={len(m)} bytes={int(m.bytes.sum())}')
if __name__=='__main__':main()

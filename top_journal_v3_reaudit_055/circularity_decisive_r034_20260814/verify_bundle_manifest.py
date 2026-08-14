#!/usr/bin/env python3
"""Verify every r034 bundle object against its manifest."""
import argparse, hashlib
from pathlib import Path
import pandas as pd

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);a=p.parse_args();m=pd.read_csv(a.bundle/'bundle_manifest.csv');listed=set(m.path);actual={x.relative_to(a.bundle).as_posix() for x in a.bundle.rglob('*') if x.is_file() and x.name!='bundle_manifest.csv'}
    if listed!=actual:raise SystemExit(f'path set mismatch missing={sorted(actual-listed)} extra={sorted(listed-actual)}')
    for r in m.itertuples(index=False):
        x=a.bundle/r.path
        if x.stat().st_size!=int(r.bytes) or sha(x)!=r.sha256:raise SystemExit('hash mismatch '+r.path)
        if x.stat().st_size>80*1024*1024:raise SystemExit('unsplit file exceeds 80 MiB '+r.path)
    print(f'PASS_BUNDLE files={len(m)} bytes={m.bytes.sum()}')
if __name__=='__main__':main()

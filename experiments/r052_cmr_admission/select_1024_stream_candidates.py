#!/usr/bin/env python3
"""Freeze the first 1,024 deterministic rows emitted during live pre-NMS export."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--shard-dir', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    rows = []
    files = sorted(a.shard_dir.glob('rank[0-9].pkl'))
    for f in files:
        rows.extend(pickle.load(f.open('rb')))
    rows.sort(key=lambda x: (hashlib.sha256(x['image_id'].encode()).hexdigest(), x['image_id'], x['proposal_index']))
    chosen = rows[:1024]
    if len(chosen) != 1024:
        raise RuntimeError(f'NOT_ADJUDICATED_ASSET_ENV: found {len(chosen)} live pre-NMS positives, need 1024')
    if len({x['proposal_uid'] for x in chosen}) != 1024:
        raise RuntimeError('live pre-NMS proposal UID universe is not unique')
    payload = dict(schema_version=3, dataset='DOTA-v1.0 train only', count=1024,
                   source='live detector-native decoded proposals before final ROI NMS',
                   selection='SHA256(image_id), image_id tie-break; proposal index ascending; max four/image; class match and rotated IoU >= 0.5',
                   source_shards=[str(x) for x in files], proposals=chosen)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(payload, indent=2) + '\n')
    digest = hashlib.sha256(a.out.read_bytes()).hexdigest()
    a.out.with_suffix('.sha256').write_text(digest + '  ' + a.out.name + '\n')
    print(json.dumps({'count': len(chosen), 'sha256': digest}))


if __name__ == '__main__':
    main()

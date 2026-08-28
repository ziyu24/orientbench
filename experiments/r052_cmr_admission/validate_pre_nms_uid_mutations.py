#!/usr/bin/env python3
"""Dynamic provenance validator and destructive mutations for the r052 G1 manifest."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def validate(payload: dict) -> None:
    rows = payload['proposals']
    if len(rows) != 1024 or len({x['proposal_uid'] for x in rows}) != 1024:
        raise ValueError('proposal UID universe is not exact and unique')
    for row in rows:
        if row['class_uid'] != f"{row['proposal_uid']}:{row['class_id']}":
            raise ValueError('class UID does not derive from proposal/class')
        expected = [f"{row['class_uid']}:{k}" for k in range(12)]
        if row['candidate_uids'] != expected:
            raise ValueError('candidate UID sequence does not derive from class UID')
        if (not isinstance(row['final_nms_keep_indices'], list) or
                any(not isinstance(v, int) or v < 0 for v in row['final_nms_keep_indices'])):
            raise ValueError('NMS lineage was not exported')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    payload = json.loads(args.manifest.read_text())
    validate(payload)
    mutations = {}
    cases = {
        'delete_proposal': lambda x: x['proposals'].pop(),
        'swap_class_uid': lambda x: x['proposals'][0].__setitem__('class_uid', x['proposals'][1]['class_uid']),
        'repeat_candidate_uid': lambda x: x['proposals'][0]['candidate_uids'].__setitem__(1, x['proposals'][0]['candidate_uids'][0]),
        'tamper_nms_mapping': lambda x: x['proposals'][0].__setitem__('final_nms_keep_indices', 'tampered'),
    }
    for name, mutate in cases.items():
        bad = copy.deepcopy(payload)
        mutate(bad)
        try:
            validate(bad)
        except ValueError as exc:
            mutations[name] = {'rejected': True, 'reason': str(exc)}
        else:
            mutations[name] = {'rejected': False, 'reason': 'validator accepted mutation'}
    if not all(x['rejected'] for x in mutations.values()):
        raise RuntimeError('a destructive UID/NMS mutation was not rejected')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({'schema_version': 1, 'passed': True,
                                    'mutations': mutations}, indent=2) + '\n')


if __name__ == '__main__':
    main()

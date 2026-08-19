#!/usr/bin/env python3
"""Hash the corrected-r048 evidence without reading T_cal or T_audit."""
import hashlib, json
from pathlib import Path

ROOT = Path('outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819')
OUT = ROOT / 'sheetfixed_manifest.json'
paths = []
for base in (ROOT / 'formal_sheetfixed', ROOT / 'g1_val_sheetfixed'):
    for p in sorted(base.rglob('*')):
        if p.is_file() and p.suffix in {'.json', '.jsonl', '.log', '.pt'}:
            h = hashlib.sha256()
            with p.open('rb') as f:
                for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
            paths.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': h.hexdigest(),
                          'can_recompute': False, 'checkpoint': p.suffix == '.pt'})
OUT.write_text(json.dumps({'schema_version': 2, 'dispatch_id': 'orientbench-b-r048-p2c-lift-directed-obb-stagea-20260819',
                           'information_wall': {'t_cal_read': False, 't_audit_semantic_opened': False},
                           'items': paths}, indent=2))
print(OUT, len(paths))

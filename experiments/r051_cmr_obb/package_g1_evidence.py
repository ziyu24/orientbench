#!/usr/bin/env python3
"""Freeze a reproducible file-level inventory for the completed r051 G1 arms."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ARMS = {
    'CMR': 'dota_orcnn_cmr_frozenhost_3ep',
    'DIRECT_DIST': 'dota_orcnn_direct_dist_frozenhost_3ep',
    'SINGLE_ROI_QUALITY': 'dota_orcnn_single_roi_quality_frozenhost_3ep',
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def entry(root: Path, path: Path) -> dict:
    return {
        'path': str(path.relative_to(root)),
        'bytes': path.stat().st_size,
        'sha256': sha256(path),
        'can_recompute': True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    args = parser.parse_args()
    base = args.base.resolve()
    required_common = ('train.log', 'epoch_3.pth')
    inventory: dict[str, list[dict]] = {}
    for arm, dirname in ARMS.items():
        arm_dir = base / dirname
        missing = [name for name in required_common if not (arm_dir / name).is_file()]
        if missing:
            raise RuntimeError(f'{arm}: missing required completed-arm evidence: {missing}')
        paths = [arm_dir / name for name in required_common]
        paths.extend(sorted(arm_dir.glob('best_*.pth')))
        paths.extend(sorted(arm_dir.glob('epoch_*.pth')))
        config = next(iter(sorted(arm_dir.glob('*.py'))), None)
        if config is None:
            raise RuntimeError(f'{arm}: missing copied config')
        paths.append(config)
        evaluation = arm_dir / 'evaluation'
        if not evaluation.is_dir():
            raise RuntimeError(f'{arm}: missing evaluation export directory')
        paths.extend(sorted(p for p in evaluation.rglob('*') if p.is_file()))
        # Paths may overlap when epoch_3 is also the saved best checkpoint.
        inventory[arm] = [entry(base, p) for p in dict.fromkeys(paths)]
    metrics = base / 'metrics'
    required_metrics = ('matched_tp_rows.jsonl', 'risk_metrics.csv', 'manifest.json', 'g1_gate.json')
    missing_metrics = [name for name in required_metrics if not (metrics / name).is_file()]
    if missing_metrics:
        raise RuntimeError(f'missing adjudication evidence: {missing_metrics}')
    result = {
        'schema_version': 1,
        'dispatch_id': 'orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822',
        'dataset_protocol': 'DOTA-v1.0 train->val only',
        'g1_arms': inventory,
        'adjudication': [entry(base, metrics / name) for name in required_metrics],
        'prohibited_endpoints_touched': False,
        'can_recompute': True,
    }
    out = base / 'metrics' / 'g1_evidence_inventory.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()

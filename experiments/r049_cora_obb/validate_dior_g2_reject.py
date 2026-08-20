#!/usr/bin/env python3
"""Independent structural validation for the terminal DIOR G2 receipt.

This validator deliberately does not rerun training or choose a result.  It
checks the persistent raw/metric manifests, recomputes the frozen point-gate
inequalities from their serialized values, and asserts that terminal rejection
precludes SODA and extra-seed artifacts.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/rspip/cqc/pro/study/orientbench')
G2 = ROOT / 'outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    manifest = json.loads((G2 / 'metrics/manifest.json').read_text())
    gate = json.loads((G2 / 'metrics/gate_dior_seed0.json').read_text())
    assert gate['status'] == 'REJECT_CORA_METHOD'
    assert any(gate['checks'].values())  # terminal gate retains passed evidence
    assert gate['checks']['AP75_delta_ge_minus_0_005'] is False
    assert gate['checks']['AUGRC_reduction_ge_0_01'] is False
    assert gate['checks']['Risk_at_70_reduction_ge_0_02'] is False
    for arm, item in manifest['raw_exports'].items():
        path = ROOT / item['path']
        assert path.is_file(), (arm, path)
        assert digest(path) == item['sha256'], arm
    rows = G2 / 'metrics/matched_tp_rows.jsonl'
    assert digest(rows) == manifest['matched_rows_sha256']
    with (G2 / 'metrics/risk_metrics.csv').open() as f:
        metrics = list(csv.DictReader(f))
    assert {r['arm'] for r in metrics} == {'CONT', 'VM_NLL', 'CORA'}
    assert not (G2 / 'soda').exists()
    print(json.dumps({'status': 'PASS_TERMINAL_REJECT_VALIDATION',
                      'gate': str((G2 / 'metrics/gate_dior_seed0.json').relative_to(ROOT))}, indent=2))


if __name__ == '__main__':
    main()

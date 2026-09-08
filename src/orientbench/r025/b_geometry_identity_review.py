"""Read-only r026 review of native geometry type and archived mapping existence."""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(root, data):
    art = root / 'runs/r026/artifacts'
    names = sorted(p.name for p in (data/'dota1.0/val/annfiles').glob('*.txt'))
    geometry = {}
    for version in ('1.0', '2.0'):
        total, per_image, examples = Counter(), [], []
        for name in names:
            path = data / f'dota{version}/val/annfiles' / name
            counts = Counter()
            for number, line in enumerate(path.read_text().splitlines(), 1):
                fields = line.split()
                if len(fields) != 10:
                    continue
                try:
                    points = [(float(fields[i]), float(fields[i+1])) for i in range(0, 8, 2)]
                except ValueError:
                    continue
                axis = all(abs(points[i][0]-points[(i+1)%4][0]) < 1e-6 or
                           abs(points[i][1]-points[(i+1)%4][1]) < 1e-6 for i in range(4))
                counts['objects'] += 1
                counts['axis_aligned'] += axis
                if fields[8] in ('plane', 'ship'):
                    counts['focus_objects'] += 1
                    counts['focus_axis_aligned'] += axis
                    if len(examples) < 2:
                        examples.append({'image': name, 'line': number, 'raw': line})
            total.update(counts)
            per_image.append({'image': name, 'sha256': digest(path), **counts})
        geometry[version] = {'totals': dict(total), 'per_image': per_image, 'examples': examples}
    mapping = root/'archives/worktrees/orientbench_r032_clean/audit_bundles/r028/dota/tile_to_mother.csv'
    with mapping.open(newline='') as f:
        rows = list(csv.DictReader(f))
    native = json.loads((art/'independent_verify.json').read_text())
    files = {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in art.iterdir() if p.is_file()}
    return {'utc': datetime.now(timezone.utc).isoformat(), 'root': str(root),
            'geometry': geometry, 'artifact_identity': files,
            'label_summary': json.loads((art/'label_summary.json').read_text()),
            'native_replay': native['native_replay'],
            'mapping': {'path': str(mapping), 'sha256': digest(mapping), 'rows': len(rows),
                        'unique_tiles': len({r['stem'] for r in rows}),
                        'unique_mothers': len({r['mother'] for r in rows}),
                        'examples': rows[:2], 'full_prediction_binding_verified': False},
            'local_dataset_readme': {'path': str(data/'dota2.0/README.md'),
                                    'sha256': digest(data/'dota2.0/README.md'),
                                    'text': (data/'dota2.0/README.md').read_text()},
            'source_audit': json.loads((art/'prediction_sources_corrected.json').read_text()),
            'source_verifier': json.loads((art/'prediction_provenance_verify.json').read_text()),
            'limitations': ['Axis-aligned geometry does not by itself prove which archive was extracted.',
                            'Native correspondence replay is inherited from the saved verifier and compared with the earlier B replay.',
                            'Images were not re-decoded; no models, AP or hidden test were accessed.']}


if __name__ == '__main__':
    print(json.dumps(review(Path('/home/rspip/cqc/study/orientbench'),
                            Path('/home/rspip/cqc/data/dataset/dota')), ensure_ascii=False, indent=2))

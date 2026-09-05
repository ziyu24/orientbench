"""Frozen r015 calibration inference; writes every paired view probability."""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
import torch.multiprocessing as mp

sys.path.insert(0, str(Path(__file__).parents[2]))
from orientbench.r015.data import Windows, collate, render
from orientbench.r015.model import Heads


def records(preflight: Path, windows: Path):
    p = json.loads(preflight.read_text())
    m = json.loads((windows / 'manifest.json').read_text())['objects']
    result = []
    for row in p['records']['calibration']:
        q = dict(row)
        q['window'] = m[str(q['object_id'])]['window']
        result.append(q)
    if len(result) != 7416:
        raise RuntimeError('calibration universe')
    return result


def probs(model, x, rows, strategy, size, delta=0.0, eight=False):
    with torch.no_grad():
        if eight:
            view = [torch.softmax(model(render(x, rows, strategy, size, 15015, 0, False,
                                               eval_phi='fixed', view_offset=j * np.pi / 4)), -1)
                    for j in range(8)]
            return torch.stack(view, 1)
        left = torch.softmax(model(render(x, rows, strategy, size, 15015, 0, False,
                                          eval_phi='fixed' if strategy == 'I' else delta)), -1)
        right = torch.softmax(model(render(x, rows, strategy, size, 15015, 0, True,
                                           eval_phi='fixed' if strategy == 'I' else delta)), -1)
        return torch.stack((left, right), 1)


def fit(fit_dir: Path, device: int, rows, root: Path, out: Path):
    meta = json.loads((fit_dir / 'train.json').read_text())
    fields = meta['tag'].split('_')
    strategy = fields[0]
    if fields[1:3] == ['vit', 'b16']:
        kind, size, seed = 'vit_b16', int(fields[3]), fields[4]
    else:
        kind, size, seed = fields[1], int(fields[2]), fields[3]
    target = out / meta['tag']
    if target.exists():
        raise RuntimeError(('duplicate evaluation', str(target)))
    target.mkdir(parents=True)
    torch.cuda.set_device(device)
    model = Heads(kind, size).to(device)
    checkpoint = torch.load(fit_dir / 'epoch40.pt', map_location='cpu', weights_only=False)
    model.load_state_dict(checkpoint['state_dict'], strict=True)
    model.eval()
    loader = DataLoader(Windows(rows, root), batch_size=24, shuffle=False, num_workers=2,
                        pin_memory=True, collate_fn=collate)
    conditions = ['I2', 'I8'] if strategy == 'I' else ([f'O{d:g}' for d in (0, -5, 5, -10, 10, -20, 20)] if strategy == 'O' else ['T0'])
    output = {name: [] for name in conditions}
    for x, batch in loader:
        x = x.to(device, non_blocking=True)
        for name in conditions:
            if name == 'I2': value = probs(model, x, batch, strategy, size)
            elif name == 'I8': value = probs(model, x, batch, strategy, size, eight=True)
            else: value = probs(model, x, batch, strategy, size, float(name[1:]) * np.pi / 180)
            output[name].append(value.cpu().numpy().astype(np.float32))
    arrays = {name: np.concatenate(value, 0) for name, value in output.items()}
    np.savez_compressed(target / 'probabilities.npz', object_id=np.array([r['object_id'] for r in rows]),
                        component=np.array([r['component'] for r in rows]), labels=np.array([r['labels'] for r in rows]), **arrays)
    (target / 'manifest.json').write_text(json.dumps({'protocol': 'r015-matched-support-v1', 'fit': meta,
        'conditions': conditions, 'objects': len(rows), 'test_opened': False}, indent=2, sort_keys=True) + '\n')


def worker(rank, dirs, rows, root, out):
    for directory in dirs[rank::4]:
        fit(directory, rank, rows, root, out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', type=Path, required=True)
    parser.add_argument('--windows', type=Path, required=True)
    parser.add_argument('--fits', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    dirs = sorted(args.fits.glob('*/train.json'))
    dirs = [x.parent for x in dirs]
    if len(dirs) != 36 or torch.cuda.device_count() != 4:
        raise RuntimeError(('frozen fit matrix or gpu count', len(dirs), torch.cuda.device_count()))
    if args.out.exists():
        raise RuntimeError('evaluation output exists')
    args.out.mkdir(parents=True)
    mp.spawn(worker, args=(dirs, records(args.preflight, args.windows), args.windows, args.out), nprocs=4, join=True)
    if len(list(args.out.glob('*/probabilities.npz'))) != 36:
        raise RuntimeError('incomplete evaluation')
    (args.out / 'manifest.json').write_text(json.dumps({'protocol': 'r015-matched-support-v1', 'fits': 36,
        'calibration_opened': True, 'test_opened': False}, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()

"""Compare the archived production r014 renderer to an independent CPU reference."""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).parents[2]))
from orientbench.r014.evaluate_corrected import render as production_render


def reference(row: dict[str, object], delta: float, flip: bool, canvas: np.ndarray) -> torch.Tensor:
    """Deliberately independent coordinate and sampling construction."""
    side = int(row['side']); theta = float(row['theta']) + delta + (math.pi if flip else 0.)
    uv = torch.arange(224, dtype=torch.float32) * (2.0 / 224) + (-1.0 + 1.0 / 224)
    v, u = torch.meshgrid(uv, uv, indexing='ij')
    long, short = .6 * float(row['L']), .6 * float(row['S'])
    c, s = math.cos(theta), math.sin(theta)
    center_x = float(row['center'][0]) - int(float(row['center'][0]) - side / 2)
    center_y = float(row['center'][1]) - int(float(row['center'][1]) - side / 2)
    grid = torch.stack((2 * (c * long * u - s * short * v + center_x + .5) / side - 1,
                        2 * (s * long * u + c * short * v + center_y + .5) / side - 1), -1)
    image = torch.from_numpy(canvas.transpose(2, 0, 1)).float()[None] / 255.
    return F.grid_sample(image, grid[None], mode='bilinear', padding_mode='zeros', align_corners=False)


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument('--audit', type=Path, required=True); p.add_argument('--g0', type=Path, required=True); p.add_argument('--out', type=Path, required=True); a = p.parse_args()
    if a.out.exists(): raise RuntimeError('render acceptance output exists')
    eligible = {x['object_id']: x for x in json.load(open(a.g0.parent / 'eligible_manifest.json'))}
    records = [json.loads(x) for x in open(a.audit / 'source_records.jsonl') if '"partition": "calibration"' in x]
    # One object for every source image, which necessarily includes all 20 affected loc-CAT keys.
    selected = []; seen = set()
    for record in records:
        if record['image_id'] not in seen:
            seen.add(record['image_id']); selected.append(record)
    results = []
    for record in selected:
        e = eligible[record['object_id']]
        row = {'canvas': str(a.audit / 'corrected_calibration_canvases' / f"{record['object_id']}.npy"), 'side': e['canvas_side'], 'center': e['center'], 'L': e['L'], 'S': e['S'], 'theta': e['theta']}
        canvas = np.load(row['canvas'], allow_pickle=False)
        actual = [production_render([row], d, flip, device='cpu') for d, flip in ((0., False), (0., True), (math.pi / 18, False), (math.pi / 18, True))]
        independent = [reference(row, d, flip, canvas) for d, flip in ((0., False), (0., True), (math.pi / 18, False), (math.pi / 18, True))]
        # θ+π must exchange the two actual views; a structured patch must respond to +10°.
        shifted = dict(row); shifted['theta'] += math.pi
        exchanged = [production_render([shifted], 0., flip, device='cpu') for flip in (False, True)]
        results.append({'object_id': record['object_id'], 'image_id': record['image_id'], 'affected': record['affected'],
            'reference_max_abs': max(float((x-y).abs().max()) for x,y in zip(actual, independent)),
            'theta180_exchange_max_abs': max(float((actual[0]-exchanged[1]).abs().max()), float((actual[1]-exchanged[0]).abs().max())),
            'plus10_pixel_response': float((actual[0]-actual[2]).abs().max())})
    # The analytic directional fixture rules out a vacuous coordinate-only response check.
    synthetic = np.zeros((256, 256, 3), np.uint8); synthetic[112:144, 24:232, 0] = 255
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fixture_path = a.out.parent / 'synthetic_directional_fixture.npy'
    np.save(fixture_path, synthetic, allow_pickle=False)
    fixture = {'canvas': str(fixture_path), 'side': 256, 'center': [128.,128.], 'L': 180., 'S': 28., 'theta': 0.}
    response = float((production_render([fixture], 0., False, device='cpu') - production_render([fixture], math.pi/18, False, device='cpu')).abs().max())
    summary = {'protocol': 'r014-render-acceptance-v1', 'test_opened': False, 'model_forward': False,
        'selected_sources': len(selected), 'affected_sources': sum(x['affected'] for x in selected),
        'max_reference_abs': max(x['reference_max_abs'] for x in results), 'max_theta180_exchange_abs': max(x['theta180_exchange_max_abs'] for x in results),
        'min_plus10_pixel_response': min(x['plus10_pixel_response'] for x in results), 'synthetic_plus10_pixel_response': response,
        'pass': max(x['reference_max_abs'] for x in results) == 0. and max(x['theta180_exchange_max_abs'] for x in results) < 2e-6 and response > 0.}
    a.out.write_text(json.dumps({'summary': summary, 'records': results}, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__': main()

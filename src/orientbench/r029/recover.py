"""Prepare exactly the original clean inference protocol after cache deletion.

Model execution remains the standard MMRotate distributed test entry, two GPUs.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from mmengine.config import Config

from orientbench.r004.prepare_inference import MODELS
from orientbench.r029.run import check, digest, read_native


def validate_runtime(folder, dataset, cfg, model):
    folder, dataset = Path(folder).resolve(), Path(dataset).resolve()
    manifest = json.loads((folder / 'RUN.json').read_text())
    check(manifest.get('restoration_task') == 'r029', 'not an r029 restoration')
    for key, expected in cfg['model_sha256'][model].items():
        check(manifest[key] == expected, 'model provenance changed')
    base = Path(manifest['base_config'])
    check(digest(base) == cfg['model_sha256'][model]['base_config_sha256'], 'base config changed')
    check(digest(manifest['checkpoint']) == cfg['model_sha256'][model]['checkpoint_sha256'], 'checkpoint changed')
    expected = Config.fromfile(base)
    expected.test_dataloader.dataset.data_root = str(folder / 'adapter')
    expected.test_dataloader.dataset.ann_file = 'ImageSets/test.txt'
    expected.test_dataloader.dataset.data_prefix.sub_data_root = 'FullDataSet/'
    expected.test_dataloader.dataset.test_mode = True
    expected.work_dir = str(folder / 'work')
    expected.launcher = 'none'  # Standard test CLI overrides only launcher to pytorch.
    actual = Config.fromfile(folder / 'runtime_config.py')
    check(expected.to_dict() == actual.to_dict(), 'runtime changes beyond original clean adapter')
    check((folder / 'adapter/FullDataSet/AllImages').resolve() == (dataset / 'images').resolve(), 'adapter images changed')
    check((folder / 'adapter/FullDataSet/Annotations').resolve() == (dataset / 'annfiles').resolve(), 'adapter labels changed')
    check((folder / 'adapter/ImageSets').resolve() == (dataset / 'splits').resolve(), 'adapter split changed')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--dataset', type=Path, required=True)
    p.add_argument('--pth-root', type=Path, required=True)
    p.add_argument('--run-root', type=Path, required=True)
    args = p.parse_args()
    cfg = json.loads(args.config.read_text())
    args.dataset = args.dataset.resolve()
    args.pth_root = args.pth_root.resolve()
    args.run_root = args.run_root.resolve()
    _, _, _, audit = read_native(args.dataset, cfg)
    for model in cfg['models']:
        spec = MODELS[model]
        check(digest(args.pth_root / spec['config']) == cfg['model_sha256'][model]['base_config_sha256'], 'wrong base config')
        check(digest(args.pth_root / spec['checkpoint']) == cfg['model_sha256'][model]['checkpoint_sha256'], 'wrong checkpoint')
        folder = args.run_root / 'inference/test' / model / 'clean'
        if (folder / 'predictions.pkl').exists():
            validate_runtime(folder, args.dataset, cfg, model)
            continue
        subprocess.run([sys.executable, '-m', 'orientbench.r004.prepare_inference',
                        '--run-root', str(args.run_root), '--dataset-root', str(args.dataset),
                        '--pth-root', str(args.pth_root), '--model', model, '--split', 'test'], check=True)
        manifest = json.loads((folder / 'RUN.json').read_text())
        manifest.update(restoration_task='r029', base_config=str(args.pth_root / spec['config']))
        (folder / 'RUN.json').write_text(json.dumps(manifest, indent=2))
        validate_runtime(folder, args.dataset, cfg, model)
    (args.run_root / 'native_input_audit.json').write_text(json.dumps(audit, indent=2))
    print('r029 clean configs prepared; run each model with the standard 2-GPU test entry.')


if __name__ == '__main__':
    main()

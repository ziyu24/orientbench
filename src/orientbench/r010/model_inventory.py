"""Record immutable provenance for existing, legal r010 model assets only."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path

def sha(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def revision(path: Path):
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()

def record(identifier, path, license_file, init, source, gap=None):
    path, license_file = Path(path), Path(license_file)
    exists = path.is_dir() and license_file.is_file() and (not init or Path(init).is_file())
    return {'id': identifier, 'source': source, 'local_path': str(path), 'revision': revision(path) if path.is_dir() else None,
            'license': sha(license_file) if license_file.is_file() else None,
            'initialization': str(init) if init else None, 'sha256': sha(Path(init)) if init and Path(init).is_file() else None,
            'exists': exists, 'minimal_adaptation_gap': gap}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--third-party', type=Path, required=True); p.add_argument('--pth', type=Path, required=True); p.add_argument('--out', type=Path, required=True); a=p.parse_args()
    init=a.pth/'rareplanes_initialization/resnet50-11ad3fa6.pth'; vit=a.pth/'rareplanes_initialization/vit_b_16-c867db91.pth'; t=a.third_party
    assets=[
      record('oriented_rcnn',t/'mmrotate_1x',t/'mmrotate_1x/LICENSE',init,'https://github.com/open-mmlab/mmrotate'),
      record('rotated_rtmdet',t/'mmrotate_1x',t/'mmrotate_1x/LICENSE',init,'https://github.com/open-mmlab/mmrotate'),
      record('ars_detr',t/'ARS-DETR',t/'ARS-DETR/LICENSE',init,'https://github.com/httle/ARS-DETR'),
      record('o2_rtdetr',t/'ai4rs',t/'ai4rs/LICENSE',init,'https://github.com/wokaikaixinxin/ai4rs', 'R50vd initialization compatibility must be configured before training'),
      {'id':'fred','source':'AAAI-24 paper / official author and repository search','local_path':None,'revision':None,'license':None,'initialization':None,'sha256':None,'exists':False,'minimal_adaptation_gap':'official implementation and legal initialization were not published/found; no surrogate used'},
      record('resnet50',t/'mmdetection',t/'mmdetection/LICENSE',init,'https://github.com/pytorch/vision', 'classifier head remains untrained by design'),
      record('vit_b16',t/'openai-clip',t/'openai-clip/LICENSE',vit,'https://github.com/pytorch/vision', 'classifier head remains untrained by design')]
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps({'protocol':'r010-model-inventory-v1','assets':assets},indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()

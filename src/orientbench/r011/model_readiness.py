"""Actual CPU config-build/state-dict-load probes; never run a forward pass."""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT=Path('/home/rspip/cqc/study')
PCP=Path('/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python')
MR=Path('/home/rspip/cqc/data/install/yes/envs/mr/bin/python')

SPECS={
 'oriented_rcnn': {'python':PCP,'config':ROOT/'pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py','weight':ROOT/'pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth'},
 'rotated_rtmdet': {'python':PCP,'config':ROOT/'pth_data/baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/config.py','weight':ROOT/'pth_data/baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/best_mAP_7161_epoch_31.pth'},
 'ars_detr': {'python':MR,'config':ROOT/'pth_data/baseline_arsdetr_r50_fpn_36e_le90/DOTA10_train_val/config.py','weight':ROOT/'pth_data/baseline_arsdetr_r50_fpn_36e_le90/DOTA10_train_val/best_mAP_6745_epoch_36.pth'},
 'o2_rtdetr': {'python':PCP,'config':ROOT/'third_party/ai4rs/projects/rotated_rtdetr/configs/o2_rtdetr_r50vd_2xb4_72e_dota.py','weight':None},
 'resnet50': {'python':PCP,'weight':ROOT/'pth_data/rareplanes_initialization/resnet50-11ad3fa6.pth'},
 'vit_b16': {'python':PCP,'weight':ROOT/'pth_data/rareplanes_initialization/vit_b_16-c867db91.pth'},
}

def probe(name):
    try:
        if name in {'oriented_rcnn','rotated_rtmdet'}:
            from mmrotate.utils import register_all_modules; register_all_modules(init_default_scope=True)
            from mmengine.config import Config
            from mmrotate.registry import MODELS
            from mmengine.runner.checkpoint import load_checkpoint
            spec=SPECS[name]; model=MODELS.build(Config.fromfile(str(spec['config'])).model)
            load_checkpoint(model,str(spec['weight']),map_location='cpu',strict=False)
            return {'id':name,'build':True,'load':True,'missing_keys':[],'unexpected_keys':[]}
        if name == 'ars_detr':
            # This is intentionally the recorded ARS runtime, not a substitute API.
            from mmcv import Config
            from mmrotate.models import build_detector
            spec=SPECS[name]; cfg=Config.fromfile(str(spec['config'])); model=build_detector(cfg.model,train_cfg=cfg.get('train_cfg'),test_cfg=cfg.get('test_cfg'))
            return {'id':name,'build':True,'load':False,'missing_keys':None,'unexpected_keys':None}
        if name == 'o2_rtdetr':
            from mmrotate.utils import register_all_modules; register_all_modules(init_default_scope=True)
            from mmengine.config import Config
            from mmrotate.registry import MODELS
            spec=SPECS[name]; model=MODELS.build(Config.fromfile(str(spec['config'])).model)
            return {'id':name,'build':True,'load':False,'missing_keys':None,'unexpected_keys':None}
        import torch
        from torchvision import models
        model=models.resnet50(weights=None) if name == 'resnet50' else models.vit_b_16(weights=None)
        result=model.load_state_dict(torch.load(SPECS[name]['weight'],map_location='cpu',weights_only=True),strict=False)
        return {'id':name,'build':True,'load':True,'missing_keys':list(result.missing_keys),'unexpected_keys':list(result.unexpected_keys)}
    except Exception as exc:
        return {'id':name,'build':False,'load':False,'error_type':type(exc).__name__,'error':str(exc)[:500]}

def parent(out):
    records=[]
    for name,spec in SPECS.items():
        env=os.environ.copy()
        if name == 'ars_detr': env['PYTHONPATH']=str(ROOT/'third_party/ARS-DETR')
        if name == 'o2_rtdetr': env['PYTHONPATH']=str(ROOT/'third_party/ai4rs')
        run=subprocess.run([str(spec['python']),str(Path(__file__).resolve()),'--probe',name],text=True,capture_output=True,env=env,timeout=180)
        try: rec=json.loads(run.stdout.strip().splitlines()[-1])
        except Exception: rec={'id':name,'build':False,'load':False,'error_type':'ProbeProtocolError','error':(run.stderr or run.stdout)[-500:]}
        rec['returncode']=run.returncode; records.append(rec)
    records.append({'id':'fred','build':False,'load':False,'error_type':'OfficialImplementationUnavailable','error':'No official/author implementation plus legal initialization is locally materialised; no surrogate accepted.','returncode':None})
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'protocol':'r011-model-readiness-v1','records':records},indent=2,sort_keys=True)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--probe');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.probe: print(json.dumps(probe(a.probe),sort_keys=True)); return
    if not a.out: raise SystemExit('--out is required')
    parent(a.out)
if __name__=='__main__': main()

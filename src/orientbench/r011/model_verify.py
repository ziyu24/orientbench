"""Independent build/load verification; does not import model_readiness."""
from __future__ import annotations
import json, os, subprocess
from pathlib import Path

STUDY=Path('/home/rspip/cqc/study'); PCP='/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python'; MR='/home/rspip/cqc/data/install/yes/envs/mr/bin/python'
PAYLOAD=r'''import json,sys,torch
name=sys.argv[1]
try:
 if name in ('oriented_rcnn','rotated_rtmdet'):
  from mmrotate.utils import register_all_modules;register_all_modules(init_default_scope=True)
  from mmengine.config import Config
  from mmrotate.registry import MODELS
  from mmengine.runner.checkpoint import load_checkpoint
  base='/home/rspip/cqc/study/pth_data/'
  path=(base+'baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/' if name=='oriented_rcnn' else base+'baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/')
  cfg=Config.fromfile(path+'config.py'); m=MODELS.build(cfg.model); ck='best_mAP_7061_epoch_11.pth' if name=='oriented_rcnn' else 'best_mAP_7161_epoch_31.pth';load_checkpoint(m,path+ck,map_location='cpu',strict=False); z={'id':name,'build':True,'load':True,'missing':[],'unexpected':[]}
 elif name=='ars_detr':
  from mmcv import Config
  from mmrotate.models import build_detector
  c=Config.fromfile('/home/rspip/cqc/study/pth_data/baseline_arsdetr_r50_fpn_36e_le90/DOTA10_train_val/config.py');build_detector(c.model,train_cfg=c.get('train_cfg'),test_cfg=c.get('test_cfg'));z={'id':name,'build':True,'load':False}
 elif name=='o2_rtdetr':
  from mmrotate.utils import register_all_modules;register_all_modules(init_default_scope=True)
  from mmengine.config import Config
  from mmrotate.registry import MODELS
  c=Config.fromfile('/home/rspip/cqc/study/third_party/ai4rs/projects/rotated_rtdetr/configs/o2_rtdetr_r50vd_2xb4_72e_dota.py');MODELS.build(c.model);z={'id':name,'build':True,'load':False}
 else:
  from torchvision import models
  m=models.resnet50(weights=None) if name=='resnet50' else models.vit_b_16(weights=None)
  fn='resnet50-11ad3fa6.pth' if name=='resnet50' else 'vit_b_16-c867db91.pth'; x=m.load_state_dict(torch.load('/home/rspip/cqc/study/pth_data/rareplanes_initialization/'+fn,map_location='cpu',weights_only=True),strict=False);z={'id':name,'build':True,'load':True,'missing':list(x.missing_keys),'unexpected':list(x.unexpected_keys)}
except Exception as e:z={'id':name,'build':False,'load':False,'error_type':type(e).__name__,'error':str(e)[:500]}
print(json.dumps(z,sort_keys=True))'''
def main():
 records=[]
 for name in ('oriented_rcnn','rotated_rtmdet','ars_detr','o2_rtdetr','resnet50','vit_b16'):
  env=os.environ.copy(); exe=MR if name=='ars_detr' else PCP
  if name=='ars_detr':env['PYTHONPATH']=str(STUDY/'third_party/ARS-DETR')
  if name=='o2_rtdetr':env['PYTHONPATH']=str(STUDY/'third_party/ai4rs')
  q=subprocess.run([exe,'-c',PAYLOAD,name],text=True,capture_output=True,env=env,timeout=180)
  try:r=json.loads(q.stdout.splitlines()[-1])
  except Exception:r={'id':name,'build':False,'load':False,'error_type':'IndependentProbeProtocol','error':(q.stderr+q.stdout)[-500:]}
  r['returncode']=q.returncode;records.append(r)
 records.append({'id':'fred','build':False,'load':False,'error_type':'OfficialImplementationUnavailable','error':'No local author implementation or matching legal initialization; no substitute was tested.','returncode':None})
 print(json.dumps({'protocol':'r011-independent-model-v1','records':records},indent=2,sort_keys=True))
if __name__=='__main__':main()

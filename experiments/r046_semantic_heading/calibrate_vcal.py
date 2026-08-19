import json,torch,sys
from pathlib import Path
sys.path.insert(0,'experiments/r046_semantic_heading');import smoke_ahc
from torch.utils.data import DataLoader
root=Path('outputs/persistent_artifacts/orientbench_semantic_heading_r046_20260818'); ids=set((root/'splits/V_cal.txt').read_text().split()); rows=[r for r in smoke_ahc.parse('val') if r[0] in ids]; dl=DataLoader(smoke_ahc.D(rows),batch_size=32,shuffle=False,num_workers=4);m=smoke_ahc.AHC();m.load_state_dict(torch.load(root/'smoke/ahc_formal.pt',map_location='cpu'));m.eval(); conf=[];err=[]
with torch.no_grad():
 for a,b,y in dl:
  z=m(a,b);conf.extend((2*torch.sigmoid(z)-1).abs().tolist());err.extend((z>0).eq(y.bool()).logical_not().int().tolist())
 conf=sorted(conf,reverse=True); out=[]
 for c in [.9,.8,.7]:
  k=max(1,int(len(conf)*c));thr=conf[k-1];keep=[i for i,v in enumerate(conf) if v>=thr];risk=sum(err[i] for i in keep)/len(keep);out.append({'coverage':c,'threshold':thr,'retained':len(keep),'risk':risk})
(root/'calibration').mkdir(exist_ok=True);(root/'calibration/V_cal.json').write_text(json.dumps({'rows':len(rows),'trials':out},indent=2)+'\n');print(json.dumps(out))

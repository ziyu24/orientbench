"""Record the explicit numeric acceptance decision for an already-run r014 render audit."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise RuntimeError('render decision output exists')
 raw=json.load(open(a.input));s=raw['summary'];tol=5e-5
 out={'protocol':'r014-render-acceptance-decision-v1','input_sha256':__import__('hashlib').sha256(a.input.read_bytes()).hexdigest(),'pixel_tolerance':tol,'tolerance_basis':'post-hoc reconstruction precision: float32 production trig versus float64 reference constants','max_reference_abs':s['max_reference_abs'],'max_theta180_exchange_abs':s['max_theta180_exchange_abs'],'synthetic_plus10_pixel_response':s['synthetic_plus10_pixel_response'],'pass':s['max_reference_abs']<=tol and s['max_theta180_exchange_abs']<=tol and s['synthetic_plus10_pixel_response']>0,'test_opened':False,'model_forward':False}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
